"""Host-scoped Codex Remote Control project-trust management.

Codex project trust belongs to the user configuration under the effective
``CODEX_HOME``.  Aegis Remote Control intentionally runs with a separate home
and a more privileged policy, so trust must be explicit in that context rather
than inherited from an attended Codex session.

This module owns only an Aegis-delimited ``[projects]`` projection in the
Remote Control config.  It never copies Codex hook hashes, never claims client
hook trust, and never lets a project install authorize itself.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import tomllib
from typing import Any, Iterator, Mapping, Sequence

try:  # pragma: no cover - platform selection is exercised on Linux CI.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

try:  # pragma: no cover - Windows fallback is not available on Linux CI.
    import msvcrt
except ImportError:  # pragma: no cover
    msvcrt = None  # type: ignore[assignment]


ALLOWLIST_SCHEMA_VERSION = 1
ALLOWLIST_FILENAME = "trusted-projects.toml"
CONFIG_FILENAME = "config.toml"
LOCK_FILENAME = ".aegis-project-trust.lock"
BACKUP_FILENAME = "config.toml.aegis-last-known-good"
MANAGED_BEGIN = "# AEGIS:BEGIN codex-remote-control-project-trust v1"
MANAGED_END = "# AEGIS:END codex-remote-control-project-trust v1"
DEFAULT_LOCK_TIMEOUT = 5.0
MAX_DIFF_LINES = 200

HOOK_SETTINGS_PATH = ".codex/hooks.json"
HOOK_REVIEW_COMMAND = "/hooks"
HOOK_HASH_SCOPE = "exact_hook_definition"


class RemoteTrustError(RuntimeError):
    """Base failure for host-scoped trust operations."""


class RemoteTrustValidationError(RemoteTrustError):
    """Input or existing host state failed closed validation."""


class RemoteTrustConflictError(RemoteTrustError):
    """Managed trust conflicts with an unowned Codex configuration entry."""


class RemoteTrustLockTimeout(RemoteTrustError):
    """Another bridge mutation retained the host lock beyond the timeout."""


class RemoteTrustRollbackError(RemoteTrustError):
    """Apply failed and the exact last-known-good state could not be restored."""


@dataclasses.dataclass(frozen=True)
class BridgePaths:
    """Resolved host paths for one normal/Remote Control context pair."""

    normal_home: Path
    remote_home: Path
    normal_config: Path
    remote_config: Path
    allowlist: Path
    lock: Path
    backup: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "normal_home": self.normal_home.as_posix(),
            "remote_home": self.remote_home.as_posix(),
            "normal_config": self.normal_config.as_posix(),
            "remote_config": self.remote_config.as_posix(),
            "allowlist": self.allowlist.as_posix(),
            "lock": self.lock.as_posix(),
            "backup": self.backup.as_posix(),
        }


@dataclasses.dataclass(frozen=True, order=True)
class TrustEntry:
    """One explicit operator authorization for the autonomous context."""

    path: str
    approved_by: str
    approved_at: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ConfigPlan:
    """Internal byte-exact plan plus its bounded public representation."""

    before: bytes
    after: bytes
    managed_projects: tuple[str, ...]
    externally_satisfied_projects: tuple[str, ...]
    diff: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return self.before != self.after

    def as_dict(self, paths: BridgePaths) -> dict[str, Any]:
        return {
            "status": "would_apply" if self.changed else "current",
            "changed": self.changed,
            "paths": paths.as_dict(),
            "before_sha256": _sha256(self.before),
            "after_sha256": _sha256(self.after),
            "managed_projects": list(self.managed_projects),
            "externally_satisfied_projects": list(self.externally_satisfied_projects),
            "diff": list(self.diff),
            "diff_truncated": len(self.diff) >= MAX_DIFF_LINES,
        }


def _absolute_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve(strict=False)


def resolve_bridge_paths(
    *,
    normal_codex_home: str | os.PathLike[str] | None = None,
    remote_codex_home: str | os.PathLike[str] | None = None,
    source_root: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> BridgePaths:
    """Resolve separate normal and autonomous homes without silently merging them."""

    env = dict(os.environ if environment is None else environment)
    active_home_raw = env.get("CODEX_HOME", "").strip()
    active_home = _absolute_path(active_home_raw) if active_home_raw else None

    if normal_codex_home is not None:
        normal_home = _absolute_path(normal_codex_home)
    elif env.get("CODEX_GLOBAL_DIR", "").strip():
        normal_home = _absolute_path(env["CODEX_GLOBAL_DIR"])
    elif active_home is not None and active_home.name != "remote-control":
        normal_home = active_home
    else:
        normal_home = (Path.home() / ".codex").resolve(strict=False)

    if remote_codex_home is not None:
        remote_home = _absolute_path(remote_codex_home)
    elif env.get("AEGIS_REMOTE_CONTROL_HOME", "").strip():
        remote_home = _absolute_path(env["AEGIS_REMOTE_CONTROL_HOME"])
    elif active_home is not None and active_home.name == "remote-control":
        remote_home = active_home
    elif source_root is not None:
        candidate = _absolute_path(source_root) / ".codex" / "remote-control"
        if not candidate.is_dir():
            raise RemoteTrustValidationError(
                "Remote Control home is not discoverable from the Aegis source root; "
                "pass --remote-codex-home or set AEGIS_REMOTE_CONTROL_HOME"
            )
        remote_home = candidate.resolve(strict=False)
    else:
        raise RemoteTrustValidationError(
            "Remote Control home is not discoverable; pass --remote-codex-home or set "
            "AEGIS_REMOTE_CONTROL_HOME"
        )

    if normal_home == remote_home:
        raise RemoteTrustValidationError(
            "normal and Remote Control CODEX_HOME values must remain separate"
        )

    return BridgePaths(
        normal_home=normal_home,
        remote_home=remote_home,
        normal_config=normal_home / CONFIG_FILENAME,
        remote_config=remote_home / CONFIG_FILENAME,
        allowlist=remote_home / ALLOWLIST_FILENAME,
        lock=remote_home / LOCK_FILENAME,
        backup=remote_home / BACKUP_FILENAME,
    )


def canonical_project_path(value: str | os.PathLike[str], *, require_exists: bool = True) -> Path:
    """Return one absolute canonical project identity or fail closed."""

    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raise RemoteTrustValidationError("project path must be absolute")
    try:
        canonical = raw.resolve(strict=require_exists)
    except (FileNotFoundError, OSError) as exc:
        raise RemoteTrustValidationError(f"project path cannot be resolved: {raw}") from exc
    if require_exists and not canonical.is_dir():
        raise RemoteTrustValidationError(f"project path is not a directory: {canonical}")
    if canonical == Path(canonical.anchor):
        raise RemoteTrustValidationError("filesystem root cannot be trusted as a project")
    return canonical


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _utc_timestamp(now: dt.datetime | None = None) -> str:
    value = now or dt.datetime.now(dt.timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.timezone.utc)
    value = value.astimezone(dt.timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def _validate_timestamp(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RemoteTrustValidationError(f"{field} must be a non-empty UTC timestamp")
    normalized = value.strip()
    try:
        parsed = dt.datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RemoteTrustValidationError(f"{field} is not a valid ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise RemoteTrustValidationError(f"{field} must include a timezone")
    if parsed.utcoffset() != dt.timedelta(0):
        raise RemoteTrustValidationError(f"{field} must use UTC")
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_toml(content: bytes, *, label: str) -> dict[str, Any]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RemoteTrustValidationError(f"{label} is not valid UTF-8") from exc
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise RemoteTrustValidationError(f"{label} is malformed TOML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RemoteTrustValidationError(f"{label} must contain a TOML table")
    return parsed


def _read_regular_file(path: Path, *, label: str) -> bytes:
    if path.is_symlink():
        raise RemoteTrustValidationError(f"{label} must not be a symlink: {path}")
    if not path.is_file():
        raise RemoteTrustValidationError(f"{label} does not exist: {path}")
    return path.read_bytes()


def _entry_from_mapping(raw: Mapping[str, Any], *, index: int) -> TrustEntry:
    allowed = {"path", "approved_by", "approved_at", "reason"}
    unknown = sorted(set(raw) - allowed)
    missing = sorted(allowed - set(raw))
    if unknown or missing:
        raise RemoteTrustValidationError(
            f"allowlist project {index} fields are invalid; missing={missing}, unknown={unknown}"
        )
    path_value = raw.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise RemoteTrustValidationError(f"allowlist project {index} path must be non-empty")
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        raise RemoteTrustValidationError(f"allowlist project {index} path must be absolute")
    approved_by = raw.get("approved_by")
    reason = raw.get("reason")
    if not isinstance(approved_by, str) or not approved_by.strip():
        raise RemoteTrustValidationError(f"allowlist project {index} approved_by must be non-empty")
    if not isinstance(reason, str) or not reason.strip():
        raise RemoteTrustValidationError(f"allowlist project {index} reason must be non-empty")
    return TrustEntry(
        path=path.as_posix(),
        approved_by=approved_by.strip(),
        approved_at=_validate_timestamp(
            raw.get("approved_at"), field=f"allowlist project {index} approved_at"
        ),
        reason=reason.strip(),
    )


def load_allowlist(
    path: Path,
    *,
    allow_missing: bool = False,
    require_existing_projects: bool = False,
) -> tuple[TrustEntry, ...]:
    """Load and fail-closed validate one durable Remote Control allowlist."""

    if not path.exists() and not path.is_symlink():
        if allow_missing:
            return ()
        raise RemoteTrustValidationError(f"Remote Control allowlist does not exist: {path}")
    content = _read_regular_file(path, label="Remote Control allowlist")
    if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise RemoteTrustValidationError(
            f"Remote Control allowlist permissions must be 0600: {path}"
        )
    parsed = _parse_toml(content, label="Remote Control allowlist")
    allowed_top = {"schema_version", "projects"}
    unknown_top = sorted(set(parsed) - allowed_top)
    if unknown_top:
        raise RemoteTrustValidationError(f"allowlist has unsupported keys: {unknown_top}")
    if parsed.get("schema_version") != ALLOWLIST_SCHEMA_VERSION:
        raise RemoteTrustValidationError(
            f"allowlist schema_version must be {ALLOWLIST_SCHEMA_VERSION}"
        )
    raw_projects = parsed.get("projects")
    if not isinstance(raw_projects, list):
        raise RemoteTrustValidationError("allowlist projects must be an array of tables")

    entries = tuple(
        _entry_from_mapping(raw, index=index)
        for index, raw in enumerate(raw_projects, start=1)
        if isinstance(raw, Mapping)
    )
    if len(entries) != len(raw_projects):
        raise RemoteTrustValidationError("every allowlist project must be a TOML table")

    identities: dict[Path, str] = {}
    lexical: set[str] = set()
    for entry in entries:
        if entry.path in lexical:
            raise RemoteTrustValidationError(f"duplicate allowlist path: {entry.path}")
        lexical.add(entry.path)
        candidate = canonical_project_path(
            entry.path,
            require_exists=require_existing_projects,
        )
        if require_existing_projects and candidate.as_posix() != entry.path:
            raise RemoteTrustValidationError(
                "allowlist paths must be stored canonically; "
                f"configured={entry.path}, canonical={candidate.as_posix()}"
            )
        prior = identities.get(candidate)
        if prior is not None:
            raise RemoteTrustValidationError(
                f"allowlist paths resolve to the same project: {prior} and {entry.path}"
            )
        identities[candidate] = entry.path
    return tuple(sorted(entries, key=lambda entry: entry.path))


def render_allowlist(entries: Sequence[TrustEntry]) -> bytes:
    """Render a deterministic, minimal TOML allowlist."""

    lines = [f"schema_version = {ALLOWLIST_SCHEMA_VERSION}", ""]
    if not entries:
        lines.append("projects = []")
    for entry in sorted(entries, key=lambda item: item.path):
        lines.extend(
            [
                "[[projects]]",
                f"path = {_toml_string(entry.path)}",
                f"approved_by = {_toml_string(entry.approved_by)}",
                f"approved_at = {_toml_string(entry.approved_at)}",
                f"reason = {_toml_string(entry.reason)}",
                "",
            ]
        )
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _strip_managed_block(text: str) -> tuple[str, bool]:
    lines = text.splitlines(keepends=True)
    begin = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == MANAGED_BEGIN]
    end = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == MANAGED_END]
    if not begin and not end:
        return text, False
    if len(begin) != 1 or len(end) != 1 or begin[0] >= end[0]:
        raise RemoteTrustValidationError(
            "Remote Control config has malformed or duplicate Aegis trust markers"
        )
    return "".join(lines[: begin[0]] + lines[end[0] + 1 :]), True


def _projects_table(config: Mapping[str, Any], *, label: str) -> Mapping[str, Any]:
    projects = config.get("projects", {})
    if not isinstance(projects, Mapping):
        raise RemoteTrustValidationError(f"{label} [projects] must be a table")
    return projects


def _existing_project_identity(path_text: str) -> Path | None:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        return None
    try:
        return path.resolve(strict=False)
    except OSError:
        return None


def _render_managed_block(paths: Sequence[str]) -> str:
    if not paths:
        return ""
    lines = [MANAGED_BEGIN]
    for project in sorted(paths):
        lines.extend(
            [
                f"[projects.{_toml_string(project)}]",
                'trust_level = "trusted"',
                "",
            ]
        )
    lines.append(MANAGED_END)
    return "\n".join(lines) + "\n"


def _bounded_diff(before: str, after: str) -> tuple[str, ...]:
    lines = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="config.toml.before",
            tofile="config.toml.after",
            lineterm="",
        )
    )
    return tuple(lines[:MAX_DIFF_LINES])


def build_config_plan(paths: BridgePaths, entries: Sequence[TrustEntry]) -> ConfigPlan:
    """Build a byte-preserving managed projection without writing host state."""

    before = _read_regular_file(paths.remote_config, label="Remote Control config")
    parsed_before = _parse_toml(before, label="Remote Control config")
    del parsed_before
    before_text = before.decode("utf-8")
    base_text, _ = _strip_managed_block(before_text)
    base_bytes = base_text.encode("utf-8")
    base_config = _parse_toml(base_bytes, label="unmanaged Remote Control config")
    base_projects = _projects_table(base_config, label="unmanaged Remote Control config")

    managed: list[str] = []
    external: list[str] = []
    existing_identities: dict[Path, str] = {}
    for configured_path in base_projects:
        if not isinstance(configured_path, str):
            raise RemoteTrustValidationError("Remote Control project keys must be strings")
        identity = _existing_project_identity(configured_path)
        if identity is not None:
            existing_identities[identity] = configured_path

    for entry in sorted(entries, key=lambda item: item.path):
        canonical = canonical_project_path(entry.path, require_exists=True)
        exact = base_projects.get(entry.path)
        alias = existing_identities.get(canonical)
        if exact is not None:
            if not isinstance(exact, Mapping) or exact.get("trust_level") != "trusted":
                raise RemoteTrustConflictError(
                    f"unmanaged project entry conflicts with requested trust: {entry.path}"
                )
            external.append(entry.path)
            continue
        if alias is not None and alias != entry.path:
            raise RemoteTrustConflictError(
                f"unmanaged project path aliases requested trust: {alias} -> {entry.path}"
            )
        managed.append(entry.path)

    rendered = base_text
    block = _render_managed_block(managed)
    if block:
        if rendered and not rendered.endswith("\n"):
            rendered += "\n"
        rendered += block
    after = rendered.encode("utf-8")
    parsed_after = _parse_toml(after, label="proposed Remote Control config")
    projects_after = _projects_table(parsed_after, label="proposed Remote Control config")
    for entry in entries:
        value = projects_after.get(entry.path)
        if not isinstance(value, Mapping) or value.get("trust_level") != "trusted":
            raise RemoteTrustValidationError(
                f"proposed config does not preserve exact trusted state for {entry.path}"
            )

    return ConfigPlan(
        before=before,
        after=after,
        managed_projects=tuple(managed),
        externally_satisfied_projects=tuple(external),
        diff=_bounded_diff(before_text, rendered),
    )


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    if path.is_symlink():
        raise RemoteTrustValidationError(f"refusing to replace symlinked host state: {path}")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
        raise


def _lock_file(descriptor: int, *, blocking: bool) -> None:
    if fcntl is not None:
        operation = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        fcntl.flock(descriptor, operation)
        return
    if msvcrt is not None:  # pragma: no cover
        mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, mode, 1)
        return
    raise RemoteTrustError("host platform does not provide a supported file lock")


def _unlock_file(descriptor: int) -> None:
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    elif msvcrt is not None:  # pragma: no cover
        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def bridge_lock(path: Path, *, timeout: float = DEFAULT_LOCK_TIMEOUT) -> Iterator[None]:
    """Acquire a bounded exclusive host lock without deleting the lock inode."""

    if timeout < 0:
        raise RemoteTrustValidationError("lock timeout must be non-negative")
    if path.is_symlink():
        raise RemoteTrustValidationError(f"lock path must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RemoteTrustValidationError(f"cannot safely open trust lock: {path}") from exc
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise RemoteTrustValidationError(f"trust lock must be a regular file: {path}")
    os.fchmod(descriptor, 0o600)
    deadline = time.monotonic() + timeout
    while True:
        try:
            _lock_file(descriptor, blocking=False)
            break
        except (BlockingIOError, OSError):
            if time.monotonic() >= deadline:
                os.close(descriptor)
                raise RemoteTrustLockTimeout(
                    f"timed out waiting for Remote Control trust lock: {path}"
                )
            time.sleep(0.05)
    try:
        yield
    finally:
        _unlock_file(descriptor)
        os.close(descriptor)


def _file_mode(path: Path, *, default: int = 0o600) -> int:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return default


def _restore_snapshot(path: Path, existed: bool, content: bytes, mode: int) -> None:
    if existed:
        _atomic_write(path, content, mode=mode)
    else:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        _fsync_directory(path.parent)


def _verify_snapshot(path: Path, existed: bool, content: bytes) -> None:
    if existed:
        restored = _read_regular_file(path, label=f"restored host state {path}")
        if restored != content:
            raise RemoteTrustValidationError(f"restored host state differs from snapshot: {path}")
    elif path.exists() or path.is_symlink():
        raise RemoteTrustValidationError(f"host state should have been removed by rollback: {path}")


def _validate_config_file(path: Path, entries: Sequence[TrustEntry]) -> None:
    parsed = _parse_toml(
        _read_regular_file(path, label="written Remote Control config"),
        label="written Remote Control config",
    )
    projects = _projects_table(parsed, label="written Remote Control config")
    for entry in entries:
        value = projects.get(entry.path)
        if not isinstance(value, Mapping) or value.get("trust_level") != "trusted":
            raise RemoteTrustValidationError(
                f"written config lost requested project trust: {entry.path}"
            )


def bridge_plan(paths: BridgePaths) -> dict[str, Any]:
    entries = load_allowlist(paths.allowlist, require_existing_projects=True)
    plan = build_config_plan(paths, entries)
    payload = plan.as_dict(paths)
    payload["allowlist"] = {
        "schema_version": ALLOWLIST_SCHEMA_VERSION,
        "project_count": len(entries),
        "projects": [entry.as_dict() for entry in entries],
    }
    return payload


def _apply_config_plan_locked(
    paths: BridgePaths,
    entries: Sequence[TrustEntry],
    plan: ConfigPlan,
) -> dict[str, Any]:
    payload = plan.as_dict(paths)
    if not plan.changed:
        payload["status"] = "current"
        payload["rollback"] = {"required": False, "performed": False}
        return payload

    config_mode = _file_mode(paths.remote_config)
    _atomic_write(paths.backup, plan.before, mode=0o600)
    try:
        _atomic_write(paths.remote_config, plan.after, mode=config_mode)
        _validate_config_file(paths.remote_config, entries)
    except Exception as exc:
        try:
            _atomic_write(paths.remote_config, plan.before, mode=config_mode)
            _verify_snapshot(paths.remote_config, True, plan.before)
            _parse_toml(plan.before, label="restored Remote Control config")
        except Exception as rollback_exc:
            raise RemoteTrustRollbackError(
                "Remote Control config apply failed and rollback failed; "
                f"apply_error={exc}; rollback_error={rollback_exc}; backup={paths.backup}"
            ) from rollback_exc
        raise RemoteTrustError(
            f"Remote Control config apply failed and was rolled back: {exc}"
        ) from exc

    payload["status"] = "applied"
    payload["rollback"] = {
        "required": True,
        "performed": False,
        "last_known_good": paths.backup.as_posix(),
        "last_known_good_sha256": _sha256(plan.before),
    }
    return payload


def bridge_apply(paths: BridgePaths, *, timeout: float = DEFAULT_LOCK_TIMEOUT) -> dict[str, Any]:
    with bridge_lock(paths.lock, timeout=timeout):
        entries = load_allowlist(paths.allowlist, require_existing_projects=True)
        plan = build_config_plan(paths, entries)
        return _apply_config_plan_locked(paths, entries, plan)


def _prospective_add(
    entries: Sequence[TrustEntry],
    *,
    project: Path,
    approved_by: str,
    approved_at: str,
    reason: str,
) -> tuple[TrustEntry, ...]:
    if not approved_by.strip():
        raise RemoteTrustValidationError("approved_by must be non-empty")
    if not reason.strip():
        raise RemoteTrustValidationError("reason must be non-empty")
    canonical = canonical_project_path(project, require_exists=True).as_posix()
    for entry in entries:
        entry_identity = canonical_project_path(entry.path, require_exists=False)
        if entry_identity == Path(canonical):
            if entry.path != canonical:
                raise RemoteTrustValidationError(
                    f"existing allowlist path aliases requested project: {entry.path}"
                )
            return tuple(entries)
    return tuple(
        sorted(
            [
                *entries,
                TrustEntry(
                    path=canonical,
                    approved_by=approved_by.strip(),
                    approved_at=_validate_timestamp(approved_at, field="approved_at"),
                    reason=reason.strip(),
                ),
            ],
            key=lambda entry: entry.path,
        )
    )


def _prospective_remove(entries: Sequence[TrustEntry], *, project: Path) -> tuple[TrustEntry, ...]:
    lexical = project.expanduser()
    if not lexical.is_absolute():
        raise RemoteTrustValidationError("project path must be absolute")
    canonical = lexical.resolve(strict=False)
    remaining: list[TrustEntry] = []
    matched = False
    for entry in entries:
        entry_path = Path(entry.path).resolve(strict=False)
        if entry.path == lexical.as_posix() or entry_path == canonical:
            matched = True
            continue
        remaining.append(entry)
    if not matched:
        raise RemoteTrustValidationError(
            f"project is not in the Remote Control allowlist: {project}"
        )
    return tuple(remaining)


def _trust_change_preview(
    paths: BridgePaths,
    *,
    action: str,
    project: Path,
    approved_by: str,
    approved_at: str,
    reason: str,
) -> tuple[tuple[TrustEntry, ...], tuple[TrustEntry, ...], bytes, ConfigPlan]:
    allow_missing = action == "add"
    current = load_allowlist(paths.allowlist, allow_missing=allow_missing)
    if action == "add":
        proposed = _prospective_add(
            current,
            project=project,
            approved_by=approved_by,
            approved_at=approved_at,
            reason=reason,
        )
    elif action == "remove":
        if not reason.strip():
            raise RemoteTrustValidationError("reason must be non-empty")
        proposed = _prospective_remove(current, project=project)
    else:
        raise RemoteTrustValidationError(f"unsupported trust action: {action}")
    proposed_bytes = render_allowlist(proposed)
    plan = build_config_plan(paths, proposed)
    return current, proposed, proposed_bytes, plan


def trust_change(
    paths: BridgePaths,
    *,
    action: str,
    project: str | os.PathLike[str],
    reason: str,
    approved_by: str,
    apply: bool,
    approved_at: str | None = None,
    timeout: float = DEFAULT_LOCK_TIMEOUT,
) -> dict[str, Any]:
    """Preview or transactionally apply one explicit allowlist change."""

    project_path = Path(project)
    timestamp = approved_at or _utc_timestamp()

    def build_payload(
        current: Sequence[TrustEntry],
        proposed: Sequence[TrustEntry],
        proposed_bytes: bytes,
        plan: ConfigPlan,
    ) -> dict[str, Any]:
        existing_bytes = paths.allowlist.read_bytes() if paths.allowlist.is_file() else b""
        allowlist_changed = existing_bytes != proposed_bytes
        payload = plan.as_dict(paths)
        payload.update(
            {
                "operation": f"trust_{action}",
                "status": (
                    "would_apply"
                    if not apply and (allowlist_changed or plan.changed)
                    else (
                        "current"
                        if not allowlist_changed and not plan.changed
                        else payload["status"]
                    )
                ),
                "project": _absolute_path(project_path).as_posix(),
                "reason": reason.strip(),
                "allowlist_changed": allowlist_changed,
                "allowlist_before_count": len(current),
                "allowlist_after_count": len(proposed),
                "allowlist_before_sha256": _sha256(existing_bytes),
                "allowlist_after_sha256": _sha256(proposed_bytes),
                "apply_requested": apply,
            }
        )
        return payload

    if not apply:
        current, proposed, proposed_bytes, plan = _trust_change_preview(
            paths,
            action=action,
            project=project_path,
            approved_by=approved_by,
            approved_at=timestamp,
            reason=reason,
        )
        return build_payload(current, proposed, proposed_bytes, plan)

    with bridge_lock(paths.lock, timeout=timeout):
        current, proposed, proposed_bytes, plan = _trust_change_preview(
            paths,
            action=action,
            project=project_path,
            approved_by=approved_by,
            approved_at=timestamp,
            reason=reason,
        )
        payload = build_payload(current, proposed, proposed_bytes, plan)
        old_allowlist_exists = paths.allowlist.is_file()
        old_allowlist = paths.allowlist.read_bytes() if old_allowlist_exists else b""
        old_allowlist_mode = _file_mode(paths.allowlist)
        old_config = plan.before
        old_config_mode = _file_mode(paths.remote_config)
        allowlist_changed = old_allowlist != proposed_bytes
        if not allowlist_changed and not plan.changed:
            payload["status"] = "current"
            payload["rollback"] = {"required": False, "performed": False}
            return payload

        if plan.changed:
            _atomic_write(paths.backup, old_config, mode=0o600)
        try:
            if allowlist_changed:
                _atomic_write(paths.allowlist, proposed_bytes, mode=0o600)
            if plan.changed:
                _atomic_write(paths.remote_config, plan.after, mode=old_config_mode)
            loaded = load_allowlist(paths.allowlist, require_existing_projects=True)
            if loaded != proposed:
                raise RemoteTrustValidationError("written allowlist does not match proposed state")
            _validate_config_file(paths.remote_config, proposed)
        except Exception as exc:
            rollback_errors: list[str] = []
            try:
                _restore_snapshot(
                    paths.allowlist,
                    old_allowlist_exists,
                    old_allowlist,
                    old_allowlist_mode,
                )
                _verify_snapshot(
                    paths.allowlist,
                    old_allowlist_exists,
                    old_allowlist,
                )
            except Exception as rollback_exc:  # noqa: BLE001 - terminal evidence needs both.
                rollback_errors.append(f"allowlist={rollback_exc}")
            try:
                _atomic_write(paths.remote_config, old_config, mode=old_config_mode)
                _verify_snapshot(paths.remote_config, True, old_config)
                _parse_toml(old_config, label="restored Remote Control config")
            except Exception as rollback_exc:  # noqa: BLE001
                rollback_errors.append(f"config={rollback_exc}")
            if rollback_errors:
                raise RemoteTrustRollbackError(
                    "trust transaction failed and rollback was incomplete; "
                    f"apply_error={exc}; rollback_errors={rollback_errors}; backup={paths.backup}"
                ) from exc
            raise RemoteTrustError(f"trust transaction failed and was rolled back: {exc}") from exc

        payload["status"] = "applied"
        payload["rollback"] = {
            "required": True,
            "performed": False,
            "last_known_good": paths.backup.as_posix() if plan.changed else None,
        }
        return payload


def _config_trust(config_path: Path, project: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {"status": "missing_config", "configured_path": None}
    try:
        parsed = _parse_toml(
            _read_regular_file(config_path, label=f"Codex config {config_path}"),
            label=f"Codex config {config_path}",
        )
        projects = _projects_table(parsed, label=f"Codex config {config_path}")
    except RemoteTrustError as exc:
        return {"status": "malformed_config", "configured_path": None, "error": str(exc)}
    exact = projects.get(project.as_posix())
    if exact is not None:
        trust = exact.get("trust_level") if isinstance(exact, Mapping) else None
        return {"status": trust or "malformed", "configured_path": project.as_posix()}
    for configured_path, value in projects.items():
        if not isinstance(configured_path, str):
            continue
        identity = _existing_project_identity(configured_path)
        if identity == project:
            trust = value.get("trust_level") if isinstance(value, Mapping) else None
            return {
                "status": f"{trust or 'malformed'}_alias",
                "configured_path": configured_path,
            }
    return {"status": "missing", "configured_path": None}


def _tracked_hook_guidance(project: Path) -> dict[str, Any]:
    manifest_path = project / ".aegis" / "foundation-manifest.json"
    if not manifest_path.is_file():
        return {"present": False, "valid": False, "path": manifest_path.as_posix()}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "present": True,
            "valid": False,
            "path": manifest_path.as_posix(),
            "error": str(exc),
        }
    gates = manifest.get("gates") if isinstance(manifest, Mapping) else None
    matching = (
        [
            gate
            for gate in gates
            if isinstance(gate, Mapping) and gate.get("id") == "codex.hook_trust"
        ]
        if isinstance(gates, list)
        else []
    )
    gate = matching[0] if len(matching) == 1 else {}
    valid = bool(
        gate.get("settings_path") == HOOK_SETTINGS_PATH
        and gate.get("review_command") == HOOK_REVIEW_COMMAND
        and gate.get("hash_scope") == HOOK_HASH_SCOPE
        and gate.get("bypass_allowed") is False
    )
    return {
        "present": True,
        "valid": valid,
        "path": manifest_path.as_posix(),
        "settings_path": gate.get("settings_path"),
        "review_command": gate.get("review_command"),
        "hash_scope": gate.get("hash_scope"),
        "bypass_allowed": gate.get("bypass_allowed"),
        "matching_gate_count": len(matching),
    }


def _client_hook_records(config_path: Path, project: Path) -> dict[str, Any]:
    hooks_path = project / HOOK_SETTINGS_PATH
    definition_present = hooks_path.is_file() and not hooks_path.is_symlink()
    definition_error = "hook definition must not be a symlink" if hooks_path.is_symlink() else None
    digest = _sha256(hooks_path.read_bytes()) if definition_present else None
    records: list[str] = []
    if config_path.is_file():
        try:
            parsed = _parse_toml(
                _read_regular_file(config_path, label="Remote Control config"),
                label="Remote Control config",
            )
            hooks = parsed.get("hooks")
            state = hooks.get("state") if isinstance(hooks, Mapping) else None
            prefix = hooks_path.as_posix() + ":"
            if isinstance(state, Mapping):
                records = sorted(str(key) for key in state if str(key).startswith(prefix))
        except RemoteTrustError:
            records = []
    return {
        "settings_path": hooks_path.as_posix(),
        "definition_present": definition_present,
        "definition_error": definition_error,
        "definition_sha256": digest,
        "client_hash_record_count": len(records),
        "client_hash_record_ids": records[:10],
        "client_hash_record_ids_truncated": len(records) > 10,
        "client_trust_asserted": False,
        "review_command": HOOK_REVIEW_COMMAND,
        "review_required": definition_present,
        "reason": (
            "Aegis cannot assert Codex client trust; reconnect and review exact definitions with /hooks"
            if definition_present
            else (
                "project hook definition is invalid because it is symlinked"
                if hooks_path.is_symlink()
                else "project has no .codex/hooks.json definition"
            )
        ),
    }


def project_status(
    paths: BridgePaths,
    *,
    project: str | os.PathLike[str],
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    canonical = canonical_project_path(project, require_exists=True)
    allowlist_error: str | None = None
    try:
        entries = load_allowlist(paths.allowlist, allow_missing=True)
    except RemoteTrustError as exc:
        entries = ()
        allowlist_error = str(exc)
    allowlisted = any(
        canonical_project_path(entry.path, require_exists=False) == canonical for entry in entries
    )
    normal = _config_trust(paths.normal_config, canonical)
    remote = _config_trust(paths.remote_config, canonical)
    env = dict(os.environ if environment is None else environment)
    active_home_raw = env.get("CODEX_HOME", "").strip()
    active_home = _absolute_path(active_home_raw).as_posix() if active_home_raw else None
    remote_trusted = remote["status"] in {"trusted", "trusted_alias"}
    project_trust_status = "ready" if allowlisted and remote_trusted else "attention_required"
    hook_state = _client_hook_records(paths.remote_config, canonical)
    next_actions: list[str] = []
    if not allowlisted:
        next_actions.append(
            "Add the canonical project to the explicit Remote Control allowlist and apply the bridge plan"
        )
    elif not remote_trusted:
        next_actions.append("Apply the Remote Control bridge plan")
    else:
        next_actions.append("Reconnect the project session so project-local configuration can load")
    if hook_state["review_required"]:
        next_actions.append(
            "Open /hooks, review the exact project hook definitions and hashes, and approve them explicitly"
        )
    return {
        "status": (
            "hook_review_required"
            if project_trust_status == "ready" and hook_state["review_required"]
            else project_trust_status
        ),
        "project_trust_status": project_trust_status,
        "project": canonical.as_posix(),
        "paths": paths.as_dict(),
        "effective_context": {
            "active_CODEX_HOME": active_home,
            "normal_home_active": active_home == paths.normal_home.as_posix(),
            "remote_home_active": active_home == paths.remote_home.as_posix(),
            "homes_separate": paths.normal_home != paths.remote_home,
        },
        "normal_project_trust": normal,
        "remote_allowlist": {
            "status": "present" if allowlisted else "missing",
            "error": allowlist_error,
        },
        "remote_effective_project_trust": remote,
        "project_local_config_eligible": remote_trusted,
        "tracked_hook_guidance": _tracked_hook_guidance(canonical),
        "client_hook_state": hook_state,
        "next_actions": next_actions,
    }


def bridge_status(
    paths: BridgePaths,
    *,
    project: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Report bridge state without creating locks, files, or generated output."""

    payload: dict[str, Any] = {
        "status": "uninitialized",
        "paths": paths.as_dict(),
        "remote_home_exists": paths.remote_home.is_dir(),
        "normal_config_exists": paths.normal_config.is_file(),
        "remote_config_exists": paths.remote_config.is_file(),
        "allowlist_exists": paths.allowlist.is_file(),
        "backup_exists": paths.backup.is_file(),
    }
    try:
        plan = bridge_plan(paths)
    except RemoteTrustError as exc:
        payload["error"] = str(exc)
    else:
        payload["status"] = "drifted" if plan["changed"] else "current"
        payload["plan"] = plan
    if project is not None:
        payload["project_status"] = project_status(
            paths,
            project=project,
            environment=environment,
        )
        if (
            payload["project_status"]["status"] == "hook_review_required"
            and payload["status"] == "current"
        ):
            payload["status"] = "hook_review_required"
        elif (
            payload["project_status"]["project_trust_status"] != "ready"
            and payload["status"] == "current"
        ):
            payload["status"] = "attention_required"
    return payload


__all__ = [
    "ALLOWLIST_FILENAME",
    "BACKUP_FILENAME",
    "BridgePaths",
    "CONFIG_FILENAME",
    "DEFAULT_LOCK_TIMEOUT",
    "LOCK_FILENAME",
    "MANAGED_BEGIN",
    "MANAGED_END",
    "RemoteTrustConflictError",
    "RemoteTrustError",
    "RemoteTrustLockTimeout",
    "RemoteTrustRollbackError",
    "RemoteTrustValidationError",
    "TrustEntry",
    "bridge_apply",
    "bridge_lock",
    "bridge_plan",
    "bridge_status",
    "build_config_plan",
    "canonical_project_path",
    "load_allowlist",
    "project_status",
    "render_allowlist",
    "resolve_bridge_paths",
    "trust_change",
]
