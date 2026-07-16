"""Production authority lifecycle for the shared Gas City control plane.

The lower-level :mod:`aegis_foundation.task_authority` module deliberately
knows nothing about deployment evidence.  This module is the operator-facing
layer that binds its receipts to reverified Taskmaster, migration, recovery,
and stopped-worker evidence.

Every transition writes an append-only intent before changing the live
receipt and an append-only generation record afterwards.  If the process dies
after the receipt commits, the intent is sufficient to restore the missing
history record without replaying or guessing the transition.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Any

from aegis_foundation import gas_city_ops, task_authority, taskmaster_beads

GENERATION_SCHEMA = "gas-city-task-authority-generation/v1"
ATTEMPT_SCHEMA = "gas-city-task-authority-attempt/v1"
MIGRATION_EVIDENCE_SCHEMA = "taskmaster-beads-migration-evidence/v1"
MIGRATION_RUN_SCHEMA = taskmaster_beads.MIGRATION_RUN_SCHEMA
STOPPED_WORKERS_KIND = "gas-city-workers-stopped"
RECOVERY_KIND = "dolt-native-restore-drill"
MAX_JSON_BYTES = 16 * 1024 * 1024
STOPPED_EVIDENCE_MAX_AGE = dt.timedelta(minutes=15)
ROLLBACK_RECOVERY_MAX_AGE = dt.timedelta(minutes=15)

SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
DOLT_HEAD_RE = re.compile(r"[0-9a-v]{20,128}\Z")
SAFE_RIG_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
SAFE_BEADS_PREFIX_RE = re.compile(r"[a-z][a-z0-9-]{0,62}\Z")
SAFE_DATABASE_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
GENERATION_FILE_RE = re.compile(r"generation-([0-9]{8})\.json\Z")
ATTEMPT_FILE_RE = re.compile(r"generation-([0-9]{8})-attempt-([0-9a-f]{32})\.json\Z")
SECRET_KEY_RE = re.compile(r"(?:password|token|secret|credential|private[_-]?key)", re.IGNORECASE)
NON_SECRET_METADATA_KEYS = frozenset({"credential_transport", "secrets_included"})

MIGRATION_ARTIFACTS = frozenset(
    {
        "conversion/issues.jsonl",
        "conversion/blockers.jsonl",
        "conversion/hierarchy.jsonl",
        "conversion/manifest.json",
        "checkpoints/empty-target.json",
        "checkpoints/first-import.json",
        "checkpoints/second-import.json",
        "exports/first.jsonl",
        "exports/final.jsonl",
        "migration-report.json",
    }
)

STOPPED_WORKERS_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "status",
        "rig",
        "observed_at",
        "supervisor_running",
        "active_provider_containers",
        "active_sessions",
        "suspension_state",
    }
)
RECOVERY_BASE_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "status",
        "backup_path",
        "backup_server_path",
        "backup_manifest_path",
        "backup_manifest_sha256",
        "source_endpoint",
        "restore_endpoint",
        "source_server",
        "restore_server",
        "restore_preflight",
        "dolt_head",
        "canonical_export_sha256",
        "backup_status",
        "locked_toolchain",
        "secrets_included",
    }
)
ENDPOINT_KEYS = frozenset({"host", "port", "user", "database"})
ATTEMPT_KEYS = frozenset(
    {
        "schema_version",
        "rig",
        "beads_prefix",
        "database",
        "generation",
        "transition",
        "created_at",
        "receipt",
        "previous_generation_record_sha256",
        "baseline_evidence",
        "transition_evidence",
    }
)
GENERATION_KEYS = frozenset((*ATTEMPT_KEYS, "attempt"))
BASELINE_KEYS = frozenset({"snapshot", "migration", "recovery"})
TRANSITION_EVIDENCE_KEYS = frozenset({"stopped_workers", "rollback_recovery"})
SNAPSHOT_RECORD_KEYS = frozenset({"path", "sha256", "source_sha256", "captured_at"})
MIGRATION_RECORD_KEYS = frozenset(
    {
        "path",
        "sha256",
        "report_path",
        "report_sha256",
        "source_sha256",
        "target_directory",
        "target_database",
        "dolt_main_head",
        "canonical_export_sha256",
    }
)
RECOVERY_RECORD_KEYS = frozenset(
    {
        "path",
        "sha256",
        "captured_at",
        "verified_at",
        "source_database",
        "dolt_head",
        "canonical_export_sha256",
    }
)
STOPPED_RECORD_KEYS = frozenset({"path", "sha256", "observed_at"})
MIGRATION_REPORT_KEYS = frozenset(
    {
        "schema_version",
        "status",
        "source",
        "target",
        "counts",
        "artifact_digests",
        "empty_target_attestation",
        "dry_run",
        "first_import",
        "first_verification",
        "second_import",
        "final_verification",
        "idempotency",
        "credential_transport",
        "locked_toolchain",
    }
)
RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "rig",
        "mode",
        "beads_prefix",
        "database",
        "taskmaster_snapshot_sha256",
        "migration_report_sha256",
        "backup_restore_report_sha256",
        "generation",
        "activated_at",
        "previous_receipt_sha256",
    }
)
ATTEMPT_REFERENCE_KEYS = frozenset({"path", "sha256"})


class GasCityAuthorityError(RuntimeError):
    """The lifecycle could not prove a safe, exact authority state."""


class GasCityAuthorityCommittedError(GasCityAuthorityError):
    """The live receipt committed even though a later lifecycle gate failed."""

    def __init__(
        self,
        message: str,
        *,
        receipt: task_authority.TaskAuthorityReceipt,
        receipt_path: Path,
    ) -> None:
        self.receipt = receipt
        self.receipt_path = receipt_path
        super().__init__(message)


StoppedWorkersHook = Callable[[str, Path, Mapping[str, Any]], bool]


@dataclasses.dataclass(frozen=True)
class AuthorityLayout:
    """The only accepted production paths for one rig's authority state."""

    city_root: Path
    runtime_root: Path
    authority_root: Path
    receipt_path: Path
    history_root: Path
    attempts_root: Path
    lifecycle_lock_path: Path


@dataclasses.dataclass(frozen=True)
class AuthorityChainReport:
    """A fully reverified live receipt and its append-only history."""

    layout: AuthorityLayout
    current: task_authority.TaskAuthorityReceipt | None
    generation_records: tuple[Mapping[str, Any], ...]
    current_record_sha256: str | None
    recoverable_attempt: Mapping[str, Any] | None
    uncommitted_attempts: tuple[Mapping[str, Any], ...]

    @property
    def generation(self) -> int:
        return 0 if self.current is None else self.current.generation


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _format_utc(value: dt.datetime) -> str:
    normalized = _require_utc_datetime(value, label="clock")
    return normalized.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_utc_datetime(value: dt.datetime, *, label: str) -> dt.datetime:
    if not isinstance(value, dt.datetime) or value.tzinfo is None:
        raise GasCityAuthorityError(f"{label} must be a timezone-aware datetime")
    if value.utcoffset() != dt.timedelta(0):
        raise GasCityAuthorityError(f"{label} must use UTC")
    return value.astimezone(dt.timezone.utc)


def _parse_utc(value: Any, *, label: str) -> dt.datetime:
    if type(value) is not str or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z",
        value,
    ):
        raise GasCityAuthorityError(f"{label} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GasCityAuthorityError(f"{label} is not a valid UTC timestamp") from exc
    return _require_utc_datetime(parsed, label=label)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GasCityAuthorityError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise GasCityAuthorityError(f"non-finite JSON number is not allowed: {value}")


def _load_json(content: bytes, *, label: str) -> dict[str, Any]:
    if not content or len(content) > MAX_JSON_BYTES:
        raise GasCityAuthorityError(f"{label} is empty or exceeds {MAX_JSON_BYTES} bytes")
    try:
        parsed = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise GasCityAuthorityError(f"{label} is not valid strict JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise GasCityAuthorityError(f"{label} must contain one JSON object")
    return parsed


def _stable_private_file(path: Path, *, label: str) -> bytes:
    candidate = Path(path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise GasCityAuthorityError(f"{label} path must be absolute and normalized")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production is Linux.
        raise GasCityAuthorityError("safe evidence reads require O_NOFOLLOW")
    try:
        descriptor = os.open(
            candidate,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | no_follow,
        )
    except OSError as exc:
        raise GasCityAuthorityError(f"cannot open {label}: {candidate}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise GasCityAuthorityError(f"{label} must be a regular non-symlink file")
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise GasCityAuthorityError(f"{label} permissions must be exactly 0600")
        if before.st_uid != os.geteuid():
            raise GasCityAuthorityError(f"{label} must be owned by the current user")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(MAX_JSON_BYTES + 1)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after or len(content) != after.st_size:
            raise GasCityAuthorityError(f"{label} changed while it was read")
        if len(content) > MAX_JSON_BYTES:
            raise GasCityAuthorityError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
        return content
    finally:
        os.close(descriptor)


def _require_private_directory(path: Path, *, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise GasCityAuthorityError(f"{label} path must be absolute and normalized")
    try:
        metadata = candidate.stat(follow_symlinks=False)
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GasCityAuthorityError(f"cannot inspect {label}: {candidate}") from exc
    if resolved != candidate or not stat.S_ISDIR(metadata.st_mode):
        raise GasCityAuthorityError(f"{label} must be a real, non-symlink directory")
    if stat.S_IMODE(metadata.st_mode) != 0o700 or metadata.st_uid != os.geteuid():
        raise GasCityAuthorityError(f"{label} must be owner-owned mode 0700")
    return candidate


def _create_private_directory(path: Path, *, label: str) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_symlink():
        return _require_private_directory(candidate, label=label)
    try:
        candidate.mkdir(mode=0o700)
    except OSError as exc:
        raise GasCityAuthorityError(f"cannot create {label}: {candidate}") from exc
    return _require_private_directory(candidate, label=label)


def authority_layout(city_root: Path, *, rig: str, create: bool = False) -> AuthorityLayout:
    """Derive the exact ``runtime/authority/<rig>.json`` production layout."""

    if type(rig) is not str or SAFE_RIG_RE.fullmatch(rig) is None:
        raise GasCityAuthorityError("rig must match [a-z][a-z0-9_-]{0,62}")
    raw_city = Path(city_root).expanduser()
    if not raw_city.is_absolute() or ".." in raw_city.parts:
        raise GasCityAuthorityError("city root must be an absolute normalized path")
    try:
        city = raw_city.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GasCityAuthorityError(f"city root does not exist: {raw_city}") from exc
    if city != raw_city or raw_city.is_symlink():
        raise GasCityAuthorityError("city root must not traverse a symlink")
    runtime = city / "runtime"
    _require_private_directory(runtime, label="city runtime root")
    authority = runtime / "authority"
    if create:
        authority = _create_private_directory(authority, label="authority root")
    else:
        authority = _require_private_directory(authority, label="authority root")
    history = authority / "history"
    if create:
        history = _create_private_directory(history, label="authority history root")
    else:
        history = _require_private_directory(history, label="authority history root")
    rig_history = history / rig
    if create:
        rig_history = _create_private_directory(rig_history, label="rig authority history")
    else:
        rig_history = _require_private_directory(rig_history, label="rig authority history")
    attempts = rig_history / "attempts"
    if create:
        attempts = _create_private_directory(attempts, label="authority attempts root")
    else:
        attempts = _require_private_directory(attempts, label="authority attempts root")
    receipt = authority / f"{rig}.json"
    if receipt != city / "runtime" / "authority" / f"{rig}.json":
        raise GasCityAuthorityError("authority receipt path is not the exact city runtime path")
    return AuthorityLayout(
        city_root=city,
        runtime_root=runtime,
        authority_root=authority,
        receipt_path=receipt,
        history_root=rig_history,
        attempts_root=attempts,
        lifecycle_lock_path=authority / f"{rig}.lifecycle.lock",
    )


@contextmanager
def _lifecycle_lock(layout: AuthorityLayout) -> Iterator[None]:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover
        raise GasCityAuthorityError("authority lifecycle locking requires O_NOFOLLOW")
    try:
        descriptor = os.open(
            layout.lifecycle_lock_path,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | no_follow,
            0o600,
        )
    except OSError as exc:
        raise GasCityAuthorityError("cannot open authority lifecycle lock") from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_uid != os.geteuid()
        ):
            raise GasCityAuthorityError("authority lifecycle lock is unsafe")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    except OSError as exc:
        raise GasCityAuthorityError("cannot lock authority lifecycle") from exc
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _write_append_only_json(path: Path, value: Mapping[str, Any]) -> str:
    content = _json_bytes(value)
    if len(content) > MAX_JSON_BYTES:
        raise GasCityAuthorityError(
            f"append-only authority artifact exceeds {MAX_JSON_BYTES} bytes"
        )
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = _require_private_directory(
        path.parent.resolve(strict=True), label="append-only parent"
    )
    if path.parent != parent:
        raise GasCityAuthorityError("append-only parent path must be absolute and normalized")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover
        raise GasCityAuthorityError("append-only writes require O_NOFOLLOW")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    try:
        parent_fd = os.open(
            parent,
            os.O_RDONLY | os.O_CLOEXEC | directory_flag | no_follow,
        )
    except OSError as exc:
        raise GasCityAuthorityError(f"cannot open append-only authority parent: {parent}") from exc
    temporary_name: str | None = None
    descriptor: int | None = None
    published = False
    try:
        for _ in range(32):
            candidate = f".{path.name}.tmp-{secrets.token_hex(16)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | no_follow,
                    0o600,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            except OSError as exc:
                raise GasCityAuthorityError(
                    f"cannot create append-only authority temporary artifact: {path}"
                ) from exc
            temporary_name = candidate
            break
        if descriptor is None or temporary_name is None:
            raise GasCityAuthorityError(
                f"cannot allocate append-only authority temporary artifact: {path}"
            )

        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_uid != os.geteuid()
            or metadata.st_nlink != 1
        ):
            raise GasCityAuthorityError("append-only authority temporary artifact is unsafe")
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.close(descriptor)
        descriptor = None

        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GasCityAuthorityError(
                f"append-only authority artifact already exists: {path}"
            ) from exc
        except OSError as exc:
            raise GasCityAuthorityError(
                f"cannot publish append-only authority artifact: {path}"
            ) from exc
        published = True

        os.unlink(temporary_name, dir_fd=parent_fd)
        temporary_name = None
        published_metadata = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(published_metadata.st_mode)
            or stat.S_IMODE(published_metadata.st_mode) != 0o600
            or published_metadata.st_uid != os.geteuid()
            or published_metadata.st_nlink != 1
            or published_metadata.st_size != len(content)
        ):
            raise GasCityAuthorityError("published append-only authority artifact is unsafe")
        os.fsync(parent_fd)
    except GasCityAuthorityError:
        raise
    except OSError as exc:
        state = "published" if published else "unpublished"
        raise GasCityAuthorityError(
            f"cannot finalize {state} append-only authority artifact: {path}"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError:
                # A published destination is already complete and durable as a
                # hard link.  A same-inode orphan in this private directory is
                # safer than deleting or rewriting the append-only record.
                pass
        os.close(parent_fd)
    return _sha256(content)


def _relative_evidence_path(layout: AuthorityLayout, path: Path, *, label: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise GasCityAuthorityError(f"{label} must use an absolute normalized path")
    try:
        resolved = candidate.resolve(strict=True)
        relative = resolved.relative_to(layout.runtime_root / "evidence")
    except (OSError, RuntimeError, ValueError) as exc:
        raise GasCityAuthorityError(
            f"{label} must live beneath the city runtime/evidence root"
        ) from exc
    if not relative.parts:
        raise GasCityAuthorityError(f"{label} cannot be the evidence root itself")
    if resolved != candidate:
        raise GasCityAuthorityError(f"{label} must not traverse a symlink")
    return (Path("runtime") / "evidence" / relative).as_posix()


def _evidence_path(layout: AuthorityLayout, relative: Any, *, label: str) -> Path:
    if type(relative) is not str:
        raise GasCityAuthorityError(f"{label}.path must be a string")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("runtime", "evidence"):
        raise GasCityAuthorityError(f"{label}.path is unsafe")
    candidate = layout.city_root / path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(layout.runtime_root / "evidence")
    except (OSError, RuntimeError, ValueError) as exc:
        raise GasCityAuthorityError(f"{label}.path escaped runtime evidence") from exc
    if resolved != candidate:
        raise GasCityAuthorityError(f"{label}.path must not traverse a symlink")
    return resolved


def _walk_reject_secrets(value: Any, *, label: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if (
                str(key) not in NON_SECRET_METADATA_KEYS
                and SECRET_KEY_RE.search(str(key))
                and child not in (None, "", False, [], {})
            ):
                raise GasCityAuthorityError(f"{label} contains secret-like field {key!r}")
            _walk_reject_secrets(child, label=label)
    elif isinstance(value, list):
        for child in value:
            _walk_reject_secrets(child, label=label)


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], *, label: str) -> None:
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise GasCityAuthorityError(
            f"{label} has an unexpected shape: missing={missing}, extra={extra}"
        )


def _require_string(value: Mapping[str, Any], key: str, *, label: str) -> str:
    observed = value.get(key)
    if type(observed) is not str or not observed:
        raise GasCityAuthorityError(f"{label}.{key} must be a non-empty string")
    return observed


def _require_sha256(value: Mapping[str, Any], key: str, *, label: str) -> str:
    observed = _require_string(value, key, label=label)
    if SHA256_RE.fullmatch(observed) is None:
        raise GasCityAuthorityError(f"{label}.{key} must be a lowercase SHA-256")
    return observed


def _validate_identity(*, rig: str, beads_prefix: str, database: str) -> None:
    if type(rig) is not str or SAFE_RIG_RE.fullmatch(rig) is None:
        raise GasCityAuthorityError("rig must match [a-z][a-z0-9_-]{0,62}")
    if type(beads_prefix) is not str or SAFE_BEADS_PREFIX_RE.fullmatch(beads_prefix) is None:
        raise GasCityAuthorityError("beads_prefix must match [a-z][a-z0-9-]{0,62}")
    if type(database) is not str or SAFE_DATABASE_RE.fullmatch(database) is None:
        raise GasCityAuthorityError("database must match [a-z][a-z0-9_-]{0,62}")


def _require_evidence_ancestors(
    layout: AuthorityLayout, path: Path, *, label: str, directory: bool = False
) -> None:
    root = _require_private_directory(
        layout.runtime_root / "evidence", label="runtime evidence root"
    )
    candidate = path if directory else path.parent
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise GasCityAuthorityError(f"{label} escaped runtime evidence") from exc
    current = root
    for part in relative.parts:
        current = current / part
        _require_private_directory(current, label=f"{label} parent")


def _load_private_json(
    path: Path,
    *,
    label: str,
    canonical: bool = True,
) -> tuple[bytes, dict[str, Any]]:
    content = _stable_private_file(path, label=label)
    value = _load_json(content, label=label)
    if canonical and content != _json_bytes(value):
        raise GasCityAuthorityError(f"{label} must use canonical sorted JSON")
    _walk_reject_secrets(value, label=label)
    return content, value


def _jsonl_records(content: bytes, *, label: str) -> list[dict[str, Any]]:
    if len(content) > MAX_JSON_BYTES:
        raise GasCityAuthorityError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
    records: list[dict[str, Any]] = []
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise GasCityAuthorityError(f"{label} is not valid UTF-8") from exc
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        value = _load_json(line.encode("utf-8"), label=f"{label} line {number}")
        _walk_reject_secrets(value, label=label)
        records.append(value)
    return records


def _canonical_export(content: bytes, *, label: str) -> bytes:
    normalized: dict[str, Mapping[str, Any]] = {}
    for record in _jsonl_records(content, label=label):
        identity = record.get("id")
        if type(identity) is not str or not identity or identity in normalized:
            raise GasCityAuthorityError(f"{label} contains an invalid or duplicate ID")
        copy = dict(record)
        dependencies = copy.get("dependencies")
        if dependencies is not None:
            if type(dependencies) is not list or any(
                type(item) is not dict for item in dependencies
            ):
                raise GasCityAuthorityError(f"{label} contains invalid dependencies")
            copy["dependencies"] = sorted(
                dependencies,
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ),
            )
        normalized[identity] = copy
    return b"".join(
        (
            json.dumps(
                normalized[identity],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        for identity in sorted(normalized)
    )


def _validate_snapshot(layout: AuthorityLayout, snapshot_dir: Path) -> tuple[bytes, dict[str, Any]]:
    raw = Path(snapshot_dir)
    if not raw.is_absolute() or ".." in raw.parts:
        raise GasCityAuthorityError("snapshot directory must be absolute and normalized")
    try:
        resolved = raw.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GasCityAuthorityError("snapshot directory does not exist") from exc
    if resolved != raw:
        raise GasCityAuthorityError("snapshot directory must not traverse a symlink")
    _relative_evidence_path(layout, resolved, label="Taskmaster snapshot")
    _require_private_directory(resolved, label="Taskmaster snapshot directory")
    _require_evidence_ancestors(layout, resolved, label="Taskmaster snapshot", directory=True)
    manifest_path = resolved / "snapshot-manifest.json"
    manifest_bytes, manifest = _load_private_json(
        manifest_path, label="Taskmaster snapshot manifest"
    )
    for name in ("tasks.json", "taskmaster-health.txt"):
        _stable_private_file(resolved / name, label=f"Taskmaster snapshot {name}")
    try:
        source_bytes, loaded = gas_city_ops.load_taskmaster_snapshot(resolved)
    except gas_city_ops.GasCityOpsError as exc:
        raise GasCityAuthorityError("Taskmaster snapshot failed semantic re-verification") from exc
    if loaded != manifest:
        raise GasCityAuthorityError("Taskmaster snapshot manifest changed during verification")
    _require_exact_keys(
        manifest,
        frozenset(
            {
                "schema_version",
                "status",
                "captured_at",
                "source",
                "git",
                "taskmaster_health_sha256",
            }
        ),
        label="Taskmaster snapshot manifest",
    )
    source = manifest.get("source")
    git = manifest.get("git")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("status") != "frozen"
        or type(source) is not dict
        or type(git) is not dict
    ):
        raise GasCityAuthorityError("Taskmaster snapshot manifest is not an exact frozen v1 record")
    _require_exact_keys(
        source,
        frozenset({"repo_root", "relative_path", "sha256", "size_bytes", "mtime_ns"}),
        label="Taskmaster snapshot source",
    )
    _require_exact_keys(
        git,
        frozenset({"head", "dirty_paths"}),
        label="Taskmaster snapshot git",
    )
    captured_at = _require_string(manifest, "captured_at", label="Taskmaster snapshot")
    _parse_utc(captured_at, label="Taskmaster snapshot captured_at")
    source_sha = _require_sha256(source, "sha256", label="Taskmaster snapshot source")
    if (
        source.get("relative_path") != ".taskmaster/tasks/tasks.json"
        or source.get("size_bytes") != len(source_bytes)
        or type(source.get("mtime_ns")) is not int
        or source["mtime_ns"] < 0
        or type(source.get("repo_root")) is not str
        or not Path(source["repo_root"]).is_absolute()
        or source_sha != _sha256(source_bytes)
    ):
        raise GasCityAuthorityError("Taskmaster snapshot source metadata is inconsistent")
    dirty = git.get("dirty_paths")
    if (
        type(git.get("head")) is not str
        or re.fullmatch(r"[0-9a-f]{40,64}", git["head"]) is None
        or type(dirty) is not list
        or dirty != sorted(set(dirty))
        or any(
            type(item) is not str or Path(item).is_absolute() or ".." in Path(item).parts
            for item in dirty
        )
        or SHA256_RE.fullmatch(str(manifest.get("taskmaster_health_sha256"))) is None
    ):
        raise GasCityAuthorityError("Taskmaster snapshot Git or health evidence is invalid")
    return source_bytes, {
        "path": _relative_evidence_path(
            layout, manifest_path, label="Taskmaster snapshot manifest"
        ),
        "sha256": _sha256(manifest_bytes),
        "source_sha256": source_sha,
        "captured_at": captured_at,
    }


def _require_dolt_head(value: Any, *, label: str) -> str:
    if type(value) is not str or DOLT_HEAD_RE.fullmatch(value) is None:
        raise GasCityAuthorityError(f"{label} must be a lowercase Dolt main head")
    return value


def _normalize_target_directory(value: Path | str, *, label: str) -> str:
    if isinstance(value, Path):
        text = value.as_posix()
    elif type(value) is str:
        text = value
    else:
        raise GasCityAuthorityError(f"{label} must be an absolute path")
    path = Path(text)
    if not text or not path.is_absolute() or ".." in path.parts or path.as_posix() != text:
        raise GasCityAuthorityError(f"{label} must be an absolute normalized POSIX path")
    return text


def _validate_import_summary(
    value: Any,
    *,
    label: str,
    issue_count: int,
    dry_run: bool,
) -> Mapping[str, Any]:
    keys = frozenset(
        {
            "schema_version",
            "created",
            "skipped",
            "dry_run",
            "ids_count",
            "stale_skipped_ids_count",
            "tie_kept_local_ids_count",
            "updated_issues_count",
        }
    )
    if type(value) is not dict:
        raise GasCityAuthorityError(f"{label} must be an import summary object")
    _require_exact_keys(value, keys, label=label)
    if (
        type(value.get("schema_version")) not in (int, str)
        or value.get("created") != issue_count
        or value.get("skipped") != 0
        or value.get("dry_run") is not dry_run
        or value.get("ids_count") != (0 if dry_run else issue_count)
        or value.get("stale_skipped_ids_count") != 0
        or value.get("tie_kept_local_ids_count") != 0
        or value.get("updated_issues_count") != 0
    ):
        raise GasCityAuthorityError(f"{label} does not prove an exact complete import")
    return value


def _validate_migration(
    layout: AuthorityLayout,
    manifest_path: Path,
    *,
    source_bytes: bytes,
    snapshot_record: Mapping[str, Any],
    beads_prefix: str,
    database: str,
    expected_target_directory: Path | str,
) -> dict[str, Any]:
    path = Path(manifest_path)
    _relative_evidence_path(layout, path, label="migration evidence manifest")
    _require_evidence_ancestors(layout, path, label="migration evidence manifest")
    manifest_bytes, manifest = _load_private_json(path, label="migration evidence manifest")
    _require_exact_keys(
        manifest,
        frozenset({"schema_version", "status", "source_sha256", "artifacts"}),
        label="migration evidence manifest",
    )
    artifacts = manifest.get("artifacts")
    source_sha = _require_sha256(manifest, "source_sha256", label="migration evidence manifest")
    if (
        manifest.get("schema_version") != MIGRATION_EVIDENCE_SCHEMA
        or manifest.get("status") != "pass"
        or source_sha != snapshot_record.get("source_sha256")
        or source_sha != _sha256(source_bytes)
        or type(artifacts) is not dict
        or set(artifacts) != MIGRATION_ARTIFACTS
    ):
        raise GasCityAuthorityError("migration manifest does not bind the frozen Taskmaster source")

    run_root = path.parent
    _require_private_directory(run_root, label="migration evidence run root")
    artifact_bytes: dict[str, bytes] = {}
    for relative_name in sorted(MIGRATION_ARTIFACTS):
        digest = artifacts.get(relative_name)
        relative = Path(relative_name)
        if (
            type(digest) is not str
            or SHA256_RE.fullmatch(digest) is None
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise GasCityAuthorityError("migration manifest contains an unsafe artifact record")
        artifact_path = run_root / relative
        try:
            resolved = artifact_path.resolve(strict=True)
            resolved.relative_to(run_root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise GasCityAuthorityError(
                f"migration artifact escaped its run: {relative_name}"
            ) from exc
        if resolved != artifact_path:
            raise GasCityAuthorityError(f"migration artifact traverses a symlink: {relative_name}")
        _require_evidence_ancestors(layout, resolved, label=f"migration artifact {relative_name}")
        content = _stable_private_file(resolved, label=f"migration artifact {relative_name}")
        if _sha256(content) != digest:
            raise GasCityAuthorityError(f"migration artifact digest mismatch: {relative_name}")
        artifact_bytes[relative_name] = content

    try:
        conversion = taskmaster_beads.build_artifacts(
            source_bytes,
            tag="master",
            prefix=beads_prefix,
            expected_source_sha256=source_sha,
        )
    except taskmaster_beads.ConversionError as exc:
        raise GasCityAuthorityError("frozen Taskmaster source no longer converts exactly") from exc
    for name in taskmaster_beads.ARTIFACT_NAMES:
        observed = artifact_bytes[f"conversion/{name}"]
        if observed != conversion.artifacts[name]:
            raise GasCityAuthorityError(f"migration conversion artifact drift: {name}")

    first_export = artifact_bytes["exports/first.jsonl"]
    final_export = artifact_bytes["exports/final.jsonl"]
    try:
        first_verification = taskmaster_beads.verify_export(
            first_export,
            source_bytes=source_bytes,
            artifacts=conversion.artifacts,
            expected_source_sha256=source_sha,
        )
        final_verification = taskmaster_beads.verify_export(
            final_export,
            source_bytes=source_bytes,
            artifacts=conversion.artifacts,
            expected_source_sha256=source_sha,
        )
    except taskmaster_beads.ReconciliationError as exc:
        raise GasCityAuthorityError("migration export failed exact reconciliation") from exc
    first_canonical = _canonical_export(first_export, label="first Beads export")
    final_canonical = _canonical_export(final_export, label="final Beads export")
    if first_canonical != final_canonical:
        raise GasCityAuthorityError("migration second import changed canonical Beads state")

    report_bytes = artifact_bytes["migration-report.json"]
    report = _load_json(report_bytes, label="migration report")
    if report_bytes != _json_bytes(report):
        raise GasCityAuthorityError("migration report must use canonical sorted JSON")
    _walk_reject_secrets(report, label="migration report")
    _require_exact_keys(report, MIGRATION_REPORT_KEYS, label="migration report")
    if (
        report.get("schema_version") != MIGRATION_RUN_SCHEMA
        or report.get("status") != "pass"
        or report.get("credential_transport") != "runner-environment-only"
    ):
        raise GasCityAuthorityError("migration report is not an exact passing operational run")
    try:
        gas_city_ops.validate_locked_operation_toolchain_evidence(
            layout.city_root / "runtime-lock.json",
            report.get("locked_toolchain"),
        )
    except gas_city_ops.GasCityOpsError as exc:
        raise GasCityAuthorityError(f"migration report toolchain is not lock-bound: {exc}") from exc
    report_source = report.get("source")
    target = report.get("target")
    counts = report.get("counts")
    idempotency = report.get("idempotency")
    if not all(type(item) is dict for item in (report_source, target, counts, idempotency)):
        raise GasCityAuthorityError(
            "migration report has malformed source, target, counts, or idempotency"
        )
    assert isinstance(report_source, dict)
    assert isinstance(target, dict)
    assert isinstance(counts, dict)
    assert isinstance(idempotency, dict)
    _require_exact_keys(report_source, frozenset({"sha256", "tag"}), label="migration source")
    _require_exact_keys(
        target,
        frozenset({"directory", "database", "beads_version"}),
        label="migration target",
    )
    _require_exact_keys(
        counts,
        frozenset(
            {
                "preexisting_records",
                "manifest_issues",
                "blocker_relationships",
                "hierarchy_relationships",
            }
        ),
        label="migration counts",
    )
    expected_target = _normalize_target_directory(
        expected_target_directory, label="expected migration target"
    )
    expected_counts = {
        "preexisting_records": 0,
        "manifest_issues": conversion.manifest["counts"]["issues"],
        "blocker_relationships": conversion.manifest["counts"]["blocker_relationships"],
        "hierarchy_relationships": conversion.manifest["counts"]["hierarchy_relationships"],
    }
    if (
        report_source != {"sha256": source_sha, "tag": "master"}
        or target
        != {
            "directory": expected_target,
            "database": database,
            "beads_version": taskmaster_beads.TARGET_BEADS_VERSION,
        }
        or counts != expected_counts
        or report.get("artifact_digests") != conversion.manifest["digests"]
        or report.get("first_verification") != first_verification
        or report.get("final_verification") != final_verification
    ):
        raise GasCityAuthorityError(
            "migration report disagrees with re-derived conversion evidence"
        )

    issue_count = int(expected_counts["manifest_issues"])
    _validate_import_summary(
        report.get("dry_run"), label="migration dry-run", issue_count=issue_count, dry_run=True
    )
    first_import = _validate_import_summary(
        report.get("first_import"),
        label="migration first import",
        issue_count=issue_count,
        dry_run=False,
    )
    second_import = _validate_import_summary(
        report.get("second_import"),
        label="migration second import",
        issue_count=issue_count,
        dry_run=False,
    )
    empty = _load_json(
        artifact_bytes["checkpoints/empty-target.json"], label="empty-target checkpoint"
    )
    first_checkpoint = _load_json(
        artifact_bytes["checkpoints/first-import.json"], label="first-import checkpoint"
    )
    second_checkpoint = _load_json(
        artifact_bytes["checkpoints/second-import.json"], label="second-import checkpoint"
    )
    for checkpoint, name, raw in (
        (empty, "empty-target checkpoint", artifact_bytes["checkpoints/empty-target.json"]),
        (
            first_checkpoint,
            "first-import checkpoint",
            artifact_bytes["checkpoints/first-import.json"],
        ),
        (
            second_checkpoint,
            "second-import checkpoint",
            artifact_bytes["checkpoints/second-import.json"],
        ),
    ):
        if raw != _json_bytes(checkpoint):
            raise GasCityAuthorityError(f"{name} must use canonical sorted JSON")
        _walk_reject_secrets(checkpoint, label=name)
    _require_exact_keys(
        empty,
        frozenset(
            {
                "schema_version",
                "status",
                "phase",
                "issue_count",
                "working_set_changes",
                "expected_config_changes",
                "unexpected_working_changes",
                "branch_count",
                "main_branch_count",
                "commit_count",
            }
        ),
        label="empty-target checkpoint",
    )
    empty_attestation = {
        key: empty[key]
        for key in (
            "issue_count",
            "working_set_changes",
            "expected_config_changes",
            "unexpected_working_changes",
            "branch_count",
            "main_branch_count",
            "commit_count",
        )
    }
    if (
        empty.get("schema_version") != MIGRATION_RUN_SCHEMA
        or empty.get("status") != "pass"
        or empty.get("phase") != "empty-target"
        or empty_attestation.get("issue_count") != 0
        or empty_attestation.get("working_set_changes") != 1
        or empty_attestation.get("expected_config_changes") != 1
        or empty_attestation.get("unexpected_working_changes") != 0
        or empty_attestation.get("branch_count") != 1
        or empty_attestation.get("main_branch_count") != 1
        or type(empty_attestation.get("commit_count")) is not int
        or empty_attestation["commit_count"] < 1
        or report.get("empty_target_attestation") != empty_attestation
    ):
        raise GasCityAuthorityError(
            "empty-target checkpoint does not prove a clean initialized target"
        )

    _require_exact_keys(
        first_checkpoint,
        frozenset(
            {
                "schema_version",
                "status",
                "phase",
                "source_sha256",
                "preflight_dolt_main_head",
                "first_dolt_main_head",
                "import",
            }
        ),
        label="first-import checkpoint",
    )
    _require_exact_keys(
        second_checkpoint,
        frozenset(
            {
                "schema_version",
                "status",
                "phase",
                "source_sha256",
                "first_dolt_main_head",
                "final_dolt_main_head",
                "import",
            }
        ),
        label="second-import checkpoint",
    )
    preflight_head = _require_dolt_head(
        first_checkpoint.get("preflight_dolt_main_head"), label="preflight Dolt head"
    )
    first_head = _require_dolt_head(
        first_checkpoint.get("first_dolt_main_head"), label="first Dolt head"
    )
    final_head = _require_dolt_head(
        second_checkpoint.get("final_dolt_main_head"), label="final Dolt head"
    )
    if (
        first_checkpoint.get("schema_version") != MIGRATION_RUN_SCHEMA
        or first_checkpoint.get("status") != "mutation-observed"
        or first_checkpoint.get("phase") != "first-import"
        or first_checkpoint.get("source_sha256") != source_sha
        or first_checkpoint.get("import") != first_import
        or second_checkpoint.get("schema_version") != MIGRATION_RUN_SCHEMA
        or second_checkpoint.get("status") != "mutation-observed"
        or second_checkpoint.get("phase") != "second-import"
        or second_checkpoint.get("source_sha256") != source_sha
        or second_checkpoint.get("first_dolt_main_head") != first_head
        or second_checkpoint.get("import") != second_import
        or preflight_head == first_head
        or final_head != first_head
    ):
        raise GasCityAuthorityError("migration checkpoints do not prove one idempotent mutation")

    idempotency_keys = frozenset(
        {
            "status",
            "canonical_export_sha256",
            "first_raw_export_sha256",
            "final_raw_export_sha256",
            "preflight_dolt_main_head",
            "post_dry_run_dolt_main_head",
            "first_dolt_main_head",
            "final_dolt_main_head",
            "dry_run_head_unchanged",
            "first_import_advanced_main",
            "export_unchanged",
            "raw_export_unchanged",
            "dolt_main_head_unchanged",
        }
    )
    _require_exact_keys(idempotency, idempotency_keys, label="migration idempotency")
    canonical_sha = _sha256(final_canonical)
    if (
        idempotency.get("status") != "pass"
        or idempotency.get("canonical_export_sha256") != canonical_sha
        or idempotency.get("first_raw_export_sha256") != _sha256(first_export)
        or idempotency.get("final_raw_export_sha256") != _sha256(final_export)
        or idempotency.get("preflight_dolt_main_head") != preflight_head
        or idempotency.get("post_dry_run_dolt_main_head") != preflight_head
        or idempotency.get("first_dolt_main_head") != first_head
        or idempotency.get("final_dolt_main_head") != final_head
        or any(
            idempotency.get(key) is not True
            for key in (
                "dry_run_head_unchanged",
                "first_import_advanced_main",
                "export_unchanged",
                "dolt_main_head_unchanged",
            )
        )
        or idempotency.get("raw_export_unchanged") is not (first_export == final_export)
    ):
        raise GasCityAuthorityError("migration idempotency evidence is internally inconsistent")

    report_path = run_root / "migration-report.json"
    return {
        "path": _relative_evidence_path(layout, path, label="migration evidence manifest"),
        "sha256": _sha256(manifest_bytes),
        "report_path": _relative_evidence_path(layout, report_path, label="migration report"),
        "report_sha256": _sha256(report_bytes),
        "source_sha256": source_sha,
        "target_directory": expected_target,
        "target_database": database,
        "dolt_main_head": final_head,
        "canonical_export_sha256": canonical_sha,
    }


def _validate_endpoint(value: Any, *, label: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise GasCityAuthorityError(f"{label} must be an endpoint object")
    _require_exact_keys(value, ENDPOINT_KEYS, label=label)
    host = value.get("host")
    port = value.get("port")
    user = value.get("user")
    database = value.get("database")
    if (
        type(host) is not str
        or not host
        or any(character.isspace() or ord(character) < 32 for character in host)
        or type(port) is not int
        or not 1 <= port <= 65535
        or type(user) is not str
        or SAFE_DATABASE_RE.fullmatch(user) is None
        or type(database) is not str
        or SAFE_DATABASE_RE.fullmatch(database) is None
    ):
        raise GasCityAuthorityError(f"{label} is not a valid non-secret Dolt endpoint")
    return value


def _validate_recovery(
    layout: AuthorityLayout,
    recovery_path: Path,
    *,
    database: str,
    expected_head: str | None = None,
    expected_export_sha256: str | None = None,
    not_before: dt.datetime | None = None,
    transition_at: dt.datetime | None = None,
    require_fresh: bool = False,
) -> dict[str, Any]:
    path = Path(recovery_path)
    _relative_evidence_path(layout, path, label="recovery evidence")
    _require_evidence_ancestors(layout, path, label="recovery evidence")
    content, value = _load_private_json(path, label="recovery evidence")
    _require_exact_keys(
        value,
        frozenset((*RECOVERY_BASE_KEYS, "captured_at", "verified_at")),
        label="recovery evidence",
    )
    captured_at_text = _require_string(value, "captured_at", label="recovery evidence")
    verified_at_text = _require_string(value, "verified_at", label="recovery evidence")
    captured_at = _parse_utc(captured_at_text, label="recovery captured_at")
    verified_at = _parse_utc(verified_at_text, label="recovery verified_at")
    source = _validate_endpoint(value.get("source_endpoint"), label="recovery source endpoint")
    restore = _validate_endpoint(value.get("restore_endpoint"), label="recovery restore endpoint")
    head = _require_dolt_head(value.get("dolt_head"), label="recovery Dolt head")
    export_sha = _require_sha256(value, "canonical_export_sha256", label="recovery evidence")
    backup_path = value.get("backup_path")
    try:
        runtime_lock = gas_city_ops.load_runtime_lock(
            layout.city_root / "runtime-lock.json",
            _validate_promotions=False,
        )
        gas_city_ops.validate_native_restore_evidence(
            layout.city_root / "runtime-lock.json",
            value,
            expected_source_endpoint=gas_city_ops.DoltEndpoint(
                gas_city_ops.AEGIS_BEADS_INIT_HOST,
                gas_city_ops.AEGIS_BEADS_INIT_PORT,
                gas_city_ops.AEGIS_RECOVERY_USER,
                gas_city_ops.AEGIS_BEADS_INIT_DATABASE,
            ),
            expected_source_container="gas-city-aegis-dolt",
            expected_source_image_id=runtime_lock["images"]["dolt_server"]["image_id"],
            expected_source_relay_image_id=runtime_lock["images"]["egress_proxy"]["image_id"],
        )
    except gas_city_ops.GasCityOpsError as exc:
        raise GasCityAuthorityError(
            f"recovery evidence is not independently reverified: {exc}"
        ) from exc
    if (
        value.get("schema_version") != gas_city_ops.NATIVE_RESTORE_SCHEMA_VERSION
        or value.get("kind") != RECOVERY_KIND
        or value.get("status") != "pass"
        or value.get("secrets_included") is not False
        or type(backup_path) is not str
        or not backup_path
        or not Path(backup_path).is_absolute()
        or ".." in Path(backup_path).parts
        or source.get("database") != database
        or (source.get("host"), source.get("port")) == (restore.get("host"), restore.get("port"))
        or type(value.get("backup_status")) is not dict
        or not value["backup_status"]
        or verified_at < captured_at
    ):
        raise GasCityAuthorityError("recovery evidence does not prove a distinct-server restore")
    _walk_reject_secrets(value.get("backup_status"), label="recovery backup status")
    if expected_head is not None and head != expected_head:
        raise GasCityAuthorityError("recovery Dolt head does not match migration evidence")
    if expected_export_sha256 is not None and export_sha != expected_export_sha256:
        raise GasCityAuthorityError("recovery export does not match migration evidence")
    if not_before is not None and captured_at <= _require_utc_datetime(
        not_before, label="recovery lower bound"
    ):
        raise GasCityAuthorityError("rollback recovery must be captured after Beads activation")
    if transition_at is not None:
        transition_time = _require_utc_datetime(transition_at, label="transition time")
        if verified_at > transition_time:
            raise GasCityAuthorityError("recovery evidence cannot be from the future")
        if require_fresh and transition_time - captured_at > ROLLBACK_RECOVERY_MAX_AGE:
            raise GasCityAuthorityError("rollback recovery evidence is older than 15 minutes")
    elif require_fresh:
        raise GasCityAuthorityError("fresh recovery validation requires a transition time")
    return {
        "path": _relative_evidence_path(layout, path, label="recovery evidence"),
        "sha256": _sha256(content),
        "captured_at": captured_at_text,
        "verified_at": verified_at_text,
        "source_database": database,
        "dolt_head": head,
        "canonical_export_sha256": export_sha,
    }


def _validate_stopped_workers(
    layout: AuthorityLayout,
    stopped_path: Path,
    *,
    rig: str,
    transition_at: dt.datetime,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    path = Path(stopped_path)
    _relative_evidence_path(layout, path, label="stopped-worker evidence")
    _require_evidence_ancestors(layout, path, label="stopped-worker evidence")
    content, value = _load_private_json(path, label="stopped-worker evidence")
    _require_exact_keys(value, STOPPED_WORKERS_KEYS, label="stopped-worker evidence")
    observed_text = _require_string(value, "observed_at", label="stopped-worker evidence")
    observed = _parse_utc(observed_text, label="stopped-worker observed_at")
    transition_time = _require_utc_datetime(transition_at, label="transition time")
    suspension = value.get("suspension_state")
    if (
        type(suspension) is not dict
        or set(suspension)
        != {
            "path",
            "sha256",
            "city_suspended",
            "aegis_suspended",
            "updated_at",
        }
        or suspension.get("path") != ".gc/runtime/suspension-state.json"
        or type(suspension.get("sha256")) is not str
        or SHA256_RE.fullmatch(suspension["sha256"]) is None
        or suspension.get("city_suspended") is not True
        or suspension.get("aegis_suspended") is not True
        or _parse_utc(suspension.get("updated_at"), label="stopped-worker suspension updated_at")
        > observed
    ):
        raise GasCityAuthorityError("stopped-worker evidence lacks exact suspension-state proof")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != STOPPED_WORKERS_KIND
        or value.get("status") != "pass"
        or value.get("rig") != rig
        or value.get("supervisor_running") is not False
        or value.get("active_provider_containers") != []
        or value.get("active_sessions") != []
        or observed > transition_time
        or transition_time - observed > STOPPED_EVIDENCE_MAX_AGE
    ):
        raise GasCityAuthorityError(
            "stopped-worker evidence is stale or does not prove an empty worker set"
        )
    return (
        {
            "path": _relative_evidence_path(layout, path, label="stopped-worker evidence"),
            "sha256": _sha256(content),
            "observed_at": observed_text,
        },
        value,
    )


def _invoke_stopped_hook(
    hook: StoppedWorkersHook,
    *,
    phase: str,
    path: Path,
    evidence: Mapping[str, Any],
) -> None:
    if not callable(hook):
        raise GasCityAuthorityError("a live stopped-worker hook is required")
    try:
        result = hook(phase, path, evidence)
    except Exception as exc:
        raise GasCityAuthorityError(f"stopped-worker hook failed during {phase}") from exc
    if result is not True:
        raise GasCityAuthorityError(
            f"stopped-worker hook did not prove stopped state during {phase}"
        )


def _receipt_from_mapping(value: Any, *, label: str) -> task_authority.TaskAuthorityReceipt:
    if type(value) is not dict:
        raise GasCityAuthorityError(f"{label} must be an authority receipt object")
    _require_exact_keys(value, RECEIPT_KEYS, label=label)
    try:
        schema_version = _require_string(value, "schema_version", label=label)
        rig = _require_string(value, "rig", label=label)
        mode = task_authority.TaskAuthorityMode(_require_string(value, "mode", label=label))
        beads_prefix = _require_string(value, "beads_prefix", label=label)
        database = _require_string(value, "database", label=label)
        generation = value.get("generation")
        if type(generation) is not int:
            raise GasCityAuthorityError(f"{label}.generation must be an integer")
        activated_at = _require_string(value, "activated_at", label=label)
        previous = value.get("previous_receipt_sha256")
        if previous is not None and type(previous) is not str:
            raise GasCityAuthorityError(f"{label}.previous_receipt_sha256 must be null or a string")
        evidence = task_authority.TaskAuthorityEvidence(
            taskmaster_snapshot_sha256=_require_sha256(
                value, "taskmaster_snapshot_sha256", label=label
            ),
            migration_report_sha256=_require_sha256(value, "migration_report_sha256", label=label),
            backup_restore_report_sha256=_require_sha256(
                value, "backup_restore_report_sha256", label=label
            ),
        )
        return task_authority.TaskAuthorityReceipt(
            schema_version=schema_version,
            rig=rig,
            mode=mode,
            beads_prefix=beads_prefix,
            database=database,
            evidence=evidence,
            generation=generation,
            activated_at=activated_at,
            previous_receipt_sha256=previous,
        )
    except (TypeError, ValueError, task_authority.TaskAuthorityError) as exc:
        raise GasCityAuthorityError(f"{label} is not a valid authority receipt") from exc


def _evidence_from_baseline(
    baseline: Mapping[str, Any],
) -> task_authority.TaskAuthorityEvidence:
    snapshot = baseline["snapshot"]
    migration = baseline["migration"]
    recovery = baseline["recovery"]
    assert isinstance(snapshot, Mapping)
    assert isinstance(migration, Mapping)
    assert isinstance(recovery, Mapping)
    try:
        return task_authority.TaskAuthorityEvidence(
            taskmaster_snapshot_sha256=str(snapshot["sha256"]),
            migration_report_sha256=str(migration["report_sha256"]),
            backup_restore_report_sha256=str(recovery["sha256"]),
        )
    except (KeyError, task_authority.TaskAuthorityError) as exc:
        raise GasCityAuthorityError("baseline evidence cannot construct authority digests") from exc


def _reverify_baseline(
    layout: AuthorityLayout,
    baseline: Any,
    *,
    beads_prefix: str,
    database: str,
) -> Mapping[str, Any]:
    if type(baseline) is not dict:
        raise GasCityAuthorityError("baseline_evidence must be an object")
    _require_exact_keys(baseline, BASELINE_KEYS, label="baseline evidence")
    snapshot_expected = baseline.get("snapshot")
    migration_expected = baseline.get("migration")
    recovery_expected = baseline.get("recovery")
    if not all(
        type(item) is dict for item in (snapshot_expected, migration_expected, recovery_expected)
    ):
        raise GasCityAuthorityError("baseline evidence records must be objects")
    assert isinstance(snapshot_expected, dict)
    assert isinstance(migration_expected, dict)
    assert isinstance(recovery_expected, dict)
    _require_exact_keys(snapshot_expected, SNAPSHOT_RECORD_KEYS, label="snapshot record")
    _require_exact_keys(migration_expected, MIGRATION_RECORD_KEYS, label="migration record")
    _require_exact_keys(recovery_expected, RECOVERY_RECORD_KEYS, label="recovery record")

    manifest_path = _evidence_path(layout, snapshot_expected.get("path"), label="snapshot record")
    source_bytes, snapshot_observed = _validate_snapshot(layout, manifest_path.parent)
    if snapshot_observed != snapshot_expected:
        raise GasCityAuthorityError("stored snapshot record no longer matches its evidence")

    migration_path = _evidence_path(
        layout, migration_expected.get("path"), label="migration record"
    )
    migration_observed = _validate_migration(
        layout,
        migration_path,
        source_bytes=source_bytes,
        snapshot_record=snapshot_observed,
        beads_prefix=beads_prefix,
        database=database,
        expected_target_directory=_require_string(
            migration_expected, "target_directory", label="migration record"
        ),
    )
    if migration_observed != migration_expected:
        raise GasCityAuthorityError("stored migration record no longer matches its evidence")

    recovery_path = _evidence_path(layout, recovery_expected.get("path"), label="recovery record")
    recovery_observed = _validate_recovery(
        layout,
        recovery_path,
        database=database,
        expected_head=migration_observed["dolt_main_head"],
        expected_export_sha256=migration_observed["canonical_export_sha256"],
    )
    if recovery_observed != recovery_expected:
        raise GasCityAuthorityError("stored recovery record no longer matches its evidence")
    return baseline


def _reverify_transition_evidence(
    layout: AuthorityLayout,
    value: Any,
    *,
    receipt: task_authority.TaskAuthorityReceipt,
    previous_receipt: task_authority.TaskAuthorityReceipt | None,
    baseline: Mapping[str, Any],
) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise GasCityAuthorityError("transition_evidence must be an object")
    _require_exact_keys(value, TRANSITION_EVIDENCE_KEYS, label="transition evidence")
    stopped_expected = value.get("stopped_workers")
    if type(stopped_expected) is not dict:
        raise GasCityAuthorityError("transition evidence must bind a stopped-worker receipt")
    _require_exact_keys(stopped_expected, STOPPED_RECORD_KEYS, label="stopped-worker record")
    stopped_path = _evidence_path(
        layout, stopped_expected.get("path"), label="stopped-worker record"
    )
    stopped_observed, _ = _validate_stopped_workers(
        layout,
        stopped_path,
        rig=receipt.rig,
        transition_at=_parse_utc(receipt.activated_at, label="receipt activated_at"),
    )
    if stopped_observed != stopped_expected:
        raise GasCityAuthorityError("stored stopped-worker record no longer matches its evidence")

    rollback_expected = value.get("rollback_recovery")
    if receipt.generation < 3:
        if rollback_expected is not None:
            raise GasCityAuthorityError("only generation 3 may bind rollback recovery evidence")
    else:
        if (
            receipt.generation != 3
            or receipt.mode is not task_authority.TaskAuthorityMode.TASKMASTER
        ):
            raise GasCityAuthorityError(
                "unsupported authority generation beyond the rollback contract"
            )
        if type(rollback_expected) is not dict or previous_receipt is None:
            raise GasCityAuthorityError("generation 3 must bind fresh rollback recovery evidence")
        _require_exact_keys(
            rollback_expected, RECOVERY_RECORD_KEYS, label="rollback recovery record"
        )
        rollback_path = _evidence_path(
            layout, rollback_expected.get("path"), label="rollback recovery record"
        )
        migration = baseline.get("migration")
        if not isinstance(migration, Mapping):
            raise GasCityAuthorityError("generation 3 is missing its migration baseline")
        rollback_observed = _validate_recovery(
            layout,
            rollback_path,
            database=receipt.database,
            expected_head=_require_string(
                migration, "dolt_main_head", label="migration rollback baseline"
            ),
            expected_export_sha256=_require_sha256(
                migration,
                "canonical_export_sha256",
                label="migration rollback baseline",
            ),
            not_before=_parse_utc(previous_receipt.activated_at, label="Beads activation time"),
            transition_at=_parse_utc(receipt.activated_at, label="rollback time"),
            require_fresh=True,
        )
        if rollback_observed != rollback_expected:
            raise GasCityAuthorityError(
                "stored rollback recovery record no longer matches evidence"
            )
    return value


def _relative_authority_path(layout: AuthorityLayout, path: Path, *, label: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise GasCityAuthorityError(f"{label} must use an absolute normalized path")
    try:
        resolved = candidate.resolve(strict=True)
        relative = resolved.relative_to(layout.authority_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise GasCityAuthorityError(f"{label} must live beneath runtime/authority") from exc
    if resolved != candidate or not relative.parts:
        raise GasCityAuthorityError(f"{label} must not traverse a symlink")
    return (Path("runtime") / "authority" / relative).as_posix()


def _authority_path(layout: AuthorityLayout, relative: Any, *, label: str) -> Path:
    if type(relative) is not str:
        raise GasCityAuthorityError(f"{label}.path must be a string")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("runtime", "authority"):
        raise GasCityAuthorityError(f"{label}.path is unsafe")
    candidate = layout.city_root / path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(layout.authority_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise GasCityAuthorityError(f"{label}.path escaped runtime/authority") from exc
    if resolved != candidate:
        raise GasCityAuthorityError(f"{label}.path must not traverse a symlink")
    return resolved


def _expected_generation_shape(
    generation: int,
) -> tuple[str, task_authority.TaskAuthorityMode]:
    shapes = {
        1: ("initialize-taskmaster", task_authority.TaskAuthorityMode.TASKMASTER),
        2: ("activate-beads", task_authority.TaskAuthorityMode.BEADS),
        3: ("rollback-taskmaster", task_authority.TaskAuthorityMode.TASKMASTER),
    }
    try:
        return shapes[generation]
    except KeyError as exc:
        raise GasCityAuthorityError(
            "authority lifecycle supports exactly generations 1 through 3"
        ) from exc


def _validate_attempt_payload(
    layout: AuthorityLayout,
    value: Mapping[str, Any],
    *,
    expected_generation: int,
    expected_rig: str,
    expected_beads_prefix: str,
    expected_database: str,
    previous_receipt: task_authority.TaskAuthorityReceipt | None,
    previous_generation_record_sha256: str | None,
) -> task_authority.TaskAuthorityReceipt:
    _require_exact_keys(value, ATTEMPT_KEYS, label="authority transition attempt")
    receipt = _receipt_from_mapping(value.get("receipt"), label="attempt receipt")
    expected_transition, expected_mode = _expected_generation_shape(expected_generation)
    if (
        value.get("schema_version") != ATTEMPT_SCHEMA
        or value.get("rig") != expected_rig
        or value.get("beads_prefix") != expected_beads_prefix
        or value.get("database") != expected_database
        or value.get("generation") != expected_generation
        or value.get("transition") != expected_transition
        or value.get("created_at") != receipt.activated_at
        or value.get("previous_generation_record_sha256") != previous_generation_record_sha256
        or receipt.rig != expected_rig
        or receipt.beads_prefix != expected_beads_prefix
        or receipt.database != expected_database
        or receipt.generation != expected_generation
        or receipt.mode is not expected_mode
    ):
        raise GasCityAuthorityError(
            "authority transition attempt identity or generation is invalid"
        )
    if expected_generation == 1:
        if previous_receipt is not None or receipt.previous_receipt_sha256 is not None:
            raise GasCityAuthorityError("generation 1 cannot name previous authority state")
    else:
        if previous_receipt is None:
            raise GasCityAuthorityError("later authority generation is missing its predecessor")
        if receipt.previous_receipt_sha256 != task_authority.receipt_sha256(
            previous_receipt
        ) or _parse_utc(receipt.activated_at, label="receipt activated_at") <= _parse_utc(
            previous_receipt.activated_at, label="previous activated_at"
        ):
            raise GasCityAuthorityError("authority receipt chain or transition time is invalid")

    baseline = _reverify_baseline(
        layout,
        value.get("baseline_evidence"),
        beads_prefix=expected_beads_prefix,
        database=expected_database,
    )
    if receipt.evidence != _evidence_from_baseline(baseline):
        raise GasCityAuthorityError("authority receipt digests do not match semantic evidence")
    if expected_generation == 1:
        initial_recovery = baseline["recovery"]
        assert isinstance(initial_recovery, Mapping)
        if _parse_utc(initial_recovery["verified_at"], label="initial recovery time") > _parse_utc(
            receipt.activated_at, label="initial authority time"
        ):
            raise GasCityAuthorityError("initial recovery evidence cannot postdate authority")
    _reverify_transition_evidence(
        layout,
        value.get("transition_evidence"),
        receipt=receipt,
        previous_receipt=previous_receipt,
        baseline=baseline,
    )
    return receipt


def _load_append_only_mapping(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    content, value = _load_private_json(path, label=label)
    return content, value


def _load_current_receipt(
    layout: AuthorityLayout,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
) -> task_authority.TaskAuthorityReceipt | None:
    if layout.receipt_path.is_symlink():
        raise GasCityAuthorityError("live authority receipt must not be a symlink")
    if not layout.receipt_path.exists():
        return None
    try:
        return task_authority.load_authority_receipt(
            layout.receipt_path,
            expected_rig=rig,
            expected_beads_prefix=beads_prefix,
            expected_database=database,
        )
    except task_authority.TaskAuthorityError as exc:
        raise GasCityAuthorityError("live authority receipt is invalid") from exc


def _verify_chain_locked(
    layout: AuthorityLayout,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
) -> AuthorityChainReport:
    current = _load_current_receipt(layout, rig=rig, beads_prefix=beads_prefix, database=database)
    entries = list(layout.history_root.iterdir())
    generation_paths: dict[int, Path] = {}
    for entry in entries:
        if entry == layout.attempts_root:
            continue
        match = GENERATION_FILE_RE.fullmatch(entry.name)
        if match is None or entry.is_dir() or entry.is_symlink():
            raise GasCityAuthorityError(f"unexpected authority history entry: {entry.name}")
        generation = int(match.group(1))
        if generation in generation_paths:
            raise GasCityAuthorityError("duplicate authority generation history")
        generation_paths[generation] = entry
    expected_numbers = list(range(1, len(generation_paths) + 1))
    if sorted(generation_paths) != expected_numbers:
        raise GasCityAuthorityError("authority generation history has a gap")

    records: list[Mapping[str, Any]] = []
    record_digests: list[str] = []
    receipts: list[task_authority.TaskAuthorityReceipt] = []
    committed_attempt_paths: set[Path] = set()
    previous_receipt: task_authority.TaskAuthorityReceipt | None = None
    previous_record_digest: str | None = None
    baseline: Mapping[str, Any] | None = None
    for generation in expected_numbers:
        path = generation_paths[generation]
        content, record = _load_append_only_mapping(
            path, label=f"authority generation {generation}"
        )
        _require_exact_keys(record, GENERATION_KEYS, label="authority generation record")
        if record.get("schema_version") != GENERATION_SCHEMA:
            raise GasCityAuthorityError("authority generation record schema is invalid")
        attempt_reference = record.get("attempt")
        if type(attempt_reference) is not dict:
            raise GasCityAuthorityError("authority generation record must bind its attempt")
        _require_exact_keys(attempt_reference, ATTEMPT_REFERENCE_KEYS, label="attempt reference")
        payload = {key: value for key, value in record.items() if key != "attempt"}
        payload["schema_version"] = ATTEMPT_SCHEMA
        receipt = _validate_attempt_payload(
            layout,
            payload,
            expected_generation=generation,
            expected_rig=rig,
            expected_beads_prefix=beads_prefix,
            expected_database=database,
            previous_receipt=previous_receipt,
            previous_generation_record_sha256=previous_record_digest,
        )
        attempt_path = _authority_path(
            layout, attempt_reference.get("path"), label="attempt reference"
        )
        try:
            attempt_path.relative_to(layout.attempts_root)
        except ValueError as exc:
            raise GasCityAuthorityError(
                "generation record attempt is outside attempts root"
            ) from exc
        attempt_content, attempt = _load_append_only_mapping(
            attempt_path, label=f"authority generation {generation} attempt"
        )
        attempt_name_match = ATTEMPT_FILE_RE.fullmatch(attempt_path.name)
        if (
            attempt != payload
            or attempt_reference.get("sha256") != _sha256(attempt_content)
            or attempt_name_match is None
            or int(attempt_name_match.group(1)) != generation
        ):
            raise GasCityAuthorityError("generation record does not exactly bind its attempt")
        if attempt_path in committed_attempt_paths:
            raise GasCityAuthorityError("one transition attempt cannot commit twice")
        if baseline is None:
            baseline = record["baseline_evidence"]
        elif record["baseline_evidence"] != baseline:
            raise GasCityAuthorityError("baseline evidence changed across authority generations")
        committed_attempt_paths.add(attempt_path)
        records.append(record)
        digest = _sha256(content)
        record_digests.append(digest)
        receipts.append(receipt)
        previous_receipt = receipt
        previous_record_digest = digest

    if current is None:
        if records:
            raise GasCityAuthorityError("authority history exists without a live receipt")
    elif current.generation < len(records) or current.generation > len(records) + 1:
        raise GasCityAuthorityError("live authority generation is inconsistent with history")
    elif current.generation == len(records):
        if not records or task_authority.receipt_mapping(current) != records[-1]["receipt"]:
            raise GasCityAuthorityError("live authority receipt disagrees with committed history")

    attempt_entries = list(layout.attempts_root.iterdir())
    attempt_paths: dict[Path, tuple[bytes, Mapping[str, Any]]] = {}
    for path in attempt_entries:
        match = ATTEMPT_FILE_RE.fullmatch(path.name)
        if match is None or path.is_dir() or path.is_symlink():
            raise GasCityAuthorityError(f"unexpected authority attempt entry: {path.name}")
        content, attempt = _load_append_only_mapping(path, label="authority transition attempt")
        if attempt.get("generation") != int(match.group(1)):
            raise GasCityAuthorityError("authority attempt filename generation mismatch")
        attempt_paths[path] = (content, attempt)

    if not committed_attempt_paths.issubset(attempt_paths):
        raise GasCityAuthorityError("committed authority history references a missing attempt")
    pending: list[Mapping[str, Any]] = []
    matching_current: list[Mapping[str, Any]] = []
    next_generation = len(records) + 1
    for path, (content, attempt) in attempt_paths.items():
        if path in committed_attempt_paths:
            continue
        if attempt.get("generation") != next_generation:
            raise GasCityAuthorityError(
                "unreferenced authority attempt has an impossible generation"
            )
        candidate_receipt = _validate_attempt_payload(
            layout,
            attempt,
            expected_generation=next_generation,
            expected_rig=rig,
            expected_beads_prefix=beads_prefix,
            expected_database=database,
            previous_receipt=receipts[-1] if receipts else None,
            previous_generation_record_sha256=record_digests[-1] if record_digests else None,
        )
        envelope = {
            "path": _relative_authority_path(layout, path, label="authority attempt"),
            "sha256": _sha256(content),
            "payload": attempt,
        }
        if (
            current is not None
            and current.generation == next_generation
            and task_authority.receipt_mapping(candidate_receipt)
            == task_authority.receipt_mapping(current)
        ):
            matching_current.append(envelope)
        else:
            pending.append(envelope)

    recoverable: Mapping[str, Any] | None = None
    if current is not None and current.generation == next_generation:
        if len(matching_current) != 1:
            raise GasCityAuthorityError(
                "live receipt is ahead of history without one unambiguous transition attempt"
            )
        recoverable = matching_current[0]
    elif matching_current:
        raise GasCityAuthorityError("authority attempt unexpectedly matches committed state")
    return AuthorityChainReport(
        layout=layout,
        current=current,
        generation_records=tuple(records),
        current_record_sha256=record_digests[-1] if record_digests else None,
        recoverable_attempt=recoverable,
        uncommitted_attempts=tuple(pending),
    )


def verify_authority_chain(
    city_root: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
) -> AuthorityChainReport:
    """Reverify the live receipt, every history link, and all external evidence."""

    _validate_identity(rig=rig, beads_prefix=beads_prefix, database=database)
    layout = authority_layout(city_root, rig=rig)
    with _lifecycle_lock(layout):
        return _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )


def _transition_time(
    activated_at: str | None, clock: Callable[[], dt.datetime]
) -> tuple[str, dt.datetime]:
    if activated_at is None:
        try:
            now = clock()
        except Exception as exc:
            raise GasCityAuthorityError("authority lifecycle clock failed") from exc
        timestamp = _format_utc(now)
    else:
        if type(activated_at) is not str:
            raise GasCityAuthorityError("activated_at must be an RFC3339 UTC string")
        timestamp = activated_at
    return timestamp, _parse_utc(timestamp, label="authority activated_at")


def _attempt_path(layout: AuthorityLayout, generation: int) -> Path:
    return layout.attempts_root / (
        f"generation-{generation:08d}-attempt-{secrets.token_hex(16)}.json"
    )


def _generation_path(layout: AuthorityLayout, generation: int) -> Path:
    return layout.history_root / f"generation-{generation:08d}.json"


def _history_record(
    attempt: Mapping[str, Any], *, attempt_path: Path, attempt_sha256: str, layout: AuthorityLayout
) -> dict[str, Any]:
    record = dict(attempt)
    record["schema_version"] = GENERATION_SCHEMA
    record["attempt"] = {
        "path": _relative_authority_path(layout, attempt_path, label="authority attempt"),
        "sha256": attempt_sha256,
    }
    return record


def _raise_committed(
    message: str,
    *,
    receipt: task_authority.TaskAuthorityReceipt,
    layout: AuthorityLayout,
    cause: BaseException | None = None,
) -> None:
    error = GasCityAuthorityCommittedError(
        message, receipt=receipt, receipt_path=layout.receipt_path
    )
    if cause is None:
        raise error
    raise error from cause


def _run_core_transition(
    layout: AuthorityLayout,
    *,
    expected_receipt: task_authority.TaskAuthorityReceipt,
    operation: Callable[[], task_authority.TaskAuthorityReceipt],
) -> task_authority.TaskAuthorityReceipt:
    try:
        observed = operation()
    except task_authority.TaskAuthorityCommittedError as exc:
        _raise_committed(
            "live authority committed but its durability is uncertain; recover history before proceeding",
            receipt=exc.receipt,
            layout=layout,
            cause=exc,
        )
    except task_authority.TaskAuthorityError as exc:
        # The lower layer can only report uncertainty after an OS-level commit
        # failure.  Re-read exact state before classifying it as committed.
        try:
            reread = _load_current_receipt(
                layout,
                rig=expected_receipt.rig,
                beads_prefix=expected_receipt.beads_prefix,
                database=expected_receipt.database,
            )
        except GasCityAuthorityError:
            reread = None
        if reread is not None and task_authority.receipt_mapping(
            reread
        ) == task_authority.receipt_mapping(expected_receipt):
            _raise_committed(
                "live authority committed while the lower transition reported uncertainty",
                receipt=reread,
                layout=layout,
                cause=exc,
            )
        raise GasCityAuthorityError(
            "live authority transition failed before a proven commit"
        ) from exc
    if task_authority.receipt_mapping(observed) != task_authority.receipt_mapping(expected_receipt):
        _raise_committed(
            "live authority returned an unexpected committed receipt",
            receipt=observed,
            layout=layout,
        )
    return observed


def _persist_transition(
    layout: AuthorityLayout,
    *,
    attempt: Mapping[str, Any],
    expected_receipt: task_authority.TaskAuthorityReceipt,
    stopped_path: Path,
    stopped_value: Mapping[str, Any],
    stopped_workers_hook: StoppedWorkersHook,
    core_operation: Callable[[], task_authority.TaskAuthorityReceipt],
) -> task_authority.TaskAuthorityReceipt:
    _invoke_stopped_hook(
        stopped_workers_hook,
        phase="before-attempt",
        path=stopped_path,
        evidence=stopped_value,
    )
    path = _attempt_path(layout, expected_receipt.generation)
    attempt_sha = _write_append_only_json(path, attempt)
    _invoke_stopped_hook(
        stopped_workers_hook,
        phase="before-transition",
        path=stopped_path,
        evidence=stopped_value,
    )
    observed = _run_core_transition(
        layout, expected_receipt=expected_receipt, operation=core_operation
    )
    try:
        _invoke_stopped_hook(
            stopped_workers_hook,
            phase="after-transition",
            path=stopped_path,
            evidence=stopped_value,
        )
        record = _history_record(
            attempt, attempt_path=path, attempt_sha256=attempt_sha, layout=layout
        )
        _write_append_only_json(_generation_path(layout, expected_receipt.generation), record)
    except GasCityAuthorityError as exc:
        _raise_committed(
            "live authority committed but append-only history is incomplete; run history recovery",
            receipt=observed,
            layout=layout,
            cause=exc,
        )
    return observed


def initialize_production_authority(
    city_root: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
    snapshot_dir: Path,
    migration_evidence_path: Path,
    recovery_evidence_path: Path,
    expected_target_directory: Path,
    stopped_workers_path: Path,
    stopped_workers_hook: StoppedWorkersHook,
    activated_at: str | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> task_authority.TaskAuthorityReceipt:
    """Create generation 1 in Taskmaster mode from reverified production evidence."""

    _validate_identity(rig=rig, beads_prefix=beads_prefix, database=database)
    layout = authority_layout(city_root, rig=rig, create=True)
    with _lifecycle_lock(layout):
        report = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        if report.current is not None or report.generation_records:
            raise GasCityAuthorityError("production authority is already initialized")
        timestamp, transition_at = _transition_time(activated_at, clock)
        source_bytes, snapshot = _validate_snapshot(layout, snapshot_dir)
        migration = _validate_migration(
            layout,
            migration_evidence_path,
            source_bytes=source_bytes,
            snapshot_record=snapshot,
            beads_prefix=beads_prefix,
            database=database,
            expected_target_directory=expected_target_directory,
        )
        recovery = _validate_recovery(
            layout,
            recovery_evidence_path,
            database=database,
            expected_head=migration["dolt_main_head"],
            expected_export_sha256=migration["canonical_export_sha256"],
            transition_at=transition_at,
        )
        baseline = {"snapshot": snapshot, "migration": migration, "recovery": recovery}
        evidence = _evidence_from_baseline(baseline)
        expected_receipt = task_authority.TaskAuthorityReceipt(
            rig=rig,
            mode=task_authority.TaskAuthorityMode.TASKMASTER,
            beads_prefix=beads_prefix,
            database=database,
            evidence=evidence,
            generation=1,
            activated_at=timestamp,
            previous_receipt_sha256=None,
        )
        stopped, stopped_value = _validate_stopped_workers(
            layout,
            stopped_workers_path,
            rig=rig,
            transition_at=transition_at,
        )
        attempt = {
            "schema_version": ATTEMPT_SCHEMA,
            "rig": rig,
            "beads_prefix": beads_prefix,
            "database": database,
            "generation": 1,
            "transition": "initialize-taskmaster",
            "created_at": timestamp,
            "receipt": task_authority.receipt_mapping(expected_receipt),
            "previous_generation_record_sha256": None,
            "baseline_evidence": baseline,
            "transition_evidence": {
                "stopped_workers": stopped,
                "rollback_recovery": None,
            },
        }
        observed = _persist_transition(
            layout,
            attempt=attempt,
            expected_receipt=expected_receipt,
            stopped_path=Path(stopped_workers_path),
            stopped_value=stopped_value,
            stopped_workers_hook=stopped_workers_hook,
            core_operation=lambda: task_authority.initialize_taskmaster_authority(
                layout.receipt_path,
                rig=rig,
                beads_prefix=beads_prefix,
                database=database,
                evidence=evidence,
                activated_at=timestamp,
            ),
        )
        verified = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        if verified.recoverable_attempt is not None or verified.generation != 1:
            _raise_committed(
                "generation 1 committed but full-chain verification did not converge",
                receipt=observed,
                layout=layout,
            )
        return observed


def _transition_from_report(
    layout: AuthorityLayout,
    *,
    report: AuthorityChainReport,
    target_mode: task_authority.TaskAuthorityMode,
    transition_name: str,
    stopped_workers_path: Path,
    stopped_workers_hook: StoppedWorkersHook,
    rollback_recovery_path: Path | None,
    activated_at: str | None,
    clock: Callable[[], dt.datetime],
) -> task_authority.TaskAuthorityReceipt:
    current = report.current
    if current is None or not report.generation_records:
        raise GasCityAuthorityError("production authority is not initialized")
    if report.recoverable_attempt is not None:
        raise GasCityAuthorityError("authority history recovery is required before transition")
    generation = current.generation + 1
    expected_name, expected_mode = _expected_generation_shape(generation)
    if transition_name != expected_name or target_mode is not expected_mode:
        raise GasCityAuthorityError("requested transition is outside the production lifecycle")
    timestamp, transition_at = _transition_time(activated_at, clock)
    if transition_at <= _parse_utc(current.activated_at, label="current authority time"):
        raise GasCityAuthorityError("authority transition time must increase")
    stopped, stopped_value = _validate_stopped_workers(
        layout,
        stopped_workers_path,
        rig=current.rig,
        transition_at=transition_at,
    )
    rollback: Mapping[str, Any] | None = None
    if generation == 3:
        if rollback_recovery_path is None:
            raise GasCityAuthorityError("Taskmaster rollback requires fresh recovery evidence")
        baseline = report.generation_records[0].get("baseline_evidence")
        migration = baseline.get("migration") if isinstance(baseline, Mapping) else None
        if not isinstance(migration, Mapping):
            raise GasCityAuthorityError("Taskmaster rollback is missing its migration baseline")
        rollback = _validate_recovery(
            layout,
            rollback_recovery_path,
            database=current.database,
            expected_head=_require_string(
                migration, "dolt_main_head", label="migration rollback baseline"
            ),
            expected_export_sha256=_require_sha256(
                migration,
                "canonical_export_sha256",
                label="migration rollback baseline",
            ),
            not_before=_parse_utc(current.activated_at, label="Beads activation time"),
            transition_at=transition_at,
            require_fresh=True,
        )
    elif rollback_recovery_path is not None:
        raise GasCityAuthorityError("Beads activation cannot bind rollback recovery evidence")
    expected_receipt = task_authority.TaskAuthorityReceipt(
        rig=current.rig,
        mode=target_mode,
        beads_prefix=current.beads_prefix,
        database=current.database,
        evidence=current.evidence,
        generation=generation,
        activated_at=timestamp,
        previous_receipt_sha256=task_authority.receipt_sha256(current),
    )
    attempt = {
        "schema_version": ATTEMPT_SCHEMA,
        "rig": current.rig,
        "beads_prefix": current.beads_prefix,
        "database": current.database,
        "generation": generation,
        "transition": transition_name,
        "created_at": timestamp,
        "receipt": task_authority.receipt_mapping(expected_receipt),
        "previous_generation_record_sha256": report.current_record_sha256,
        "baseline_evidence": report.generation_records[0]["baseline_evidence"],
        "transition_evidence": {
            "stopped_workers": stopped,
            "rollback_recovery": rollback,
        },
    }
    observed = _persist_transition(
        layout,
        attempt=attempt,
        expected_receipt=expected_receipt,
        stopped_path=Path(stopped_workers_path),
        stopped_value=stopped_value,
        stopped_workers_hook=stopped_workers_hook,
        core_operation=lambda: task_authority.transition_authority(
            layout.receipt_path,
            target_mode=target_mode,
            expected_generation=current.generation,
            expected_rig=current.rig,
            expected_beads_prefix=current.beads_prefix,
            expected_database=current.database,
            expected_evidence=current.evidence,
            activated_at=timestamp,
        ),
    )
    verified = _verify_chain_locked(
        layout,
        rig=current.rig,
        beads_prefix=current.beads_prefix,
        database=current.database,
    )
    if verified.recoverable_attempt is not None or verified.generation != generation:
        _raise_committed(
            f"generation {generation} committed but full-chain verification did not converge",
            receipt=observed,
            layout=layout,
        )
    return observed


def activate_beads_authority(
    city_root: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
    stopped_workers_path: Path,
    stopped_workers_hook: StoppedWorkersHook,
    activated_at: str | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> task_authority.TaskAuthorityReceipt:
    """Commit generation 2 and make the exactly migrated Beads store authoritative."""

    _validate_identity(rig=rig, beads_prefix=beads_prefix, database=database)
    layout = authority_layout(city_root, rig=rig)
    with _lifecycle_lock(layout):
        report = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        if report.current is None or report.current.generation != 1:
            raise GasCityAuthorityError(
                "Beads activation requires generation 1 Taskmaster authority"
            )
        return _transition_from_report(
            layout,
            report=report,
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            transition_name="activate-beads",
            stopped_workers_path=stopped_workers_path,
            stopped_workers_hook=stopped_workers_hook,
            rollback_recovery_path=None,
            activated_at=activated_at,
            clock=clock,
        )


def rollback_to_taskmaster_authority(
    city_root: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
    stopped_workers_path: Path,
    rollback_recovery_path: Path,
    stopped_workers_hook: StoppedWorkersHook,
    activated_at: str | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> task_authority.TaskAuthorityReceipt:
    """Commit generation 3 only with fresh post-activation restore evidence."""

    _validate_identity(rig=rig, beads_prefix=beads_prefix, database=database)
    layout = authority_layout(city_root, rig=rig)
    with _lifecycle_lock(layout):
        report = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        if report.current is None or report.current.generation != 2:
            raise GasCityAuthorityError("Taskmaster rollback requires generation 2 Beads authority")
        return _transition_from_report(
            layout,
            report=report,
            target_mode=task_authority.TaskAuthorityMode.TASKMASTER,
            transition_name="rollback-taskmaster",
            stopped_workers_path=stopped_workers_path,
            stopped_workers_hook=stopped_workers_hook,
            rollback_recovery_path=rollback_recovery_path,
            activated_at=activated_at,
            clock=clock,
        )


def recover_authority_history(
    city_root: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
) -> AuthorityChainReport:
    """Append the one missing history record for an already committed receipt.

    Recovery never calls the authority transition APIs.  It succeeds only when
    the live receipt is exactly one generation ahead and one immutable intent
    matches it, its predecessor, and all semantically reverified evidence.
    """

    _validate_identity(rig=rig, beads_prefix=beads_prefix, database=database)
    layout = authority_layout(city_root, rig=rig)
    with _lifecycle_lock(layout):
        report = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        envelope = report.recoverable_attempt
        if envelope is None or report.current is None:
            raise GasCityAuthorityError("there is no unambiguous committed transition to recover")
        payload = envelope.get("payload")
        path = _authority_path(layout, envelope.get("path"), label="recoverable attempt")
        if type(payload) is not dict:
            raise GasCityAuthorityError("recoverable attempt payload is invalid")
        record = _history_record(
            payload,
            attempt_path=path,
            attempt_sha256=str(envelope.get("sha256")),
            layout=layout,
        )
        try:
            _write_append_only_json(_generation_path(layout, report.current.generation), record)
        except GasCityAuthorityError as exc:
            _raise_committed(
                "live authority remains committed but history recovery failed",
                receipt=report.current,
                layout=layout,
                cause=exc,
            )
        verified = _verify_chain_locked(
            layout,
            rig=rig,
            beads_prefix=beads_prefix,
            database=database,
        )
        if verified.recoverable_attempt is not None:
            _raise_committed(
                "history recovery did not converge",
                receipt=report.current,
                layout=layout,
            )
        return verified
