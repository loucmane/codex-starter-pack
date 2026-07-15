"""Read-only Codex topology diagnostics and canonical-home migration planning.

The module deliberately has no write helpers and never executes a Codex binary.  It reads
bounded, non-secret metadata from explicitly selected Codex homes, project manifests,
session metadata, executable paths, and procfs.  The resulting status can be transformed
into a deterministic Task 257 plan, but Task 256 cannot apply that plan.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tomllib
from typing import Any, Mapping, Sequence

from aegis_foundation import codex_remote_trust

SCHEMA_VERSION = 1
MAX_CONFIG_BYTES = 2 * 1024 * 1024
MAX_HOOK_BYTES = 2 * 1024 * 1024
MAX_SESSION_META_BYTES = 64 * 1024
MAX_PROCESS_CMDLINE_BYTES = 64 * 1024
MAX_WRAPPER_BYTES = 256 * 1024
MAX_SESSION_FILES = 20_000
MAX_COMMAND_CANDIDATES = 64
MAX_PROCESSES = 10_000
STALE_THREAD_MESSAGE = (
    "Project is trusted on disk; this session predates the trust change and requires "
    "a fresh session."
)
THREAD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
VERSION_RE = re.compile(r"(?:^|/)(\d+\.\d+\.\d+)(?:[-/]|$)")
ACTIVE_WORK_STATES = frozenset({"unknown", "present", "drained"})
PROCESS_SCOPES = frozenset({"unknown", "host", "fixture"})


class CodexTopologyError(RuntimeError):
    """Invalid diagnostic input or unsafe metadata."""


def _absolute_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve(strict=False)


def _state_root(value: str | os.PathLike[str], *, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise CodexTopologyError(f"{label} must be absolute: {path}")
    resolved = path.resolve(strict=False)
    if resolved == Path(resolved.anchor):
        raise CodexTopologyError(f"{label} must not be the filesystem root: {resolved}")
    return resolved


def _path_text(path: Path) -> str:
    return path.as_posix()


def _fact(
    value: Any,
    *,
    state: str = "known",
    source: str,
    observed: bool = True,
    detail: str = "",
) -> dict[str, Any]:
    if state not in {"known", "unknown", "invalid", "not_applicable"}:
        raise AssertionError(f"unsupported fact state: {state}")
    return {
        "value": value,
        "state": state,
        "source": source,
        "observed": observed,
        "detail": detail,
    }


def _unknown(*, source: str, detail: str) -> dict[str, Any]:
    return _fact(None, state="unknown", source=source, observed=False, detail=detail)


def _invalid(*, source: str, detail: str) -> dict[str, Any]:
    return _fact(None, state="invalid", source=source, observed=True, detail=detail)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _read_regular_bytes(path: Path, *, limit: int, label: str) -> bytes:
    if path.is_symlink():
        raise CodexTopologyError(f"{label} must not be a symlink: {path}")
    try:
        info = path.stat()
    except OSError as exc:
        raise CodexTopologyError(f"{label} cannot be inspected: {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise CodexTopologyError(f"{label} must be a regular file: {path}")
    if info.st_size > limit:
        raise CodexTopologyError(f"{label} exceeds the {limit}-byte diagnostic limit: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CodexTopologyError(f"{label} cannot be read: {path}") from exc


def _parse_utc(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _version_from_path(path: Path) -> str | None:
    match = VERSION_RE.search(path.as_posix())
    return match.group(1) if match else None


def _safe_resolve(path: Path) -> tuple[Path | None, str | None]:
    try:
        return path.resolve(strict=False), None
    except (OSError, RuntimeError) as exc:
        return None, type(exc).__name__


def _path_surface(path: Path, *, label: str) -> dict[str, Any]:
    source = path.as_posix()
    if not path.exists() and not path.is_symlink():
        return {
            "path": source,
            "kind": "missing",
            "resolved": _unknown(source=source, detail=f"{label} does not exist"),
        }
    try:
        info = path.lstat()
    except OSError as exc:
        return {
            "path": source,
            "kind": "invalid",
            "resolved": _invalid(
                source=source, detail=f"{label} lstat failed: {type(exc).__name__}"
            ),
        }
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(path)
        resolved, error = _safe_resolve(path)
        return {
            "path": source,
            "kind": "symlink",
            "target": target,
            "resolved": (
                _fact(_path_text(resolved), source=source, detail=f"{label} symlink target")
                if resolved is not None
                else _invalid(source=source, detail=f"{label} symlink cannot resolve: {error}")
            ),
        }
    kind = (
        "directory"
        if stat.S_ISDIR(info.st_mode)
        else (
            "regular"
            if stat.S_ISREG(info.st_mode)
            else "socket" if stat.S_ISSOCK(info.st_mode) else "other"
        )
    )
    resolved, error = _safe_resolve(path)
    return {
        "path": source,
        "kind": kind,
        "resolved": (
            _fact(_path_text(resolved), source=source, detail=f"{label} canonical identity")
            if resolved is not None
            else _invalid(source=source, detail=f"{label} cannot resolve: {error}")
        ),
    }


def _canonical_project(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise CodexTopologyError(f"project path must be absolute: {path}")
    try:
        canonical = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise CodexTopologyError(f"project path cannot be resolved: {path}") from exc
    if not canonical.is_dir() or canonical == Path(canonical.anchor):
        raise CodexTopologyError(f"project path is not a safe project directory: {canonical}")
    return canonical


def _config_snapshot(home: Path, projects: Sequence[Path]) -> dict[str, Any]:
    path = home / "config.toml"
    if not path.exists() and not path.is_symlink():
        return {
            "path": path.as_posix(),
            "state": "missing",
            "sha256": None,
            "sqlite_home": _unknown(
                source=path.as_posix(),
                detail="config.toml is absent; CODEX_SQLITE_HOME or CODEX_HOME decides",
            ),
            "projects": [
                {
                    "project": project.as_posix(),
                    "status": "missing",
                    "trust_level": None,
                    "configured_path": None,
                }
                for project in projects
            ],
        }
    try:
        content = _read_regular_bytes(path, limit=MAX_CONFIG_BYTES, label="Codex config")
        parsed = tomllib.loads(content.decode("utf-8"))
    except (CodexTopologyError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        return {
            "path": path.as_posix(),
            "state": "invalid",
            "sha256": None,
            "error": type(exc).__name__,
            "sqlite_home": _invalid(
                source=path.as_posix(),
                detail="config.toml is not safe, bounded, UTF-8 TOML",
            ),
            "projects": [
                {
                    "project": project.as_posix(),
                    "status": "invalid",
                    "trust_level": None,
                    "configured_path": None,
                }
                for project in projects
            ],
        }

    raw_sqlite = parsed.get("sqlite_home")
    if raw_sqlite is None:
        sqlite_fact = _unknown(
            source=f"{path.as_posix()}::sqlite_home",
            detail="sqlite_home is not configured in this home",
        )
    elif not isinstance(raw_sqlite, str) or not raw_sqlite.strip():
        sqlite_fact = _invalid(
            source=f"{path.as_posix()}::sqlite_home",
            detail="sqlite_home must be a non-empty string",
        )
    else:
        sqlite_path = Path(raw_sqlite).expanduser()
        if not sqlite_path.is_absolute():
            sqlite_fact = _invalid(
                source=f"{path.as_posix()}::sqlite_home",
                detail="relative sqlite_home depends on CWD and is not canonical-home safe",
            )
        else:
            sqlite_fact = _fact(
                _path_text(sqlite_path.resolve(strict=False)),
                source=f"{path.as_posix()}::sqlite_home",
                detail="explicit Codex sqlite_home",
            )

    raw_projects = parsed.get("projects")
    projects_table = raw_projects if isinstance(raw_projects, Mapping) else {}
    project_rows: list[dict[str, Any]] = []
    for project in projects:
        matches: list[tuple[str, object]] = []
        for raw_path, raw_entry in projects_table.items():
            if not isinstance(raw_path, str):
                continue
            candidate, error = _safe_resolve(Path(raw_path).expanduser())
            if error is None and candidate == project:
                matches.append((raw_path, raw_entry))
        if len(matches) > 1:
            project_rows.append(
                {
                    "project": project.as_posix(),
                    "status": "invalid",
                    "trust_level": None,
                    "configured_path": None,
                    "detail": "multiple config paths resolve to the same project",
                }
            )
            continue
        if not matches:
            project_rows.append(
                {
                    "project": project.as_posix(),
                    "status": "missing",
                    "trust_level": None,
                    "configured_path": None,
                }
            )
            continue
        configured_path, raw_entry = matches[0]
        trust_level = raw_entry.get("trust_level") if isinstance(raw_entry, Mapping) else None
        canonical_match = Path(configured_path).expanduser().as_posix() == project.as_posix()
        status_value = (
            "trusted"
            if trust_level == "trusted" and canonical_match
            else (
                "trusted_alias"
                if trust_level == "trusted"
                else "untrusted" if trust_level == "untrusted" else "invalid"
            )
        )
        project_rows.append(
            {
                "project": project.as_posix(),
                "status": status_value,
                "trust_level": trust_level if isinstance(trust_level, str) else None,
                "configured_path": configured_path,
            }
        )
    return {
        "path": path.as_posix(),
        "state": "valid",
        "sha256": _sha256(content),
        "sqlite_home": sqlite_fact,
        "projects": project_rows,
    }


def _allowlist_authority(home: Path, projects: Sequence[Path]) -> dict[str, Any]:
    path = home / codex_remote_trust.ALLOWLIST_FILENAME
    try:
        entries = codex_remote_trust.load_allowlist(path, allow_missing=True)
    except codex_remote_trust.RemoteTrustError as exc:
        return {
            "path": path.as_posix(),
            "state": "invalid",
            "error": type(exc).__name__,
            "projects": [
                {
                    "project": project.as_posix(),
                    "authorized": None,
                    "approved_at": None,
                }
                for project in projects
            ],
        }
    rows: list[dict[str, Any]] = []
    for project in projects:
        matches = [
            entry
            for entry in entries
            if Path(entry.path).expanduser().resolve(strict=False) == project
        ]
        if len(matches) == 1:
            approved = _parse_utc(matches[0].approved_at)
            rows.append(
                {
                    "project": project.as_posix(),
                    "authorized": True,
                    "approved_at": (
                        approved.isoformat().replace("+00:00", "Z")
                        if approved is not None
                        else None
                    ),
                }
            )
        else:
            rows.append(
                {
                    "project": project.as_posix(),
                    "authorized": False if not matches else None,
                    "approved_at": None,
                }
            )
    return {
        "path": path.as_posix(),
        "state": "present" if path.exists() else "missing",
        "projects": rows,
    }


def _tracked_hook_guidance(project: Path) -> dict[str, Any]:
    manifest = project / ".aegis" / "foundation-manifest.json"
    if not manifest.exists() and not manifest.is_symlink():
        return {
            "state": "missing",
            "source": manifest.as_posix(),
            "valid": False,
        }
    try:
        content = _read_regular_bytes(
            manifest,
            limit=MAX_CONFIG_BYTES,
            label="Aegis foundation manifest",
        )
        parsed = json.loads(content)
    except (CodexTopologyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "state": "invalid",
            "source": manifest.as_posix(),
            "valid": False,
            "error": type(exc).__name__,
        }
    gates = parsed.get("gates") if isinstance(parsed, Mapping) else None
    matches = (
        [
            gate
            for gate in gates
            if isinstance(gate, Mapping) and gate.get("id") == "codex.hook_trust"
        ]
        if isinstance(gates, list)
        else []
    )
    expected = {
        "settings_path": codex_remote_trust.HOOK_SETTINGS_PATH,
        "review_command": codex_remote_trust.HOOK_REVIEW_COMMAND,
        "hash_scope": codex_remote_trust.HOOK_HASH_SCOPE,
        "bypass_allowed": False,
    }
    valid = len(matches) == 1 and all(
        matches[0].get(key) == value for key, value in expected.items()
    )
    return {
        "state": "valid" if valid else "invalid",
        "source": manifest.as_posix(),
        "valid": valid,
        "contract": expected,
    }


def _hook_definition(project: Path) -> dict[str, Any]:
    path = project / codex_remote_trust.HOOK_SETTINGS_PATH
    if not path.exists() and not path.is_symlink():
        return {
            "state": "missing",
            "path": path.as_posix(),
            "sha256": None,
        }
    try:
        content = _read_regular_bytes(path, limit=MAX_HOOK_BYTES, label="Codex hook definition")
        parsed = json.loads(content)
    except (CodexTopologyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "sha256": None,
            "error": type(exc).__name__,
        }
    if not isinstance(parsed, Mapping):
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "sha256": None,
            "error": "definition_not_object",
        }
    return {
        "state": "present",
        "path": path.as_posix(),
        "sha256": _sha256(content),
    }


def _session_store(home: Path, name: str) -> dict[str, Any]:
    raw = home / name
    surface = _path_surface(raw, label=f"Codex {name}")
    resolved_fact = surface["resolved"]
    resolved_value = resolved_fact.get("value")
    count = 0
    truncated = False
    if resolved_fact.get("state") == "known" and isinstance(resolved_value, str):
        resolved = Path(resolved_value)
        if resolved.is_dir():
            try:
                for candidate in resolved.rglob("*.jsonl"):
                    if candidate.is_file() and not candidate.is_symlink():
                        count += 1
                        if count >= MAX_SESSION_FILES:
                            truncated = True
                            break
            except OSError:
                surface["scan_state"] = "invalid"
            else:
                surface["scan_state"] = "known"
        else:
            surface["scan_state"] = "not_applicable"
    else:
        surface["scan_state"] = "unknown"
    surface["jsonl_count"] = count
    surface["count_truncated"] = truncated
    return surface


def _session_candidates(store: dict[str, Any], thread_id: str) -> tuple[list[Path], bool]:
    resolved = store.get("resolved", {}).get("value")
    if not isinstance(resolved, str):
        return [], False
    root = Path(resolved)
    if not root.is_dir():
        return [], False
    matches: list[Path] = []
    inspected = 0
    truncated = False
    try:
        for candidate in root.rglob("*.jsonl"):
            if not candidate.is_file() or candidate.is_symlink():
                continue
            inspected += 1
            if inspected > MAX_SESSION_FILES:
                truncated = True
                break
            name = candidate.name
            if candidate.stem == thread_id or name.endswith(f"-{thread_id}.jsonl"):
                matches.append(candidate)
                if len(matches) > 2:
                    break
    except OSError:
        return [], True
    return sorted(matches, key=lambda item: item.as_posix()), truncated


def _session_metadata(path: Path, expected_thread_id: str) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            line = handle.readline(MAX_SESSION_META_BYTES + 1)
    except OSError as exc:
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": type(exc).__name__,
        }
    if len(line) > MAX_SESSION_META_BYTES:
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": "metadata_line_too_large",
        }
    try:
        parsed = json.loads(line)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": "metadata_not_json",
        }
    payload = parsed.get("payload") if isinstance(parsed, Mapping) else None
    if parsed.get("type") != "session_meta" or not isinstance(payload, Mapping):
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": "first_record_not_session_meta",
        }
    thread_id = payload.get("id")
    started = _parse_utc(payload.get("timestamp"))
    cwd = payload.get("cwd")
    if thread_id != expected_thread_id or started is None or not isinstance(cwd, str):
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": "required_session_metadata_invalid",
        }
    cwd_path = Path(cwd).expanduser()
    if not cwd_path.is_absolute():
        return {
            "state": "invalid",
            "path": path.as_posix(),
            "error": "session_cwd_not_absolute",
        }
    source = payload.get("source")
    source_kind = "unknown"
    if isinstance(source, str):
        source_kind = source
    elif isinstance(source, Mapping):
        source_kind = next(iter(sorted(str(key) for key in source)), "unknown")
    return {
        "state": "valid",
        "path": path.as_posix(),
        "thread_id": thread_id,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "cwd": cwd_path.resolve(strict=False).as_posix(),
        "source_kind": source_kind,
    }


def _sqlite_inventory(
    home: Path,
    *,
    canonical_sqlite_home: Path | None,
    config: Mapping[str, Any],
    environment: Mapping[str, str],
    is_canonical: bool,
) -> dict[str, Any]:
    configured = config.get("sqlite_home", {})
    configured_value = configured.get("value") if isinstance(configured, Mapping) else None
    env_value = environment.get("CODEX_SQLITE_HOME", "").strip() if is_canonical else ""
    if canonical_sqlite_home is not None and is_canonical:
        effective = canonical_sqlite_home
        source = "--canonical-sqlite-home"
    elif isinstance(configured_value, str):
        effective = Path(configured_value)
        source = f"{home.as_posix()}/config.toml::sqlite_home"
    elif env_value:
        effective = _absolute_path(env_value)
        source = "environment::CODEX_SQLITE_HOME"
    else:
        effective = home
        source = "CODEX_HOME default"

    roots = {
        effective.resolve(strict=False),
        home.resolve(strict=False),
        (home / "sqlite").resolve(strict=False),
    }
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in sorted(roots, key=lambda item: item.as_posix()):
        if not root.is_dir():
            continue
        try:
            candidates = sorted(root.glob("state_*.sqlite"))
        except OSError:
            continue
        for path in candidates:
            if path.is_symlink() or not path.is_file():
                continue
            identity = path.resolve(strict=False).as_posix()
            if identity in seen:
                continue
            seen.add(identity)
            files.append(
                {
                    "path": path.as_posix(),
                    "resolved": identity,
                    "name": path.name,
                    "size": path.stat().st_size,
                }
            )
    return {
        "effective_home": _fact(
            effective.resolve(strict=False).as_posix(),
            source=source,
            detail="resolved SQLite state owner",
        ),
        "selection_explicit": _fact(
            source != "CODEX_HOME default",
            source=source,
            detail="whether the SQLite authority was selected beyond the CODEX_HOME default",
        ),
        "roots_with_state": sorted(
            {
                Path(str(item["resolved"])).parent.as_posix()
                for item in files
                if item.get("resolved")
            }
        ),
        "files": files,
    }


def _package_inventory(home: Path) -> dict[str, Any]:
    current = home / "packages" / "standalone" / "current"
    surface = _path_surface(current, label="Codex standalone current")
    resolved_value = surface.get("resolved", {}).get("value")
    resolved = Path(resolved_value) if isinstance(resolved_value, str) else None
    binary = resolved / "bin" / "codex" if resolved is not None else None
    return {
        "current": surface,
        "version": _version_from_path(resolved) if resolved is not None else None,
        "binary": binary.as_posix() if binary is not None else None,
        "binary_present": bool(binary is not None and binary.is_file()),
    }


def _lifecycle_inventory(home: Path) -> dict[str, Any]:
    socket = home / "app-server-control" / "app-server-control.sock"
    daemon = home / "app-server-daemon"
    return {
        "control_socket": _path_surface(socket, label="Codex app-server control socket"),
        "daemon_directory": _path_surface(daemon, label="Codex app-server daemon directory"),
        "pid_lock_present": (daemon / "app-server.pid.lock").is_file(),
        "updater_lock_present": (daemon / "app-server-updater.pid.lock").is_file(),
    }


def _home_inventory(
    home: Path,
    *,
    canonical_home: Path,
    canonical_sqlite_home: Path | None,
    projects: Sequence[Path],
    thread_ids: Sequence[str],
    environment: Mapping[str, str],
) -> dict[str, Any]:
    canonical = home.resolve(strict=False)
    config = _config_snapshot(home, projects)
    sessions = _session_store(home, "sessions")
    archived = _session_store(home, "archived_sessions")
    requested: list[dict[str, Any]] = []
    for thread_id in thread_ids:
        matches: list[Path] = []
        search_incomplete = False
        for store in (sessions, archived):
            store_matches, truncated = _session_candidates(store, thread_id)
            matches.extend(store_matches)
            search_incomplete = search_incomplete or truncated
        unique = sorted(
            {path.resolve(strict=False) for path in matches}, key=lambda item: item.as_posix()
        )
        if search_incomplete:
            requested.append(
                {
                    "state": "unknown",
                    "thread_id": thread_id,
                    "paths": [path.as_posix() for path in unique],
                    "error": "session_search_incomplete",
                }
            )
        elif len(unique) == 1:
            requested.append(_session_metadata(unique[0], thread_id))
        elif not unique:
            requested.append(
                {
                    "state": "missing",
                    "thread_id": thread_id,
                    "path": None,
                }
            )
        else:
            requested.append(
                {
                    "state": "ambiguous",
                    "thread_id": thread_id,
                    "paths": [path.as_posix() for path in unique],
                }
            )
    return {
        "path": home.as_posix(),
        "canonical_path": canonical.as_posix(),
        "role": "canonical" if canonical == canonical_home else "candidate",
        "exists": home.is_dir(),
        "config": config,
        "allowlist_authority": _allowlist_authority(home, projects),
        "session_stores": [sessions, archived],
        "requested_threads": requested,
        "sqlite": _sqlite_inventory(
            home,
            canonical_sqlite_home=canonical_sqlite_home,
            config=config,
            environment=environment,
            is_canonical=canonical == canonical_home,
        ),
        "package": _package_inventory(home),
        "lifecycle": _lifecycle_inventory(home),
    }


def _wrapper_signals(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        candidate = path.resolve(strict=False)
    else:
        candidate = path
    try:
        info = candidate.stat()
    except OSError:
        return {"wrapper": False, "signals": [], "sha256": None}
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_WRAPPER_BYTES:
        return {"wrapper": False, "signals": [], "sha256": None}
    try:
        content = candidate.read_bytes()
    except OSError:
        return {"wrapper": False, "signals": [], "sha256": None}
    if b"\x00" in content[:4096]:
        return {"wrapper": False, "signals": [], "sha256": None}
    signals: list[str] = []
    checks = (
        ("sets_CODEX_HOME", b"CODEX_HOME"),
        ("references_global_home", b"CODEX_GLOBAL_DIR"),
        ("references_remote_home", b"AEGIS_REMOTE_CONTROL_HOME"),
        ("references_remote_control", b"remote-control"),
        ("uses_cwd_or_pwd", b"pwd"),
        ("uses_project_root", b"git rev-parse"),
    )
    for label, marker in checks:
        if marker in content:
            signals.append(label)
    home_routing = (
        "sets_CODEX_HOME" in signals
        and ("references_global_home" in signals or "references_remote_home" in signals)
        and ("uses_cwd_or_pwd" in signals or "uses_project_root" in signals)
    )
    return {
        "wrapper": bool(signals),
        "home_routing": home_routing,
        "signals": signals,
        "sha256": _sha256(content),
    }


def _command_inventory(
    homes: Sequence[Path],
    *,
    explicit_commands: Sequence[str | os.PathLike[str]],
    environment: Mapping[str, str],
) -> list[dict[str, Any]]:
    candidates: list[tuple[Path, str]] = []
    for raw in explicit_commands:
        candidates.append((_absolute_path(raw), "explicit"))
    for home in homes:
        candidates.append((home / "packages" / "standalone" / "current" / "bin" / "codex", "home"))
        candidates.append((home / "bin" / "codex", "home"))
    for raw_dir in environment.get("PATH", "").split(os.pathsep):
        if raw_dir.strip():
            candidates.append((Path(raw_dir).expanduser() / "codex", "PATH"))

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, source in candidates:
        if len(rows) >= MAX_COMMAND_CANDIDATES:
            break
        if not path.exists() and not path.is_symlink():
            continue
        absolute = path if path.is_absolute() else _absolute_path(path)
        lexical = absolute.as_posix()
        if lexical in seen:
            continue
        seen.add(lexical)
        resolved, error = _safe_resolve(absolute)
        wrapper = _wrapper_signals(absolute)
        rows.append(
            {
                "path": lexical,
                "source": source,
                "resolved": resolved.as_posix() if resolved is not None else None,
                "resolve_error": error,
                "version": _version_from_path(resolved) if resolved is not None else None,
                "executable": os.access(absolute, os.X_OK),
                "wrapper": wrapper,
            }
        )
    return sorted(rows, key=lambda row: (str(row["source"]), str(row["path"])))


def _read_proc_bytes(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        return handle.read(limit + 1)


def _process_role(arguments: Sequence[str]) -> str:
    joined = "\n".join(arguments)
    if "app-server" in arguments and "--remote-control" in arguments:
        return "remote_control_server"
    if "app-server" in arguments:
        return "app_server"
    if "pid-update-loop" in joined:
        return "daemon_update_loop"
    if any("codex" in Path(argument).name for argument in arguments[:1]):
        return "client"
    return "codex_related"


def _safe_unix_endpoint(arguments: Sequence[str]) -> str | None:
    for flag in ("--listen", "--remote"):
        try:
            index = arguments.index(flag)
        except ValueError:
            continue
        if index + 1 < len(arguments):
            value = arguments[index + 1]
            if value.startswith("unix://"):
                return value
            if value.startswith(("ws://", "wss://")):
                return value.split(":", 1)[0] + "://<redacted>"
    return None


def _open_codex_sqlite_paths(process_dir: Path, homes: Sequence[Path]) -> list[str]:
    fd_root = process_dir / "fd"
    if not fd_root.is_dir():
        return []
    canonical_homes = [home.resolve(strict=False) for home in homes]
    matches: set[str] = set()
    try:
        descriptors = list(fd_root.iterdir())[:512]
    except OSError:
        return []
    for descriptor in descriptors:
        try:
            target = descriptor.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        name = target.name
        if not (
            name.startswith("state_")
            and (
                name.endswith(".sqlite")
                or name.endswith(".sqlite-wal")
                or name.endswith(".sqlite-shm")
            )
        ):
            continue
        if any(_is_within(target, home) for home in canonical_homes):
            matches.add(target.as_posix())
    return sorted(matches)


def _process_inventory(
    proc_root: Path,
    homes: Sequence[Path],
    *,
    process_scope: str,
) -> dict[str, Any]:
    if not proc_root.is_dir():
        return {
            "state": "unknown",
            "source": proc_root.as_posix(),
            "scope": _fact(
                process_scope,
                state="unknown" if process_scope == "unknown" else "known",
                source="operator_argument::process_scope",
                observed=process_scope != "unknown",
                detail="Completeness of this procfs view relative to the host",
            ),
            "processes": [],
            "scanned_pid_count": 0,
            "scan_truncated": False,
            "detail": "procfs root is unavailable",
        }
    processes: list[dict[str, Any]] = []
    try:
        all_directories = sorted(
            (path for path in proc_root.iterdir() if path.name.isdigit()),
            key=lambda item: int(item.name),
        )
    except OSError as exc:
        return {
            "state": "unknown",
            "source": proc_root.as_posix(),
            "scope": _fact(
                process_scope,
                state="unknown" if process_scope == "unknown" else "known",
                source="operator_argument::process_scope",
                observed=process_scope != "unknown",
                detail="Completeness of this procfs view relative to the host",
            ),
            "processes": [],
            "scanned_pid_count": 0,
            "scan_truncated": False,
            "detail": f"procfs inventory failed: {type(exc).__name__}",
        }
    scan_truncated = len(all_directories) > MAX_PROCESSES
    directories = all_directories[:MAX_PROCESSES]
    canonical_homes = [(home, home.resolve(strict=False)) for home in homes]
    for directory in directories:
        if len(processes) >= MAX_PROCESSES:
            break
        try:
            executable = (directory / "exe").resolve(strict=True)
            cmdline_raw = _read_proc_bytes(directory / "cmdline", MAX_PROCESS_CMDLINE_BYTES)
        except (OSError, RuntimeError):
            continue
        if len(cmdline_raw) > MAX_PROCESS_CMDLINE_BYTES:
            continue
        arguments = [
            value.decode("utf-8", errors="replace") for value in cmdline_raw.split(b"\x00") if value
        ]
        role = _process_role(arguments)
        if "codex" not in executable.name.lower() and role == "codex_related":
            continue
        open_sqlite_paths = _open_codex_sqlite_paths(directory, homes)
        owner: str | None = None
        owner_source: str | None = None
        for home, canonical in canonical_homes:
            if _is_within(executable, canonical):
                owner = home.as_posix()
                owner_source = "executable_path"
                break
        if owner is None:
            sqlite_owners = {
                home.as_posix()
                for home, canonical in canonical_homes
                if any(_is_within(Path(path), canonical) for path in open_sqlite_paths)
            }
            if len(sqlite_owners) == 1:
                owner = next(iter(sqlite_owners))
                owner_source = "open_sqlite_path"
        ppid: int | None = None
        try:
            for line in (directory / "status").read_text(encoding="utf-8").splitlines():
                if line.startswith("PPid:"):
                    ppid = int(line.split(":", 1)[1].strip())
                    break
        except (OSError, UnicodeDecodeError, ValueError):
            pass
        processes.append(
            {
                "pid": int(directory.name),
                "ppid": ppid,
                "role": role,
                "executable": executable.as_posix(),
                "version": _version_from_path(executable),
                "home": owner,
                "home_source": owner_source,
                "endpoint": _safe_unix_endpoint(arguments),
                "open_sqlite_paths": open_sqlite_paths,
            }
        )
    return {
        "state": "unknown" if scan_truncated else "known",
        "source": proc_root.as_posix(),
        "scope": _fact(
            process_scope,
            state="unknown" if process_scope == "unknown" else "known",
            source="operator_argument::process_scope",
            observed=process_scope != "unknown",
            detail="Completeness of this procfs view relative to the host",
        ),
        "processes": processes,
        "scanned_pid_count": len(directories),
        "scan_truncated": scan_truncated,
        "detail": (
            "process scan exceeded the safety bound"
            if scan_truncated
            else "sanitized executable, role, ownership, and local endpoint metadata only"
        ),
    }


def _project_snapshot(project: Path) -> dict[str, Any]:
    return {
        "project": project.as_posix(),
        "tracked_hook_guidance": _tracked_hook_guidance(project),
        "hook_definition": _hook_definition(project),
        "client_hook_trust": {
            "state": "unknown",
            "asserted": False,
            "source": "/hooks",
            "detail": (
                "Topology diagnostics never read, copy, or infer client-local exact-hash trust"
            ),
        },
    }


def _trust_for_project(home: Mapping[str, Any], project: Path) -> tuple[str, str | None]:
    config = home.get("config", {})
    rows = config.get("projects", []) if isinstance(config, Mapping) else []
    row = next(
        (
            candidate
            for candidate in rows
            if isinstance(candidate, Mapping) and candidate.get("project") == project.as_posix()
        ),
        None,
    )
    status_value = str(row.get("status")) if isinstance(row, Mapping) else "missing"
    authority = home.get("allowlist_authority", {})
    authority_rows = authority.get("projects", []) if isinstance(authority, Mapping) else []
    authority_row = next(
        (
            candidate
            for candidate in authority_rows
            if isinstance(candidate, Mapping) and candidate.get("project") == project.as_posix()
        ),
        None,
    )
    approved_at = (
        authority_row.get("approved_at")
        if isinstance(authority_row, Mapping) and authority_row.get("authorized") is True
        else None
    )
    return status_value, approved_at if isinstance(approved_at, str) else None


def _thread_diagnostics(
    homes: Sequence[Mapping[str, Any]],
    *,
    canonical_home: Path,
    projects: Sequence[Path],
    thread_ids: Sequence[str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for thread_id in thread_ids:
        owners: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        for home in homes:
            rows = home.get("requested_threads", [])
            row = next(
                (
                    candidate
                    for candidate in rows
                    if isinstance(candidate, Mapping) and candidate.get("thread_id") == thread_id
                ),
                None,
            )
            if isinstance(row, Mapping) and row.get("state") == "valid":
                owners.append((home, row))
        if len(owners) != 1:
            results.append(
                {
                    "thread_id": thread_id,
                    "ownership": "missing" if not owners else "ambiguous",
                    "owner_home": None,
                    "freshness": "unknown",
                    "message": (
                        "Thread ownership is not present in any candidate home"
                        if not owners
                        else "Thread exists in more than one candidate home"
                    ),
                    "hook_execution_asserted": False,
                    "hook_trust_asserted": False,
                }
            )
            continue
        home, metadata = owners[0]
        owner_path = str(home.get("canonical_path"))
        cwd = Path(str(metadata.get("cwd"))).resolve(strict=False)
        project = next(
            (candidate for candidate in projects if cwd == candidate or _is_within(cwd, candidate)),
            None,
        )
        if project is None:
            results.append(
                {
                    "thread_id": thread_id,
                    "ownership": (
                        "canonical" if owner_path == canonical_home.as_posix() else "other_home"
                    ),
                    "owner_home": owner_path,
                    "freshness": "unknown",
                    "message": "Thread CWD does not map to a requested project",
                    "hook_execution_asserted": False,
                    "hook_trust_asserted": False,
                }
            )
            continue
        trust_status, approved_at = _trust_for_project(home, project)
        started = _parse_utc(metadata.get("started_at"))
        approved = _parse_utc(approved_at)
        if (
            trust_status in {"trusted", "trusted_alias"}
            and started is not None
            and approved is not None
        ):
            stale = started < approved
            results.append(
                {
                    "thread_id": thread_id,
                    "ownership": (
                        "canonical" if owner_path == canonical_home.as_posix() else "other_home"
                    ),
                    "owner_home": owner_path,
                    "project": project.as_posix(),
                    "freshness": "stale" if stale else "not_predating_trust",
                    "message": (
                        STALE_THREAD_MESSAGE
                        if stale
                        else "Session started after the durable trust change; hook loading and trust remain unproven."
                    ),
                    "trust_effective_at": approved_at,
                    "thread_started_at": metadata.get("started_at"),
                    "hook_execution_asserted": False,
                    "hook_trust_asserted": False,
                }
            )
        else:
            results.append(
                {
                    "thread_id": thread_id,
                    "ownership": (
                        "canonical" if owner_path == canonical_home.as_posix() else "other_home"
                    ),
                    "owner_home": owner_path,
                    "project": project.as_posix(),
                    "freshness": "unknown",
                    "message": (
                        "Current trust or a durable trust-effective timestamp is unavailable; "
                        "session freshness cannot be proven."
                    ),
                    "trust_effective_at": approved_at,
                    "thread_started_at": metadata.get("started_at"),
                    "hook_execution_asserted": False,
                    "hook_trust_asserted": False,
                }
            )
    return results


def _split_brain_indicators(
    homes: Sequence[Mapping[str, Any]],
    commands: Sequence[Mapping[str, Any]],
    processes: Mapping[str, Any],
    threads: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    indicators: list[dict[str, Any]] = []

    session_owners: set[str] = set()
    for home in homes:
        if any(
            isinstance(store, Mapping)
            and int(store.get("jsonl_count", 0)) > 0
            and store.get("resolved", {}).get("state") == "known"
            for store in home.get("session_stores", [])
        ):
            owner = home.get("canonical_path")
            if isinstance(owner, str):
                session_owners.add(owner)
    if len(session_owners) > 1:
        indicators.append(
            {
                "code": "multiple_session_stores",
                "detail": "more than one Codex home owns session files",
                "evidence": sorted(session_owners),
            }
        )

    sqlite_owners = {
        str(home.get("sqlite", {}).get("effective_home", {}).get("value"))
        for home in homes
        if home.get("sqlite", {}).get("files")
    }
    sqlite_owners.discard("None")
    if len(sqlite_owners) > 1:
        indicators.append(
            {
                "code": "multiple_sqlite_stores",
                "detail": "more than one SQLite home owns Codex state files",
                "evidence": sorted(sqlite_owners),
            }
        )

    sqlite_roots = {
        str(root) for home in homes for root in home.get("sqlite", {}).get("roots_with_state", [])
    }
    if len(sqlite_roots) > 1:
        indicators.append(
            {
                "code": "multiple_sqlite_roots",
                "detail": "Codex SQLite state files exist under more than one root",
                "evidence": sorted(sqlite_roots),
            }
        )

    server_homes = {
        str(process.get("home"))
        for process in processes.get("processes", [])
        if process.get("role") in {"remote_control_server", "app_server"} and process.get("home")
    }
    if len(server_homes) > 1:
        indicators.append(
            {
                "code": "multiple_server_homes",
                "detail": "live app-server processes resolve to different Codex homes",
                "evidence": sorted(server_homes),
            }
        )

    control_socket_homes = {
        str(home.get("canonical_path"))
        for home in homes
        if home.get("lifecycle", {}).get("control_socket", {}).get("kind") == "socket"
    }
    if len(control_socket_homes) > 1:
        indicators.append(
            {
                "code": "multiple_control_sockets",
                "detail": "more than one Codex home exposes an app-server control socket",
                "evidence": sorted(control_socket_homes),
            }
        )

    identities = {
        str(command.get("resolved"))
        for command in commands
        if command.get("executable") and command.get("resolved")
    }
    if len(identities) > 1:
        indicators.append(
            {
                "code": "multiple_executable_identities",
                "detail": "Codex command candidates resolve to different executable identities",
                "evidence": sorted(identities),
            }
        )
    routed_wrappers = [
        str(command.get("path"))
        for command in commands
        if command.get("wrapper", {}).get("home_routing") is True
    ]
    if routed_wrappers:
        indicators.append(
            {
                "code": "context_routed_wrapper",
                "detail": "a Codex wrapper contains context-sensitive CODEX_HOME routing signals",
                "evidence": sorted(routed_wrappers),
            }
        )

    for thread in threads:
        if thread.get("ownership") == "other_home":
            indicators.append(
                {
                    "code": "thread_owned_by_noncanonical_home",
                    "detail": "a requested thread is owned by a non-canonical home",
                    "evidence": [str(thread.get("thread_id")), str(thread.get("owner_home"))],
                }
            )
    return sorted(indicators, key=lambda item: (str(item["code"]), json.dumps(item["evidence"])))


def _status_issues(
    homes: Sequence[Mapping[str, Any]],
    processes: Mapping[str, Any],
    threads: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for home in homes:
        path = str(home.get("path"))
        if not home.get("exists"):
            issues.append({"code": "home_missing", "source": path})
        if home.get("config", {}).get("state") == "invalid":
            issues.append({"code": "config_invalid", "source": f"{path}/config.toml"})
        if home.get("config", {}).get("sqlite_home", {}).get("state") == "invalid":
            issues.append(
                {
                    "code": "sqlite_home_invalid",
                    "source": f"{path}/config.toml::sqlite_home",
                }
            )
        if home.get("allowlist_authority", {}).get("state") == "invalid":
            issues.append({"code": "allowlist_invalid", "source": f"{path}/trusted-projects.toml"})
        sqlite = home.get("sqlite", {})
        if (
            home.get("role") == "canonical"
            and len(sqlite.get("roots_with_state", [])) > 1
            and sqlite.get("selection_explicit", {}).get("value") is not True
        ):
            issues.append(
                {
                    "code": "sqlite_authority_ambiguous",
                    "source": path,
                }
            )
        for thread in home.get("requested_threads", []):
            if thread.get("state") in {"invalid", "ambiguous", "unknown"}:
                issues.append(
                    {
                        "code": "session_metadata_" + str(thread.get("state")),
                        "source": str(thread.get("path") or thread.get("thread_id")),
                    }
                )
    if processes.get("state") != "known":
        issues.append({"code": "process_inventory_unknown", "source": str(processes.get("source"))})
    elif processes.get("scope", {}).get("value") == "unknown":
        issues.append(
            {
                "code": "process_inventory_scope_unknown",
                "source": str(processes.get("source")),
            }
        )
    for thread in threads:
        if thread.get("ownership") in {"missing", "ambiguous"}:
            issues.append(
                {
                    "code": "thread_ownership_" + str(thread.get("ownership")),
                    "source": str(thread.get("thread_id")),
                }
            )
    return sorted(issues, key=lambda item: (item["code"], item["source"]))


def topology_status(
    *,
    canonical_codex_home: str | os.PathLike[str] | None = None,
    canonical_sqlite_home: str | os.PathLike[str] | None = None,
    candidate_codex_homes: Sequence[str | os.PathLike[str]] = (),
    projects: Sequence[str | os.PathLike[str]] = (),
    thread_ids: Sequence[str] = (),
    codex_commands: Sequence[str | os.PathLike[str]] = (),
    proc_root: str | os.PathLike[str] = "/proc",
    process_scope: str = "unknown",
    active_work_state: str = "unknown",
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a bounded, deterministic, side-effect-free Codex topology report."""

    env = dict(os.environ if environment is None else environment)
    if active_work_state not in ACTIVE_WORK_STATES:
        raise CodexTopologyError(
            "active_work_state must be one of: " + ", ".join(sorted(ACTIVE_WORK_STATES))
        )
    if process_scope not in PROCESS_SCOPES:
        raise CodexTopologyError(
            "process_scope must be one of: " + ", ".join(sorted(PROCESS_SCOPES))
        )
    raw_home = canonical_codex_home or env.get("CODEX_HOME", "").strip() or (Path.home() / ".codex")
    canonical_home = _state_root(raw_home, label="canonical CODEX_HOME")
    sqlite_home = (
        _state_root(canonical_sqlite_home, label="canonical CODEX_SQLITE_HOME")
        if canonical_sqlite_home is not None
        else None
    )

    homes_raw: list[Path] = [canonical_home]
    homes_raw.extend(
        _state_root(value, label="candidate CODEX_HOME") for value in candidate_codex_homes
    )
    for key in ("CODEX_HOME", "AEGIS_REMOTE_CONTROL_HOME"):
        value = env.get(key, "").strip()
        if value:
            homes_raw.append(_state_root(value, label=key))
    homes: list[Path] = []
    seen_homes: set[str] = set()
    for home in homes_raw:
        identity = home.resolve(strict=False).as_posix()
        if identity not in seen_homes:
            seen_homes.add(identity)
            homes.append(home)
    homes.sort(key=lambda item: (item.resolve(strict=False) != canonical_home, item.as_posix()))

    canonical_projects = tuple(sorted({_canonical_project(value) for value in projects}))
    checked_thread_ids: list[str] = []
    for thread_id in thread_ids:
        if not THREAD_ID_RE.fullmatch(thread_id):
            raise CodexTopologyError(f"unsafe thread ID: {thread_id!r}")
        if thread_id not in checked_thread_ids:
            checked_thread_ids.append(thread_id)

    home_rows = [
        _home_inventory(
            home,
            canonical_home=canonical_home,
            canonical_sqlite_home=sqlite_home,
            projects=canonical_projects,
            thread_ids=checked_thread_ids,
            environment=env,
        )
        for home in homes
    ]
    command_rows = _command_inventory(
        homes,
        explicit_commands=codex_commands,
        environment=env,
    )
    process_rows = _process_inventory(
        _absolute_path(proc_root),
        homes,
        process_scope=process_scope,
    )
    thread_rows = _thread_diagnostics(
        home_rows,
        canonical_home=canonical_home,
        projects=canonical_projects,
        thread_ids=checked_thread_ids,
    )
    indicators = _split_brain_indicators(
        home_rows,
        command_rows,
        process_rows,
        thread_rows,
    )
    issues = _status_issues(home_rows, process_rows, thread_rows)
    overall = "split_brain" if indicators else "attention_required" if issues else "healthy"
    canonical_sqlite_value = next(
        (
            str(home["sqlite"]["effective_home"]["value"])
            for home in home_rows
            if home.get("role") == "canonical"
            and home.get("sqlite", {}).get("effective_home", {}).get("value")
        ),
        canonical_home.as_posix(),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "codex_topology_status",
        "status": overall,
        "read_only": True,
        "canonical_architecture": {
            "codex_home": canonical_home.as_posix(),
            "codex_sqlite_home": canonical_sqlite_value,
            "home_count": 1,
            "server_count": 1,
            "session_store_count": 1,
            "hook_trust_store_count": 1,
        },
        "active_work": _fact(
            active_work_state,
            state="unknown" if active_work_state == "unknown" else "known",
            source="operator_argument::active_work_state",
            observed=active_work_state != "unknown",
            detail=(
                "Operator-supplied drain state; diagnostics do not infer active work from silence"
            ),
        ),
        "homes": home_rows,
        "commands": command_rows,
        "process_inventory": process_rows,
        "projects": [_project_snapshot(project) for project in canonical_projects],
        "threads": thread_rows,
        "split_brain": {
            "detected": bool(indicators),
            "indicators": indicators,
        },
        "issues": issues,
        "limits": {
            "session_files_per_store": MAX_SESSION_FILES,
            "processes": MAX_PROCESSES,
            "command_candidates": MAX_COMMAND_CANDIDATES,
            "session_metadata_bytes": MAX_SESSION_META_BYTES,
        },
        "security": {
            "selected_nonsecret_config_values_emitted": True,
            "unrequested_config_values_emitted": False,
            "auth_read": False,
            "transcript_text_read": False,
            "hook_trust_store_read": False,
            "hook_trust_asserted": False,
            "process_arguments_emitted": False,
            "lifecycle_contacted": False,
        },
    }


def _migration_blockers(status: Mapping[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    active = status.get("active_work", {}).get("value")
    if active == "unknown":
        blockers.append(
            {
                "code": "active_work_unknown",
                "required_action": "Prove all active child work is drained before Task 257 mutation.",
            }
        )
    elif active == "present":
        blockers.append(
            {
                "code": "active_work_present",
                "required_action": "Finish or safely hand off active child work before Task 257.",
            }
        )

    processes = status.get("process_inventory", {})
    if processes.get("state") != "known":
        blockers.append(
            {
                "code": "process_inventory_unknown",
                "required_action": "Obtain a read-only native process inventory before lifecycle action.",
            }
        )
    elif processes.get("scope", {}).get("value") not in {"host", "fixture"}:
        blockers.append(
            {
                "code": "process_inventory_scope_unknown",
                "required_action": (
                    "Prove the process inventory covers the host namespace before lifecycle action."
                ),
            }
        )
    for process in processes.get("processes", []):
        if process.get("role") in {"remote_control_server", "app_server"} and not process.get(
            "home"
        ):
            blockers.append(
                {
                    "code": "server_owner_unknown",
                    "required_action": (
                        f"Prove the owning CODEX_HOME for server PID {process.get('pid')}."
                    ),
                }
            )

    for issue in status.get("issues", []):
        code = str(issue.get("code"))
        if code in {
            "config_invalid",
            "sqlite_home_invalid",
            "allowlist_invalid",
            "session_metadata_invalid",
            "session_metadata_ambiguous",
            "session_metadata_unknown",
            "thread_ownership_ambiguous",
            "sqlite_authority_ambiguous",
        }:
            blockers.append(
                {
                    "code": code,
                    "required_action": f"Resolve invalid or ambiguous evidence at {issue.get('source')}.",
                }
            )

    canonical = status.get("canonical_architecture", {}).get("codex_home")
    for home in status.get("homes", []):
        if home.get("canonical_path") == canonical:
            continue
        owns_sessions = any(
            int(store.get("jsonl_count", 0)) > 0 for store in home.get("session_stores", [])
        )
        owns_sqlite = bool(home.get("sqlite", {}).get("files"))
        if owns_sessions or owns_sqlite:
            blockers.append(
                {
                    "code": "noncanonical_state_requires_disposition",
                    "required_action": (
                        f"Record preserve, handoff, archive, or retire disposition for {home.get('path')}."
                    ),
                }
            )
    unique = {(blocker["code"], blocker["required_action"]): blocker for blocker in blockers}
    return [unique[key] for key in sorted(unique, key=lambda item: (item[0], item[1]))]


def _phase(
    phase_id: str,
    title: str,
    *,
    mutates_host: bool,
    attended: bool,
    preconditions: Sequence[str],
    actions: Sequence[str],
    verification: Sequence[str],
    rollback: Sequence[str],
) -> dict[str, Any]:
    return {
        "id": phase_id,
        "title": title,
        "task256_execute": False,
        "task257_mutates_host": mutates_host,
        "attended_boundary": attended,
        "preconditions": list(preconditions),
        "actions": list(actions),
        "verification": list(verification),
        "rollback": list(rollback),
    }


def topology_migration_plan(status: Mapping[str, Any]) -> dict[str, Any]:
    """Transform one status payload into the deterministic Task 257 plan."""

    if status.get("schema_version") != SCHEMA_VERSION:
        raise CodexTopologyError("topology status schema_version is unsupported")
    canonical_home = str(status.get("canonical_architecture", {}).get("codex_home"))
    canonical_sqlite = str(status.get("canonical_architecture", {}).get("codex_sqlite_home"))
    blockers = _migration_blockers(status)
    phases = [
        _phase(
            "257.0-preflight",
            "Revalidate topology and freeze authority",
            mutates_host=False,
            attended=True,
            preconditions=[
                "Task 256 is merged and the source tree is clean.",
                "The owner confirms the canonical home and SQLite home.",
            ],
            actions=[
                "Run topology status with every known home, project, and relevant thread.",
                "Record an explicit disposition for every non-canonical session and SQLite store.",
                "Refuse to continue while any migration blocker remains.",
            ],
            verification=[
                "Status has no invalid evidence.",
                "Active work is proven drained.",
                "Server and session ownership are unambiguous.",
            ],
            rollback=["No host mutation has occurred; stop Task 257."],
        ),
        _phase(
            "257.1-snapshot",
            "Capture exact rollback inventory",
            mutates_host=False,
            attended=True,
            preconditions=["Preflight is blocker-free."],
            actions=[
                "Snapshot paths, owners, modes, symlink targets, and byte digests for both homes.",
                "Record process and socket ownership without reading auth or hook trust content.",
                "Store rollback evidence outside both live Codex homes.",
            ],
            verification=[
                "Every planned mutation has an exact pre-change identity.",
                "No secret values or transcript text appear in evidence.",
            ],
            rollback=["Discard the Task 257 plan; no host state has changed."],
        ),
        _phase(
            "257.2-drain",
            "Drain Remote Control and session work",
            mutates_host=False,
            attended=True,
            preconditions=["Rollback inventory is complete."],
            actions=[
                "Prevent new autonomous dispatch without changing hook trust.",
                "Finish, archive, or create an Aegis capsule handoff for every active thread.",
                "Confirm no child work remains in either app-server context.",
            ],
            verification=[
                "A second independent inventory reports active_work=drained.",
                "Every cross-home thread has its approved preservation disposition.",
            ],
            rollback=[
                "Reopen dispatch only if no subsequent lifecycle or state mutation occurred."
            ],
        ),
        _phase(
            "257.3-native-stop",
            "Stop only the proven legacy server through its native owner",
            mutates_host=True,
            attended=True,
            preconditions=[
                "Drain is independently verified.",
                "The legacy server PID, home, socket, client version, and native supervisor agree.",
            ],
            actions=[
                "Invoke native codex remote-control stop in the explicit legacy owner context.",
                "Refuse wrong-home or unmanaged-server diagnostics; never fall back to kill or pkill.",
            ],
            verification=[
                "The exact legacy PID and control socket are gone.",
                "The canonical server and unrelated global or WSL contexts remain unchanged.",
            ],
            rollback=[
                "Restart only the exact previous legacy server through its proven native context.",
                "Stop if ownership cannot be reproduced exactly.",
            ],
        ),
        _phase(
            "257.4-consolidate",
            "Consolidate durable state into the canonical homes",
            mutates_host=True,
            attended=True,
            preconditions=[
                "The legacy server is stopped and canonical state ownership is quiescent.",
                "Every source item has an explicit conflict and rollback rule.",
            ],
            actions=[
                f"Make {canonical_home} the sole CODEX_HOME authority.",
                f"Make {canonical_sqlite} the sole CODEX_SQLITE_HOME authority.",
                "Preserve canonical config, auth, sessions, connectors, skills, packages, and trust.",
                "Import or hand off only owner-approved non-canonical sessions through a supported mechanism.",
                "Do not copy hook trust hashes or synthesize session database rows.",
            ],
            verification=[
                "Canonical config parses and exact unowned bytes are preserved.",
                "Session and SQLite inventories have one owner.",
                "No duplicate auth, trust, or active SQLite authority was created.",
            ],
            rollback=[
                "Restore exact snapshots before restarting any server.",
                "Keep both original homes quarantined and byte-identifiable.",
            ],
        ),
        _phase(
            "257.5-host-routing",
            "Replace CWD routing with one explicit canonical environment",
            mutates_host=True,
            attended=True,
            preconditions=["Canonical durable state verification passes."],
            actions=[
                "Update shell and launcher configuration to one official binary and canonical homes.",
                "Remove dual-home decisions from the wrapper only after the canonical command works directly.",
                "Open a fresh shell and diagnose effective command, home, SQLite home, and version.",
            ],
            verification=[
                "Every project resolves the same official Codex executable and homes.",
                "No stale temporary PATH or alternate-home route remains.",
            ],
            rollback=[
                "Restore exact wrapper and shell snapshots.",
                "Do not edit session, auth, or hook trust state during routing rollback.",
            ],
        ),
        _phase(
            "257.6-native-start",
            "Start one native Remote Control server",
            mutates_host=True,
            attended=True,
            preconditions=["Fresh-shell routing resolves only the canonical context."],
            actions=[
                "Run native codex remote-control start once in the canonical context.",
                "Do not attach with a compatibility client or change the installed current symlink.",
            ],
            verification=[
                "Exactly one native server and one control socket are present.",
                "Server executable, version, CODEX_HOME, and SQLite owner match the canonical plan.",
            ],
            rollback=[
                "Use native stop in the same proven canonical context.",
                "Restore routing before restarting the legacy server if required.",
            ],
        ),
        _phase(
            "257.7-fresh-session-hooks",
            "Re-establish project sessions and attended hook trust",
            mutates_host=False,
            attended=True,
            preconditions=["The canonical server passes native health diagnostics."],
            actions=[
                "Open a fresh project session so trusted project-local config can load.",
                "Use /hooks to review exact definitions and hashes; never bypass or copy trust.",
                "After approval, open a second fresh SessionStart before claiming hook execution.",
            ],
            verification=[
                "Project warning reflects the current on-disk trust generation.",
                "The expected project hook definitions are visible in /hooks.",
                "A post-approval fresh-session hook event exists; approval alone is not execution proof.",
            ],
            rollback=[
                "Disable or decline the project hooks in /hooks.",
                "Keep the server and project trust unchanged while investigating definition drift.",
            ],
        ),
        _phase(
            "257.8-system-verification",
            "Verify one-home behavior across projects",
            mutates_host=False,
            attended=False,
            preconditions=["Canonical fresh-session hook verification passes."],
            actions=[
                "Run topology status, Codex doctor, project strict Aegis checks, resume, fork, and Remote Control smoke.",
                "Confirm ordinary projects route by project path and native trust, not source-repository CWD.",
            ],
            verification=[
                "Topology status is healthy with one home, one SQLite owner, one server, and one executable.",
                "Same-home resume and fork see the expected sessions.",
                "No project needed copied trust, hashes, auth, or session databases.",
            ],
            rollback=[
                "If state integrity fails, stop the canonical server natively and restore exact snapshots.",
                "If only one project fails, preserve the canonical host and roll back that project separately.",
            ],
        ),
        _phase(
            "257.9-observe-and-quarantine",
            "Observe before retiring legacy topology",
            mutates_host=True,
            attended=True,
            preconditions=["System verification passes."],
            actions=[
                "Quarantine the legacy home and wrapper route without deleting them.",
                "Observe ordinary, Remote Control, resume, compaction, and hook-change workflows.",
                "Retire legacy state only in a later reviewed cleanup after the observation window.",
            ],
            verification=[
                "No access to the quarantined home occurs during the observation window.",
                "Rollback artifacts remain complete and readable.",
            ],
            rollback=[
                "Restore the previous route from exact snapshots and restart only its proven native server.",
                "Do not merge trust stores or delete canonical evidence.",
            ],
        ),
    ]
    status_digest = _sha256(
        json.dumps(status, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "codex_topology_plan",
        "status": "blocked" if blockers else "ready_for_task257",
        "read_only": True,
        "source_status_sha256": status_digest,
        "canonical_codex_home": canonical_home,
        "canonical_codex_sqlite_home": canonical_sqlite,
        "blockers": blockers,
        "phases": phases,
        "hard_prohibitions": [
            "Task 256 executes none of these phases.",
            "Never kill or signal a Codex process as lifecycle fallback.",
            "Never copy auth, hook trust hashes, connector secrets, or live SQLite files.",
            "Never claim hook trust without attended /hooks review of exact definitions.",
            "Never touch Blog or begin Gas Town migration as part of Task 256.",
        ],
        "rollback_principle": (
            "Preserve both original homes and exact routing snapshots until the post-cutover "
            "observation window closes."
        ),
    }


__all__ = [
    "ACTIVE_WORK_STATES",
    "CodexTopologyError",
    "PROCESS_SCOPES",
    "SCHEMA_VERSION",
    "STALE_THREAD_MESSAGE",
    "topology_migration_plan",
    "topology_status",
]
