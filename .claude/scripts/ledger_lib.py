"""Aegis passive ledger core (capsule program PR-1a).

Standalone hook-side ledger writer/reader. This module MUST stay stdlib-only with no
aegis_foundation imports: the bootstrap fallback path (``python3 gate_lib.py <phase>``)
has to keep working without the runtime installed. The documented schema and query
recipes live in ``docs/aegis/LEDGER_SCHEMA.md``.

Decisions inherited from ``docs/aegis/AEGIS_CAPSULE_SPEC.md`` section 2 (do not
re-litigate here):

- Append-only SQLite at
  ``${XDG_STATE_HOME:-~/.local/state}/aegis/<sha1-of-git-common-dir>/ledger.db``,
  keyed on the git COMMON dir so all worktrees of one repository share one store.
- WAL mode + busy_timeout on every open.
- NO hash chain: append-only rows with timestamps.
- Capture-time redaction with an extensible pattern list.
- Fallback backend: per-session JSONL shards with the SAME event schema, append
  semantics, and reader merge behavior; the same test suite runs against both.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1"
LEDGER_FILENAME = "ledger.db"
SHARDS_DIRNAME = "shards"
ROTATE_BYTES = 64 * 1024 * 1024
BUSY_TIMEOUT_MS = 5000
SQLITE_BACKEND = "sqlite"
JSONL_BACKEND = "jsonl"
BACKENDS = (SQLITE_BACKEND, JSONL_BACKEND)
BACKEND_ENV_VAR = "AEGIS_LEDGER_BACKEND"

OUTCOME_CLASSES = ("pass", "fail", "interrupted", "unknown")
EXIT_CLASSES = OUTCOME_CLASSES

EVENT_FIELDS = (
    "schema_version",
    "event_id",
    "ts",
    "session_id",
    "branch",
    "cwd",
    "event_type",
    "tool_name",
    "handler",
    "paths",
    "outcome",
    "exit_class",
    "duration_ms",
    "agent_id",
    "agent_type",
    "payload_digest",
    "extra",
)

REDACTED = "[REDACTED]"

# (pattern, replacement) pairs applied in order at record time. Values are chosen to
# scrub the secret token while keeping enough surrounding text to stay debuggable.
DEFAULT_REDACT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)(wrangler\s+secret\s+put\s+\S+)\b[^\r\n]*", r"\1 " + REDACTED),
    (r"(?i)(authorization\s*[:=]\s*)[^\r\n]+", r"\1" + REDACTED),
    (r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/=]+", "Bearer " + REDACTED),
    (r"\bsk_[A-Za-z0-9_\-]{8,}\b", REDACTED),
    (r"\beyJ[A-Za-z0-9_\-]{10,}(?:\.[A-Za-z0-9_\-]+){1,2}", REDACTED),
)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    event_id TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    session_id TEXT,
    branch TEXT,
    cwd TEXT,
    event_type TEXT NOT NULL,
    tool_name TEXT,
    handler TEXT,
    paths TEXT NOT NULL DEFAULT '[]',
    outcome TEXT,
    exit_class TEXT,
    duration_ms INTEGER,
    agent_id TEXT,
    agent_type TEXT,
    payload_digest TEXT,
    extra TEXT NOT NULL DEFAULT '{}'
)
"""
_CREATE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)",
)


class LedgerError(Exception):
    """Raised for unrecoverable ledger setup problems (never for missing fields)."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_common_dir(cwd: str | Path | None = None) -> Path:
    """Resolve the git COMMON dir for ``cwd`` (worktrees share their parent repo's)."""

    base = Path(cwd) if cwd is not None else Path.cwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(base),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise LedgerError(f"not inside a git repository: {base} ({exc})") from exc
    if result.returncode != 0:
        raise LedgerError(f"not inside a git repository: {base}")
    raw = result.stdout.strip()
    common = Path(raw)
    if not common.is_absolute():
        common = (base / common).resolve()
    return common.resolve()


def _state_base(environment: Mapping[str, str]) -> Path:
    """Resolve the XDG state base without ever raising RuntimeError.

    Sandboxed hook environments (no HOME, no passwd entry for the uid) make
    ``Path.home()`` raise ``RuntimeError: Could not determine home directory`` —
    the HP-Coach 2026-06-12 incident. The ledger is an audit surface; its path
    resolution must degrade to a deterministic per-uid tmp store, not crash the
    gate that is trying to record a decision.
    """

    state_home = environment.get("XDG_STATE_HOME")
    if state_home:
        try:
            return Path(state_home).expanduser()
        except RuntimeError:
            return Path(state_home)
    home = environment.get("HOME")
    if home:
        return Path(home) / ".local" / "state"
    try:
        return Path.home() / ".local" / "state"
    except RuntimeError:
        uid = os.getuid() if hasattr(os, "getuid") else "unknown"
        return Path(tempfile.gettempdir()) / f"aegis-state-{uid}"


def store_dir(cwd: str | Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    """Per-repo out-of-worktree state directory (spec section 2 store decision)."""

    environment = env if env is not None else os.environ
    base = _state_base(environment)
    key = hashlib.sha1(git_common_dir(cwd).as_posix().encode("utf-8")).hexdigest()
    return base / "aegis" / key


def store_path(cwd: str | Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    return store_dir(cwd, env) / LEDGER_FILENAME


def shards_dir(cwd: str | Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    return store_dir(cwd, env) / SHARDS_DIRNAME


def compile_redact_patterns(
    extra_patterns: Iterable[str] = (),
) -> tuple[tuple[re.Pattern[str], str], ...]:
    compiled: list[tuple[re.Pattern[str], str]] = [
        (re.compile(pattern), replacement) for pattern, replacement in DEFAULT_REDACT_PATTERNS
    ]
    for pattern in extra_patterns:
        compiled.append((re.compile(pattern), REDACTED))
    return tuple(compiled)


def redact_text(text: str, extra_patterns: Iterable[str] = ()) -> str:
    """Scrub secret-shaped content from free text before it is recorded."""

    redacted = text
    for pattern, replacement in compile_redact_patterns(extra_patterns):
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _redact_value(value: Any, patterns: Iterable[str]) -> Any:
    if isinstance(value, str):
        return redact_text(value, patterns)
    if isinstance(value, Mapping):
        return {str(key): _redact_value(item, patterns) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_value(item, patterns) for item in value]
    return value


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_enum(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in OUTCOME_CLASSES else "unknown"


def normalize_event(
    event: Mapping[str, Any],
    *,
    redact_patterns: Iterable[str] = (),
) -> dict[str, Any]:
    """Fill, coerce, and redact an event into the v1 schema.

    Missing fields degrade to ``None`` (the recorder must never crash on a payload
    shape); unknown top-level keys are preserved under ``extra`` instead of being
    silently dropped.
    """

    raw = dict(event)
    paths_value = raw.get("paths")
    if paths_value is None:
        paths: list[str] = []
    elif isinstance(paths_value, (list, tuple)):
        paths = [str(item) for item in paths_value]
    else:
        paths = [str(paths_value)]

    extra_value = raw.get("extra")
    extra = dict(extra_value) if isinstance(extra_value, Mapping) else {}
    for key, value in raw.items():
        if key not in EVENT_FIELDS:
            extra[str(key)] = value

    duration: int | None
    try:
        duration = int(raw["duration_ms"]) if raw.get("duration_ms") is not None else None
    except (TypeError, ValueError):
        duration = None

    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": _coerce_optional_str(raw.get("event_id")) or uuid.uuid4().hex,
        "ts": _coerce_optional_str(raw.get("ts")) or utc_now_iso(),
        "session_id": _coerce_optional_str(raw.get("session_id")),
        "branch": _coerce_optional_str(raw.get("branch")),
        "cwd": _coerce_optional_str(raw.get("cwd")),
        "event_type": _coerce_optional_str(raw.get("event_type")) or "unknown",
        "tool_name": _coerce_optional_str(raw.get("tool_name")),
        "handler": _coerce_optional_str(raw.get("handler")),
        "paths": [redact_text(path, redact_patterns) for path in paths],
        "outcome": _coerce_enum(raw.get("outcome")),
        "exit_class": _coerce_enum(raw.get("exit_class") or raw.get("outcome")),
        "duration_ms": duration,
        "agent_id": _coerce_optional_str(raw.get("agent_id")),
        "agent_type": _coerce_optional_str(raw.get("agent_type")),
        "payload_digest": _coerce_optional_str(raw.get("payload_digest")),
        "extra": _redact_value(extra, redact_patterns),
    }


def rotate_if_needed(path: str | Path, max_bytes: int = ROTATE_BYTES) -> Path | None:
    """Rotate an oversized SQLite ledger aside; returns the rotated path or None.

    Enforcement wiring (calling this from the recorder) lands with PR-1b; PR-1a only
    ships the mechanism.
    """

    db_path = Path(path)
    if not db_path.is_file() or db_path.stat().st_size < max_bytes:
        return None
    connection = sqlite3.connect(db_path.as_posix())
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()
    stamp = utc_now_iso().replace(":", "").replace("-", "").replace("Z", "Z")
    rotated = db_path.with_name(f"{db_path.stem}-{stamp}{db_path.suffix}")
    counter = 1
    while rotated.exists():
        rotated = db_path.with_name(f"{db_path.stem}-{stamp}.{counter}{db_path.suffix}")
        counter += 1
    db_path.rename(rotated)
    return rotated


def _matches_filters(
    event: Mapping[str, Any],
    *,
    session_id: str | None,
    event_type: str | None,
    agent_id: str | None,
    since_ts: str | None,
) -> bool:
    if session_id is not None and event.get("session_id") != session_id:
        return False
    if event_type is not None and event.get("event_type") != event_type:
        return False
    if agent_id is not None and event.get("agent_id") != agent_id:
        return False
    if since_ts is not None and str(event.get("ts") or "") < since_ts:
        return False
    return True


class _BaseLedger:
    """Backend-agnostic ledger contract: append-only writes, merged ordered reads."""

    backend = "base"

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def read(
        self,
        *,
        session_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        since_ts: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - trivial default
        return None

    def __enter__(self) -> "_BaseLedger":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class SQLiteLedger(_BaseLedger):
    backend = SQLITE_BACKEND

    def _open_read_only_connection(self, *, immutable: bool) -> sqlite3.Connection:
        query = "mode=ro&immutable=1" if immutable else "mode=ro"
        connection = sqlite3.connect(
            f"{self.path.resolve().as_uri()}?{query}",
            timeout=BUSY_TIMEOUT_MS / 1000,
            uri=True,
        )
        connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        return connection

    def __init__(
        self,
        path: str | Path,
        *,
        redact_patterns: Iterable[str] = (),
        read_only: bool = False,
    ) -> None:
        self.path = Path(path)
        self.redact_patterns = tuple(redact_patterns)
        self.read_only = read_only
        self._read_only_immutable = False
        if read_only:
            if not self.path.is_file():
                raise LedgerError(f"ledger store does not exist: {self.path}")
            self.connection = self._open_read_only_connection(immutable=False)
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path.as_posix(), timeout=BUSY_TIMEOUT_MS / 1000)
        self.connection.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        # Switching journal modes takes an exclusive lock and can raise "database is
        # locked" while a concurrent writer holds a transaction (the busy handler does
        # not always cover this pragma). WAL is persistent in the file, so a brief
        # retry suffices; if every attempt loses the race the connection still works
        # in the file's existing (already-WAL) journal mode.
        for attempt in range(20):
            try:
                self.connection.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError:
                time.sleep(0.02 * (attempt + 1))
        self.connection.execute(_CREATE_TABLE)
        for statement in _CREATE_INDEXES:
            self.connection.execute(statement)
        self.connection.commit()

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if self.read_only:
            raise LedgerError("cannot append to a read-only ledger")
        normalized = normalize_event(event, redact_patterns=self.redact_patterns)
        row = dict(normalized)
        row["paths"] = json.dumps(normalized["paths"], sort_keys=True)
        row["extra"] = json.dumps(normalized["extra"], sort_keys=True, default=str)
        columns = ", ".join(EVENT_FIELDS)
        placeholders = ", ".join(f":{field}" for field in EVENT_FIELDS)
        self.connection.execute(
            f"INSERT INTO events ({columns}) VALUES ({placeholders})",
            row,
        )
        self.connection.commit()
        return normalized

    def read(
        self,
        *,
        session_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        since_ts: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        statement = f"SELECT {', '.join(EVENT_FIELDS)} FROM events ORDER BY ts, event_id"
        try:
            cursor = self.connection.execute(statement)
        except sqlite3.OperationalError as exc:
            # Sandboxed readers may be allowed to read the database file but not create the
            # shared-memory sidecar SQLite normally uses for a WAL database. Fall back to an
            # immutable snapshot only for that access failure; normal readers retain WAL-aware
            # behavior and see concurrent commits.
            if (
                not self.read_only
                or self._read_only_immutable
                or "unable to open database file" not in str(exc).lower()
            ):
                raise
            self.connection.close()
            self.connection = self._open_read_only_connection(immutable=True)
            self._read_only_immutable = True
            cursor = self.connection.execute(statement)
        events = []
        for values in cursor.fetchall():
            event = dict(zip(EVENT_FIELDS, values))
            event["paths"] = json.loads(event["paths"] or "[]")
            event["extra"] = json.loads(event["extra"] or "{}")
            if _matches_filters(
                event,
                session_id=session_id,
                event_type=event_type,
                agent_id=agent_id,
                since_ts=since_ts,
            ):
                events.append(event)
        if limit is not None:
            events = events[-limit:]
        return events

    def close(self) -> None:
        self.connection.close()


class JsonlLedger(_BaseLedger):
    """Fallback backend: per-session JSONL shards, same schema and read contract."""

    backend = JSONL_BACKEND

    def __init__(
        self,
        directory: str | Path,
        *,
        redact_patterns: Iterable[str] = (),
        read_only: bool = False,
    ) -> None:
        self.directory = Path(directory)
        self.redact_patterns = tuple(redact_patterns)
        self.read_only = read_only
        if not read_only:
            self.directory.mkdir(parents=True, exist_ok=True)

    def _shard_path(self, session_id: str | None) -> Path:
        token = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "unscoped") or "unscoped"
        return self.directory / f"{token}.jsonl"

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if self.read_only:
            raise LedgerError("cannot append to a read-only ledger")
        normalized = normalize_event(event, redact_patterns=self.redact_patterns)
        line = json.dumps(normalized, sort_keys=True, default=str)
        with self._shard_path(normalized["session_id"]).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return normalized

    def read(
        self,
        *,
        session_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        since_ts: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for shard in sorted(self.directory.glob("*.jsonl")):
            for line in shard.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if _matches_filters(
                    event,
                    session_id=session_id,
                    event_type=event_type,
                    agent_id=agent_id,
                    since_ts=since_ts,
                ):
                    events.append(event)
        events.sort(key=lambda event: (str(event.get("ts") or ""), str(event.get("event_id") or "")))
        if limit is not None:
            events = events[-limit:]
        return events


def open_ledger(
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    backend: str | None = None,
    path: str | Path | None = None,
    redact_patterns: Iterable[str] = (),
    read_only: bool = False,
) -> _BaseLedger:
    """Open the repo's ledger store with the selected backend.

    ``path`` overrides resolution entirely (a db file for sqlite, a shard directory
    for jsonl). Backend selection order: explicit argument, ``AEGIS_LEDGER_BACKEND``
    env var, sqlite default.
    """

    environment = env if env is not None else os.environ
    selected = (backend or environment.get(BACKEND_ENV_VAR) or SQLITE_BACKEND).strip().lower()
    if selected not in BACKENDS:
        raise LedgerError(f"unsupported ledger backend: {selected}")
    if selected == SQLITE_BACKEND:
        target = Path(path) if path is not None else store_path(cwd, environment)
        return SQLiteLedger(
            target,
            redact_patterns=redact_patterns,
            read_only=read_only,
        )
    target = Path(path) if path is not None else shards_dir(cwd, environment)
    return JsonlLedger(
        target,
        redact_patterns=redact_patterns,
        read_only=read_only,
    )


__all__ = [
    "BACKEND_ENV_VAR",
    "BACKENDS",
    "BUSY_TIMEOUT_MS",
    "DEFAULT_REDACT_PATTERNS",
    "EVENT_FIELDS",
    "EXIT_CLASSES",
    "JSONL_BACKEND",
    "JsonlLedger",
    "LEDGER_FILENAME",
    "LedgerError",
    "OUTCOME_CLASSES",
    "REDACTED",
    "ROTATE_BYTES",
    "SCHEMA_VERSION",
    "SHARDS_DIRNAME",
    "SQLITE_BACKEND",
    "SQLiteLedger",
    "compile_redact_patterns",
    "git_common_dir",
    "normalize_event",
    "open_ledger",
    "redact_text",
    "rotate_if_needed",
    "shards_dir",
    "store_dir",
    "store_path",
    "utc_now_iso",
]
