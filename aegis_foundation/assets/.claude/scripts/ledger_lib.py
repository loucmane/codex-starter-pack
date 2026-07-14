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
AGENT_ID_ENV_VAR = "AEGIS_AGENT_ID"
AGENT_TYPE_ENV_VAR = "AEGIS_AGENT_TYPE"
PARENT_AGENT_ID_ENV_VAR = "AEGIS_PARENT_AGENT_ID"
SESSION_ID_ENV_VAR = "AEGIS_SESSION_ID"

OUTCOME_CLASSES = ("pass", "fail", "interrupted", "unknown")
EXIT_CLASSES = OUTCOME_CLASSES

EVENT_FIELDS = (
    "schema_version",
    "event_id",
    "ts",
    "session_id",
    "repository_identity",
    "worktree_root",
    "branch",
    "head",
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
    "parent_agent_id",
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
    repository_identity TEXT,
    worktree_root TEXT,
    branch TEXT,
    head TEXT,
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
    parent_agent_id TEXT,
    payload_digest TEXT,
    extra TEXT NOT NULL DEFAULT '{}'
)
"""
_CREATE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)",
    "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)",
    "CREATE INDEX IF NOT EXISTS idx_events_repository ON events(repository_identity)",
    "CREATE INDEX IF NOT EXISTS idx_events_worktree ON events(worktree_root)",
    "CREATE INDEX IF NOT EXISTS idx_events_branch ON events(branch)",
    "CREATE INDEX IF NOT EXISTS idx_events_head ON events(head)",
    "CREATE INDEX IF NOT EXISTS idx_events_parent_agent ON events(parent_agent_id)",
)

_ADDITIVE_COLUMNS = {
    "repository_identity": "TEXT",
    "worktree_root": "TEXT",
    "head": "TEXT",
    "parent_agent_id": "TEXT",
}


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


def _git_output(base: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=str(base),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def repository_identity(common_dir: str | Path) -> str:
    canonical = Path(common_dir).resolve().as_posix().encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def repository_context(cwd: str | Path | None = None) -> dict[str, str | None]:
    """Capture immutable repository/worktree context for one ledger-open boundary."""

    base = (Path(cwd) if cwd is not None else Path.cwd()).resolve()
    common = git_common_dir(base)
    worktree = _git_output(base, "rev-parse", "--show-toplevel")
    branch = _git_output(base, "branch", "--show-current")
    head = _git_output(base, "rev-parse", "HEAD")
    return {
        "repository_identity": repository_identity(common),
        "worktree_root": Path(worktree).resolve().as_posix() if worktree else None,
        "branch": branch,
        "head": head,
        "cwd": base.as_posix(),
    }


def capture_context(
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, str | None]:
    """Repository context plus explicit adapter-provided identity defaults."""

    environment = env if env is not None else os.environ
    context = repository_context(cwd)
    context.update(
        {
            "session_id": _coerce_optional_str(environment.get(SESSION_ID_ENV_VAR)),
            "agent_id": _coerce_optional_str(environment.get(AGENT_ID_ENV_VAR)),
            "agent_type": _coerce_optional_str(environment.get(AGENT_TYPE_ENV_VAR)),
            "parent_agent_id": _coerce_optional_str(environment.get(PARENT_AGENT_ID_ENV_VAR)),
        }
    )
    return context


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
    defaults: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill, coerce, and redact an event into the v1 schema.

    Missing fields degrade to ``None`` (the recorder must never crash on a payload
    shape); unknown top-level keys are preserved under ``extra`` instead of being
    silently dropped.
    """

    raw = dict(event)
    context = dict(defaults or {})

    def resolved_value(key: str) -> Any:
        explicit = raw.get(key)
        return explicit if _coerce_optional_str(explicit) is not None else context.get(key)

    paths_value = raw.get("paths")
    if paths_value is None:
        paths: list[str] = []
    elif isinstance(paths_value, (list, tuple)):
        paths = [str(item) for item in paths_value]
    else:
        paths = [str(paths_value)]

    extra_value = raw.get("extra")
    extra = dict(extra_value) if isinstance(extra_value, Mapping) else {}
    for key, raw_value in raw.items():
        if key not in EVENT_FIELDS:
            extra[str(key)] = raw_value

    duration: int | None
    try:
        duration = int(raw["duration_ms"]) if raw.get("duration_ms") is not None else None
    except (TypeError, ValueError):
        duration = None

    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": _coerce_optional_str(raw.get("event_id")) or uuid.uuid4().hex,
        "ts": _coerce_optional_str(raw.get("ts")) or utc_now_iso(),
        "session_id": _coerce_optional_str(resolved_value("session_id")),
        "repository_identity": _coerce_optional_str(resolved_value("repository_identity")),
        "worktree_root": _coerce_optional_str(resolved_value("worktree_root")),
        "branch": _coerce_optional_str(resolved_value("branch")),
        "head": _coerce_optional_str(resolved_value("head")),
        "cwd": _coerce_optional_str(resolved_value("cwd")),
        "event_type": _coerce_optional_str(raw.get("event_type")) or "unknown",
        "tool_name": _coerce_optional_str(raw.get("tool_name")),
        "handler": _coerce_optional_str(raw.get("handler")),
        "paths": [redact_text(path, redact_patterns) for path in paths],
        "outcome": _coerce_enum(raw.get("outcome")),
        "exit_class": _coerce_enum(raw.get("exit_class") or raw.get("outcome")),
        "duration_ms": duration,
        "agent_id": _coerce_optional_str(resolved_value("agent_id")),
        "agent_type": _coerce_optional_str(resolved_value("agent_type")),
        "parent_agent_id": _coerce_optional_str(resolved_value("parent_agent_id")),
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
    repository_identity: str | None,
    worktree_root: str | None,
    branch: str | None,
    head: str | None,
    parent_agent_id: str | None,
    since_ts: str | None,
) -> bool:
    if session_id is not None and event.get("session_id") != session_id:
        return False
    if event_type is not None and event.get("event_type") != event_type:
        return False
    if agent_id is not None and event.get("agent_id") != agent_id:
        return False
    if repository_identity is not None and event.get("repository_identity") != repository_identity:
        return False
    if worktree_root is not None and event.get("worktree_root") != worktree_root:
        return False
    if branch is not None and event.get("branch") != branch:
        return False
    if head is not None and event.get("head") != head:
        return False
    if parent_agent_id is not None and event.get("parent_agent_id") != parent_agent_id:
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
        repository_identity: str | None = None,
        worktree_root: str | None = None,
        branch: str | None = None,
        head: str | None = None,
        parent_agent_id: str | None = None,
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
        defaults: Mapping[str, Any] | None = None,
    ) -> None:
        self.path = Path(path)
        self.redact_patterns = tuple(redact_patterns)
        self.read_only = read_only
        self.defaults = dict(defaults or {})
        self._read_only_immutable = False
        if read_only:
            if not self.path.is_file():
                raise LedgerError(f"ledger store does not exist: {self.path}")
            self.connection = self._open_read_only_connection(immutable=False)
            self._columns = self._table_columns()
            # Sandboxed readers may open the database file but be unable to create or
            # access SQLite's WAL shared-memory sidecar.  ``_table_columns`` intentionally
            # converts that probe failure to an empty set; establish the immutable
            # fallback *before* read() constructs its SELECT list, otherwise every real
            # column is projected as ``NULL AS <field>`` and valid events appear empty.
            if not self._columns:
                self.connection.close()
                self.connection = self._open_read_only_connection(immutable=True)
                self._read_only_immutable = True
                self._columns = self._table_columns()
            if not self._columns:
                self.connection.close()
                raise LedgerError(f"ledger schema is unreadable: {self.path}")
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
        existing_columns = self._table_columns()
        for column, declaration in _ADDITIVE_COLUMNS.items():
            if column not in existing_columns:
                self.connection.execute(f"ALTER TABLE events ADD COLUMN {column} {declaration}")
        for statement in _CREATE_INDEXES:
            self.connection.execute(statement)
        self.connection.commit()
        self._columns = self._table_columns()

    def _table_columns(self) -> set[str]:
        try:
            return {str(row[1]) for row in self.connection.execute("PRAGMA table_info(events)")}
        except sqlite3.OperationalError:
            return set()

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if self.read_only:
            raise LedgerError("cannot append to a read-only ledger")
        normalized = normalize_event(
            event,
            redact_patterns=self.redact_patterns,
            defaults=self.defaults,
        )
        row = dict(normalized)
        row["paths"] = json.dumps(normalized["paths"], sort_keys=True)
        row["extra"] = json.dumps(normalized["extra"], sort_keys=True, default=str)
        columns = ", ".join(EVENT_FIELDS)
        placeholders = ", ".join(f":{field}" for field in EVENT_FIELDS)
        for attempt in range(20):
            try:
                self.connection.execute(
                    f"INSERT INTO events ({columns}) VALUES ({placeholders})",
                    row,
                )
                self.connection.commit()
                break
            except sqlite3.OperationalError as exc:
                self.connection.rollback()
                if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():
                    raise
                if attempt == 19:
                    raise
                time.sleep(0.02 * (attempt + 1))
        return normalized

    def read(
        self,
        *,
        session_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        repository_identity: str | None = None,
        worktree_root: str | None = None,
        branch: str | None = None,
        head: str | None = None,
        parent_agent_id: str | None = None,
        since_ts: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        filters = {
            "session_id": session_id,
            "event_type": event_type,
            "agent_id": agent_id,
            "repository_identity": repository_identity,
            "worktree_root": worktree_root,
            "branch": branch,
            "head": head,
            "parent_agent_id": parent_agent_id,
        }
        if any(
            value is not None and field not in self._columns for field, value in filters.items()
        ):
            return []
        selected = [
            field if field in self._columns else f"NULL AS {field}" for field in EVENT_FIELDS
        ]
        where = [f"{field} = :{field}" for field, value in filters.items() if value is not None]
        if since_ts is not None:
            where.append("ts >= :since_ts")
        statement = f"SELECT {', '.join(selected)} FROM events"
        if where:
            statement += " WHERE " + " AND ".join(where)
        statement += " ORDER BY ts, event_id"
        parameters = {**{key: value for key, value in filters.items() if value is not None}}
        if since_ts is not None:
            parameters["since_ts"] = since_ts
        try:
            cursor = self.connection.execute(statement, parameters)
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
            self._columns = self._table_columns()
            cursor = self.connection.execute(statement, parameters)
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
                repository_identity=repository_identity,
                worktree_root=worktree_root,
                branch=branch,
                head=head,
                parent_agent_id=parent_agent_id,
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
        defaults: Mapping[str, Any] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.redact_patterns = tuple(redact_patterns)
        self.read_only = read_only
        self.defaults = dict(defaults or {})
        if not read_only:
            self.directory.mkdir(parents=True, exist_ok=True)

    def _shard_path(self, session_id: str | None) -> Path:
        token = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "unscoped") or "unscoped"
        return self.directory / f"{token}.jsonl"

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if self.read_only:
            raise LedgerError("cannot append to a read-only ledger")
        normalized = normalize_event(
            event,
            redact_patterns=self.redact_patterns,
            defaults=self.defaults,
        )
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
        repository_identity: str | None = None,
        worktree_root: str | None = None,
        branch: str | None = None,
        head: str | None = None,
        parent_agent_id: str | None = None,
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
                event = {field: event.get(field) for field in EVENT_FIELDS} | {
                    key: value for key, value in event.items() if key not in EVENT_FIELDS
                }
                event["paths"] = event.get("paths") if isinstance(event.get("paths"), list) else []
                event["extra"] = (
                    event.get("extra") if isinstance(event.get("extra"), Mapping) else {}
                )
                if _matches_filters(
                    event,
                    session_id=session_id,
                    event_type=event_type,
                    agent_id=agent_id,
                    repository_identity=repository_identity,
                    worktree_root=worktree_root,
                    branch=branch,
                    head=head,
                    parent_agent_id=parent_agent_id,
                    since_ts=since_ts,
                ):
                    events.append(event)
        events.sort(
            key=lambda event: (str(event.get("ts") or ""), str(event.get("event_id") or ""))
        )
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
    context_cwd = cwd if cwd is not None else (None if path is not None else Path.cwd())
    defaults = capture_context(context_cwd, environment) if context_cwd is not None else {}
    if selected == SQLITE_BACKEND:
        target = Path(path) if path is not None else store_path(cwd, environment)
        return SQLiteLedger(
            target,
            redact_patterns=redact_patterns,
            read_only=read_only,
            defaults=defaults,
        )
    target = Path(path) if path is not None else shards_dir(cwd, environment)
    return JsonlLedger(
        target,
        redact_patterns=redact_patterns,
        read_only=read_only,
        defaults=defaults,
    )


__all__ = [
    "BACKEND_ENV_VAR",
    "AGENT_ID_ENV_VAR",
    "AGENT_TYPE_ENV_VAR",
    "PARENT_AGENT_ID_ENV_VAR",
    "SESSION_ID_ENV_VAR",
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
    "capture_context",
    "git_common_dir",
    "normalize_event",
    "open_ledger",
    "redact_text",
    "repository_context",
    "repository_identity",
    "rotate_if_needed",
    "shards_dir",
    "store_dir",
    "store_path",
    "utc_now_iso",
]
