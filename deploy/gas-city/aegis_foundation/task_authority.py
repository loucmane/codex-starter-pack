"""Explicit, fail-closed task-authority receipts for Gas City workers.

The presence of Taskmaster or Beads files never selects authority.  Legacy
callers retain Taskmaster authority only when ``AEGIS_TASK_AUTHORITY_FILE`` is
absent.  Once that variable is configured, the referenced receipt must be a
private, canonical, regular file and must exactly match the caller's rig and
Beads identity.

This module owns the authority receipt and the explicit external enrollment
used by attended/manual sessions. It never selects authority from task-store
presence, deletes either task store, or mutates migration evidence.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
import dataclasses
import datetime as dt
import enum
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Any


TASK_AUTHORITY_ENV = "AEGIS_TASK_AUTHORITY_FILE"
RECEIPT_SCHEMA = "aegis-task-authority/v1"
INITIAL_GENERATION = 1
MAX_RECEIPT_BYTES = 64 * 1024
MAX_ENROLLMENT_BYTES = 64 * 1024
MAX_SECRET_BYTES = 64 * 1024
MAX_BEADS_METADATA_BYTES = 16 * 1024
MAX_BEADS_CONFIG_BYTES = 64 * 1024
MANUAL_BOUNDARY_EXECUTABLE = Path("/usr/bin/bwrap")
# Workspace sandboxes may map the host root identity to the overflow UID while
# retaining an immutable, non-user-owned /usr tree.  Production normally sees 0.
SYSTEM_ROOT_UIDS = frozenset({0, 65534})

ENROLLMENT_POINTER_SCHEMA = "aegis-authority-enrollment-pointer/v1"
ENROLLMENT_BINDING_SCHEMA = "aegis-authority-enrollment/v1"
ENROLLMENT_POINTER_NAME = "aegis-authority-enrollment.json"
ENROLLMENT_BINDING_RELATIVE_ROOT = Path("runtime/authority/enrollments")
REPOSITORY_KEY_DOMAIN = b"aegis-authority-repository/v1\0"

TASK_AUTHORITY_RUNTIME_ENV = "AEGIS_TASK_AUTHORITY_RUNTIME_FILE"
TASK_AUTHORITY_RUNTIME_SHA256_ENV = "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256"
BD_EXECUTABLE_ENV = "AEGIS_BD_EXECUTABLE"
BD_SHA256_ENV = "AEGIS_BD_SHA256"

_BOUND_ENVIRONMENT_KEYS = (
    TASK_AUTHORITY_ENV,
    TASK_AUTHORITY_RUNTIME_ENV,
    TASK_AUTHORITY_RUNTIME_SHA256_ENV,
    BD_EXECUTABLE_ENV,
    BD_SHA256_ENV,
    "GC_RIG",
    "GC_RIG_ROOT",
    "GC_BEADS_PREFIX",
    "GC_DOLT_HOST",
    "GC_DOLT_PORT",
    "GC_DOLT_USER",
    "GC_DOLT_DATABASE",
    "BEADS_DOLT_SERVER_HOST",
    "BEADS_DOLT_SERVER_PORT",
    "BEADS_DOLT_SERVER_USER",
    "BEADS_DOLT_SERVER_DATABASE",
    "BEADS_DIR",
)

SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SAFE_RIG_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
SAFE_BEADS_PREFIX_RE = re.compile(r"[a-z][a-z0-9-]{0,62}\Z")
SAFE_BEADS_DATABASE_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
SAFE_BEADS_PROJECT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
UTC_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?Z\Z"
)

_RECEIPT_KEYS = frozenset(
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

_ENROLLMENT_POINTER_KEYS = frozenset(
    {
        "schema_version",
        "repository_key",
        "city_root",
        "task_authority_runtime",
        "task_authority_runtime_sha256",
    }
)

_ENROLLMENT_BINDING_KEYS = frozenset(
    {
        "schema_version",
        "repository_key",
        "repository_root",
        "git_common_dir",
        "city_root",
        "rig",
        "rig_root",
        "beads_prefix",
        "beads_dir",
        "database",
        "dolt_host",
        "dolt_port",
        "dolt_user",
        "authority_receipt",
        "authority_generation",
        "authority_receipt_sha256",
        "task_authority_runtime",
        "task_authority_runtime_sha256",
        "bd_executable",
        "bd_sha256",
        "password_file",
        "claude_executable",
        "claude_sha256",
        "claude_config",
        "claude_config_sha256",
        "codex_executable",
        "codex_sha256",
        "activated_at",
    }
)

_BEADS_METADATA_KEYS = frozenset(
    {
        "backend",
        "database",
        "dolt_database",
        "dolt_mode",
        "project_id",
    }
)
_GAS_CITY_REQUIRED_CUSTOM_TYPES = (
    "molecule,convoy,message,event,gate,merge-request,agent,role,rig,session,"
    "spec,convergence,step"
)
_BEADS_CANONICAL_CONFIG = (
    b"issue_prefix: ags\n"
    b"issue-prefix: ags\n"
    b"dolt.auto-start: false\n"
    b"dolt:\n"
    b"  disable-event-flush: true\n"
    b"export.auto: false\n"
    b"backup.enabled: false\n"
    b"gc.endpoint_origin: explicit\n"
    b"gc.endpoint_status: verified\n"
    b"dolt.host: 127.0.0.1\n"
    b"dolt.port: 33071\n"
    b"dolt.user: aegis_beads\n"
    + f"types.custom: {_GAS_CITY_REQUIRED_CUSTOM_TYPES}\n".encode("ascii")
)


class TaskAuthorityError(RuntimeError):
    """Authority cannot be selected or transitioned without guessing."""


class TaskAuthorityCommittedError(TaskAuthorityError):
    """A receipt was committed but its directory durability is uncertain."""

    def __init__(self, receipt: TaskAuthorityReceipt, path: Path) -> None:
        self.receipt = receipt
        self.path = path
        super().__init__(
            "authority receipt generation "
            f"{receipt.generation} was committed at {path}, but directory sync failed"
        )


class TaskAuthorityMode(str, enum.Enum):
    """The only supported authoritative task stores."""

    TASKMASTER = "taskmaster"
    BEADS = "beads"


@dataclasses.dataclass(frozen=True)
class TaskAuthorityEvidence:
    """Immutable digests for the evidence required to reverse a cutover."""

    taskmaster_snapshot_sha256: str
    migration_report_sha256: str
    backup_restore_report_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("taskmaster_snapshot_sha256", self.taskmaster_snapshot_sha256),
            ("migration_report_sha256", self.migration_report_sha256),
            ("backup_restore_report_sha256", self.backup_restore_report_sha256),
        ):
            if type(value) is not str or not SHA256_RE.fullmatch(value):
                raise TaskAuthorityError(f"{label} must be a lowercase SHA-256 digest")


@dataclasses.dataclass(frozen=True)
class TaskAuthorityReceipt:
    """One validated generation of explicit task authority."""

    rig: str
    mode: TaskAuthorityMode
    beads_prefix: str
    database: str
    evidence: TaskAuthorityEvidence
    generation: int
    activated_at: str
    previous_receipt_sha256: str | None
    schema_version: str = RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != RECEIPT_SCHEMA:
            raise TaskAuthorityError(f"schema_version must be {RECEIPT_SCHEMA!r}")
        _validate_safe_identity(self.rig, self.beads_prefix, self.database)
        if not isinstance(self.mode, TaskAuthorityMode):
            raise TaskAuthorityError("mode must be taskmaster or beads")
        if not isinstance(self.evidence, TaskAuthorityEvidence):
            raise TaskAuthorityError("evidence must be TaskAuthorityEvidence")
        if type(self.generation) is not int or self.generation < INITIAL_GENERATION:
            raise TaskAuthorityError("generation must be an integer greater than or equal to 1")
        _parse_utc_timestamp(self.activated_at)
        if self.generation == INITIAL_GENERATION:
            if self.previous_receipt_sha256 is not None:
                raise TaskAuthorityError("generation 1 must not name a previous receipt")
        elif (
            type(self.previous_receipt_sha256) is not str
            or not SHA256_RE.fullmatch(self.previous_receipt_sha256)
        ):
            raise TaskAuthorityError(
                "generation greater than 1 must name the previous receipt SHA-256"
            )


@dataclasses.dataclass(frozen=True)
class LoadedTaskAuthority:
    """Selected authority plus whether it came from an explicit receipt."""

    mode: TaskAuthorityMode
    explicit: bool
    receipt: TaskAuthorityReceipt | None
    receipt_path: Path | None

    def __post_init__(self) -> None:
        if self.explicit != (self.receipt is not None and self.receipt_path is not None):
            raise TaskAuthorityError("explicit authority requires both a receipt and its path")
        if self.receipt is not None and self.receipt.mode is not self.mode:
            raise TaskAuthorityError("loaded authority mode does not match its receipt")
        if not self.explicit and self.mode is not TaskAuthorityMode.TASKMASTER:
            raise TaskAuthorityError("implicit legacy authority can only be Taskmaster")


@dataclasses.dataclass(frozen=True)
class RepositoryIdentity:
    """Stable identity shared by a primary checkout and all linked worktrees."""

    repository_root: Path
    git_common_dir: Path
    repository_key: str
    enrollment_pointer: Path


@dataclasses.dataclass(frozen=True)
class ProjectAuthorityEnrollment:
    """Validated, secret-free manual-session binding for one enrolled project."""

    identity: RepositoryIdentity
    city_root: Path
    pointer_path: Path
    binding_path: Path
    rig: str
    rig_root: Path
    beads_prefix: str
    beads_dir: Path
    database: str
    dolt_host: str
    dolt_port: int
    dolt_user: str
    authority_receipt: Path
    authority_generation: int
    authority_receipt_sha256: str
    task_authority_runtime: Path
    task_authority_runtime_sha256: str
    bd_executable: Path
    bd_sha256: str
    password_file: Path
    claude_executable: Path
    claude_sha256: str
    claude_config: Path
    claude_config_sha256: str
    codex_executable: Path
    codex_sha256: str
    activated_at: str

    def expected_environment(self) -> dict[str, str]:
        """Return every non-secret environment value fixed by the enrollment."""

        port = str(self.dolt_port)
        return {
            TASK_AUTHORITY_ENV: str(self.authority_receipt),
            TASK_AUTHORITY_RUNTIME_ENV: str(self.task_authority_runtime),
            TASK_AUTHORITY_RUNTIME_SHA256_ENV: self.task_authority_runtime_sha256,
            BD_EXECUTABLE_ENV: str(self.bd_executable),
            BD_SHA256_ENV: self.bd_sha256,
            "GC_RIG": self.rig,
            "GC_RIG_ROOT": str(self.rig_root),
            "GC_BEADS_PREFIX": self.beads_prefix,
            "GC_DOLT_HOST": self.dolt_host,
            "GC_DOLT_PORT": port,
            "GC_DOLT_USER": self.dolt_user,
            "GC_DOLT_DATABASE": self.database,
            "BEADS_DOLT_SERVER_HOST": self.dolt_host,
            "BEADS_DOLT_SERVER_PORT": port,
            "BEADS_DOLT_SERVER_USER": self.dolt_user,
            "BEADS_DOLT_SERVER_DATABASE": self.database,
            "BEADS_DIR": str(self.beads_dir),
        }


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TaskAuthorityError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise TaskAuthorityError(f"non-finite JSON number is not allowed: {value}")


def _parse_json(content: bytes, *, label: str) -> Any:
    if not content:
        raise TaskAuthorityError(f"{label} is empty")
    if len(content) > MAX_RECEIPT_BYTES:
        raise TaskAuthorityError(f"{label} exceeds {MAX_RECEIPT_BYTES} bytes")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskAuthorityError(f"{label} is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (ValueError, RecursionError) as exc:
        raise TaskAuthorityError(f"{label} is not valid JSON: {exc}") from exc


def _validate_safe_identity(rig: str, beads_prefix: str, database: str) -> None:
    if type(rig) is not str or not SAFE_RIG_RE.fullmatch(rig):
        raise TaskAuthorityError("rig must match [a-z][a-z0-9_-]{0,62}")
    if type(beads_prefix) is not str or not SAFE_BEADS_PREFIX_RE.fullmatch(beads_prefix):
        raise TaskAuthorityError("beads_prefix must match [a-z][a-z0-9-]{0,62}")
    if type(database) is not str or not SAFE_BEADS_DATABASE_RE.fullmatch(database):
        raise TaskAuthorityError("database must match [a-z][a-z0-9_-]{0,62}")


def _parse_utc_timestamp(value: str) -> dt.datetime:
    if type(value) is not str or not UTC_TIMESTAMP_RE.fullmatch(value):
        raise TaskAuthorityError("activated_at must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TaskAuthorityError("activated_at is not a valid UTC timestamp") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise TaskAuthorityError("activated_at must use UTC")
    return parsed


def _mode_from_value(value: Any) -> TaskAuthorityMode:
    if type(value) is not str:
        raise TaskAuthorityError("mode must be taskmaster or beads")
    try:
        return TaskAuthorityMode(value)
    except ValueError as exc:
        raise TaskAuthorityError("mode must be taskmaster or beads") from exc


def _require_string(value: Mapping[str, Any], key: str) -> str:
    result = value[key]
    if type(result) is not str:
        raise TaskAuthorityError(f"{key} must be a string")
    return result


def _receipt_from_mapping(value: Any) -> TaskAuthorityReceipt:
    if not isinstance(value, dict):
        raise TaskAuthorityError("authority receipt must contain one JSON object")
    keys = frozenset(value)
    if keys != _RECEIPT_KEYS:
        missing = sorted(_RECEIPT_KEYS - keys)
        extra = sorted(keys - _RECEIPT_KEYS)
        raise TaskAuthorityError(
            f"authority receipt fields must be exact; missing={missing}, extra={extra}"
        )
    generation = value["generation"]
    if type(generation) is not int:
        raise TaskAuthorityError("generation must be an integer greater than or equal to 1")
    previous_digest = value["previous_receipt_sha256"]
    if previous_digest is not None and type(previous_digest) is not str:
        raise TaskAuthorityError("previous_receipt_sha256 must be a string or null")
    evidence = TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=_require_string(
            value, "taskmaster_snapshot_sha256"
        ),
        migration_report_sha256=_require_string(value, "migration_report_sha256"),
        backup_restore_report_sha256=_require_string(
            value, "backup_restore_report_sha256"
        ),
    )
    return TaskAuthorityReceipt(
        schema_version=_require_string(value, "schema_version"),
        rig=_require_string(value, "rig"),
        mode=_mode_from_value(value["mode"]),
        beads_prefix=_require_string(value, "beads_prefix"),
        database=_require_string(value, "database"),
        evidence=evidence,
        generation=generation,
        activated_at=_require_string(value, "activated_at"),
        previous_receipt_sha256=previous_digest,
    )


def receipt_mapping(receipt: TaskAuthorityReceipt) -> dict[str, Any]:
    """Return the exact public JSON projection for a validated receipt."""

    if not isinstance(receipt, TaskAuthorityReceipt):
        raise TaskAuthorityError("receipt must be TaskAuthorityReceipt")
    return {
        "schema_version": receipt.schema_version,
        "rig": receipt.rig,
        "mode": receipt.mode.value,
        "beads_prefix": receipt.beads_prefix,
        "database": receipt.database,
        "taskmaster_snapshot_sha256": receipt.evidence.taskmaster_snapshot_sha256,
        "migration_report_sha256": receipt.evidence.migration_report_sha256,
        "backup_restore_report_sha256": receipt.evidence.backup_restore_report_sha256,
        "generation": receipt.generation,
        "activated_at": receipt.activated_at,
        "previous_receipt_sha256": receipt.previous_receipt_sha256,
    }


def receipt_bytes(receipt: TaskAuthorityReceipt) -> bytes:
    """Serialize a receipt in the one accepted canonical representation."""

    return (
        json.dumps(
            receipt_mapping(receipt),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def receipt_sha256(receipt: TaskAuthorityReceipt) -> str:
    """Return the canonical SHA-256 used to chain receipt generations."""

    return hashlib.sha256(receipt_bytes(receipt)).hexdigest()


def _absolute_path(path: Path, *, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise TaskAuthorityError(f"{label} must be an absolute path")
    if ".." in candidate.parts:
        raise TaskAuthorityError(f"{label} must not contain '..'")
    if "\0" in os.fspath(candidate):
        raise TaskAuthorityError(f"{label} must not contain a NUL byte")
    return candidate


def _current_uid() -> int:
    try:
        return os.geteuid()
    except AttributeError as exc:  # pragma: no cover - Gas City workers are POSIX.
        raise TaskAuthorityError("task-authority receipts require a POSIX runtime") from exc


@contextmanager
def _open_parent_directory(path: Path, *, create: bool) -> Iterator[tuple[int, str]]:
    """Open an absolute path's parent without following any symlink component."""

    receipt_path = _absolute_path(path, label="authority receipt path")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - Gas City workers are Linux.
        raise TaskAuthorityError("this runtime cannot safely walk an authority path")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    flags = os.O_RDONLY | os.O_CLOEXEC | no_follow | directory_flag
    try:
        descriptor = os.open(receipt_path.anchor, flags)
    except (OSError, ValueError) as exc:
        raise TaskAuthorityError("cannot open the authority path root") from exc
    try:
        for component in receipt_path.parts[1:-1]:
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                except OSError as exc:
                    raise TaskAuthorityError(
                        f"cannot create authority path component: {component}"
                    ) from exc
            try:
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError as exc:
                raise TaskAuthorityError(
                    f"authority receipt parent does not exist: {receipt_path.parent}"
                ) from exc
            except (OSError, ValueError) as exc:
                raise TaskAuthorityError(
                    "authority path must contain only real directories; "
                    f"refusing component {component!r}"
                ) from exc
            os.close(descriptor)
            descriptor = next_descriptor
        yield descriptor, receipt_path.name
    finally:
        os.close(descriptor)


def _read_private_receipt_at(parent_fd: int, name: str, display_path: Path) -> bytes:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - Gas City workers are Linux.
        raise TaskAuthorityError("this runtime cannot safely open a non-symlink receipt")
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | no_follow,
            dir_fd=parent_fd,
        )
    except FileNotFoundError as exc:
        raise TaskAuthorityError(f"authority receipt does not exist: {display_path}") from exc
    except (OSError, ValueError) as exc:
        raise TaskAuthorityError(
            f"authority receipt must be a regular non-symlink file: {display_path}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise TaskAuthorityError(
                f"authority receipt must be a regular non-symlink file: {display_path}"
            )
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise TaskAuthorityError("authority receipt permissions must be exactly 0600")
        if before.st_uid != _current_uid():
            raise TaskAuthorityError("authority receipt must be owned by the current user")
        if before.st_nlink != 1:
            raise TaskAuthorityError("authority receipt must have exactly one hard link")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(MAX_RECEIPT_BYTES + 1)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after or len(content) != after.st_size:
            raise TaskAuthorityError("authority receipt changed while it was being read")
        if len(content) > MAX_RECEIPT_BYTES:
            raise TaskAuthorityError(f"authority receipt exceeds {MAX_RECEIPT_BYTES} bytes")
        return content
    except OSError as exc:
        raise TaskAuthorityError(f"cannot read authority receipt: {display_path}") from exc
    finally:
        os.close(descriptor)


def _read_private_receipt(path: Path) -> bytes:
    receipt_path = _absolute_path(path, label="authority receipt path")
    with _open_parent_directory(receipt_path, create=False) as (parent_fd, name):
        return _read_private_receipt_at(parent_fd, name, receipt_path)


def _read_secure_regular_file(
    path: Path,
    *,
    label: str,
    allowed_modes: frozenset[int],
    maximum_bytes: int,
    require_owner: bool = True,
) -> bytes:
    """Read one bounded file without accepting aliases or replacement races."""

    configured = _absolute_path(path, label=label)
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production is Linux.
        raise TaskAuthorityError(f"this runtime cannot safely open {label}")
    with _open_parent_directory(configured, create=False) as (parent_fd, name):
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | no_follow,
                dir_fd=parent_fd,
            )
        except (OSError, ValueError) as exc:
            raise TaskAuthorityError(
                f"{label} must be a regular non-symlink file: {configured}"
            ) from exc
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise TaskAuthorityError(f"{label} must be a regular file")
            if stat.S_IMODE(before.st_mode) not in allowed_modes:
                rendered = ", ".join(f"{mode:04o}" for mode in sorted(allowed_modes))
                raise TaskAuthorityError(f"{label} permissions must be one of: {rendered}")
            if require_owner and before.st_uid != _current_uid():
                raise TaskAuthorityError(f"{label} must be owned by the current user")
            if before.st_nlink != 1:
                raise TaskAuthorityError(f"{label} must have exactly one hard link")
            with os.fdopen(os.dup(descriptor), "rb") as handle:
                content = handle.read(maximum_bytes + 1)
            after = os.fstat(descriptor)
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_mode,
                before.st_uid,
                before.st_nlink,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_mode,
                after.st_uid,
                after.st_nlink,
            )
            if identity_before != identity_after or len(content) != after.st_size:
                raise TaskAuthorityError(f"{label} changed while it was being read")
            if len(content) > maximum_bytes:
                raise TaskAuthorityError(f"{label} exceeds {maximum_bytes} bytes")
            return content
        except OSError as exc:
            raise TaskAuthorityError(f"cannot read {label}: {configured}") from exc
        finally:
            os.close(descriptor)


def _inspect_secure_regular_file(
    path: Path,
    *,
    label: str,
    allowed_modes: frozenset[int],
    maximum_bytes: int,
) -> os.stat_result:
    """Inspect a secret without putting its bytes in a validation process."""

    configured = _absolute_path(path, label=label)
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production is Linux.
        raise TaskAuthorityError(f"this runtime cannot safely inspect {label}")
    with _open_parent_directory(configured, create=False) as (parent_fd, name):
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | no_follow,
                dir_fd=parent_fd,
            )
        except (OSError, ValueError) as exc:
            raise TaskAuthorityError(
                f"{label} must be a regular non-symlink file: {configured}"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise TaskAuthorityError(f"{label} must be a regular file")
            if stat.S_IMODE(metadata.st_mode) not in allowed_modes:
                raise TaskAuthorityError(f"{label} permissions must be 0400 or 0600")
            if metadata.st_uid != _current_uid():
                raise TaskAuthorityError(f"{label} must be owned by the current user")
            if metadata.st_nlink != 1:
                raise TaskAuthorityError(f"{label} must have exactly one hard link")
            if metadata.st_size < 1 or metadata.st_size > maximum_bytes:
                raise TaskAuthorityError(f"{label} has an unsafe size")
            return metadata
        finally:
            os.close(descriptor)


def _strict_json_object(
    content: bytes,
    *,
    label: str,
    keys: frozenset[str],
    schema: str,
) -> dict[str, Any]:
    value = _parse_json(content, label=label)
    if not isinstance(value, dict):
        raise TaskAuthorityError(f"{label} must contain one JSON object")
    actual_keys = frozenset(value)
    if actual_keys != keys:
        raise TaskAuthorityError(
            f"{label} fields must be exact; "
            f"missing={sorted(keys - actual_keys)}, extra={sorted(actual_keys - keys)}"
        )
    if value.get("schema_version") != schema:
        raise TaskAuthorityError(f"{label} schema_version must be {schema!r}")
    canonical = (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if canonical != content:
        raise TaskAuthorityError(f"{label} is not canonical JSON")
    return value


def _read_git_metadata_file(path: Path, *, label: str) -> str:
    content = _read_secure_regular_file(
        path,
        label=label,
        allowed_modes=frozenset({0o600, 0o640, 0o644}),
        maximum_bytes=16 * 1024,
    )
    try:
        result = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskAuthorityError(f"{label} is not valid UTF-8") from exc
    if "\0" in result:
        raise TaskAuthorityError(f"{label} contains a NUL byte")
    return result.strip()


def repository_identity(project_root: Path) -> RepositoryIdentity:
    """Derive one canonical key from Git common metadata, not task-store presence."""

    requested = _absolute_path(Path(project_root), label="project root")
    try:
        resolved_root = requested.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError(f"cannot resolve project root: {requested}") from exc
    if not resolved_root.is_dir():
        raise TaskAuthorityError("project root must be a directory")
    dot_git = resolved_root / ".git"
    try:
        dot_git_metadata = dot_git.lstat()
    except FileNotFoundError as exc:
        raise TaskAuthorityError("project root has no Git metadata") from exc
    if stat.S_ISDIR(dot_git_metadata.st_mode):
        common_dir = dot_git
    elif stat.S_ISREG(dot_git_metadata.st_mode):
        gitdir_line = _read_git_metadata_file(dot_git, label="linked-worktree .git file")
        if not gitdir_line.startswith("gitdir: ") or "\n" in gitdir_line:
            raise TaskAuthorityError("linked-worktree .git file has an invalid shape")
        raw_gitdir = Path(gitdir_line[len("gitdir: ") :])
        gitdir = raw_gitdir if raw_gitdir.is_absolute() else resolved_root / raw_gitdir
        try:
            gitdir = gitdir.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise TaskAuthorityError("cannot resolve linked-worktree Git directory") from exc
        commondir_text = _read_git_metadata_file(
            gitdir / "commondir", label="linked-worktree commondir file"
        )
        raw_common = Path(commondir_text)
        candidate = raw_common if raw_common.is_absolute() else gitdir / raw_common
        try:
            common_dir = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise TaskAuthorityError("cannot resolve linked-worktree Git common directory") from exc
    else:
        raise TaskAuthorityError("project .git must be one real directory or regular file")
    try:
        common_metadata = common_dir.lstat()
    except OSError as exc:
        raise TaskAuthorityError("cannot inspect Git common directory") from exc
    if not stat.S_ISDIR(common_metadata.st_mode) or common_dir.is_symlink():
        raise TaskAuthorityError("Git common directory must be one real directory")
    if common_dir.name != ".git":
        raise TaskAuthorityError("Aegis enrollment requires a non-bare Git common directory")
    repository_root = common_dir.parent
    try:
        primary_git = (repository_root / ".git").resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError("cannot verify primary repository Git directory") from exc
    if primary_git != common_dir:
        raise TaskAuthorityError("Git common directory does not identify one primary checkout")
    digest = hashlib.sha256()
    digest.update(REPOSITORY_KEY_DOMAIN)
    digest.update(os.fsencode(repository_root))
    digest.update(b"\0")
    digest.update(os.fsencode(common_dir))
    repository_key = digest.hexdigest()
    return RepositoryIdentity(
        repository_root=repository_root,
        git_common_dir=common_dir,
        repository_key=repository_key,
        enrollment_pointer=common_dir / ENROLLMENT_POINTER_NAME,
    )


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if type(item) is not str or not item:
        raise TaskAuthorityError(f"{key} must be a non-empty string")
    return item


def _relative_city_path(city_root: Path, raw: Any, *, label: str) -> Path:
    if type(raw) is not str or not raw:
        raise TaskAuthorityError(f"{label} must be a non-empty relative path")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise TaskAuthorityError(f"{label} must be a normalized city-relative path")
    candidate = city_root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError(f"cannot resolve {label}: {candidate}") from exc
    if resolved != candidate:
        raise TaskAuthorityError(f"{label} must not traverse a symlink")
    try:
        resolved.relative_to(city_root)
    except ValueError as exc:  # pragma: no cover - guarded by relative path check.
        raise TaskAuthorityError(f"{label} escapes the city root") from exc
    return resolved


def _secure_city_root(raw: Any) -> Path:
    if type(raw) is not str or not raw:
        raise TaskAuthorityError("city_root must be a non-empty absolute path")
    configured = _absolute_path(Path(raw), label="city_root")
    try:
        resolved = configured.resolve(strict=True)
        metadata = configured.lstat()
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError(f"cannot resolve city_root: {configured}") from exc
    if resolved != configured or not stat.S_ISDIR(metadata.st_mode):
        raise TaskAuthorityError("city_root must be one real non-symlink directory")
    if metadata.st_uid != _current_uid():
        raise TaskAuthorityError("city_root must be owned by the current user")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise TaskAuthorityError("city_root permissions must be exactly 0700")
    return resolved


def _require_private_directory(path: Path, *, label: str) -> None:
    configured = _absolute_path(path, label=label)
    try:
        resolved = configured.resolve(strict=True)
        metadata = configured.lstat()
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError(f"cannot inspect {label}: {configured}") from exc
    if resolved != configured or not stat.S_ISDIR(metadata.st_mode):
        raise TaskAuthorityError(f"{label} must be one real non-symlink directory")
    if metadata.st_uid != _current_uid() or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise TaskAuthorityError(f"{label} must be owner-controlled mode 0700")


def _validate_primary_beads_metadata(beads_dir: Path) -> str:
    """Prove the primary checkout names only the enrolled Aegis Dolt store."""

    _require_private_directory(beads_dir, label="primary repository Beads directory")
    legacy_environment = beads_dir / ".env"
    try:
        legacy_environment.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise TaskAuthorityError(
            f"cannot inspect retained Beads environment file: {legacy_environment}"
        ) from exc
    else:
        raise TaskAuthorityError(
            "primary repository must not retain .beads/.env; "
            "Dolt credentials and endpoints are launcher-owned"
        )

    content = _read_secure_regular_file(
        beads_dir / "metadata.json",
        label="primary repository Beads metadata",
        allowed_modes=frozenset({0o600}),
        maximum_bytes=MAX_BEADS_METADATA_BYTES,
    )
    value = _parse_json(content, label="primary repository Beads metadata")
    if not isinstance(value, dict):
        raise TaskAuthorityError(
            "primary repository Beads metadata must contain one JSON object"
        )
    actual_keys = frozenset(value)
    if actual_keys != _BEADS_METADATA_KEYS:
        raise TaskAuthorityError(
            "primary repository Beads metadata fields must be exact; "
            f"missing={sorted(_BEADS_METADATA_KEYS - actual_keys)}, "
            f"extra={sorted(actual_keys - _BEADS_METADATA_KEYS)}"
        )
    expected = {
        "backend": "dolt",
        "database": "dolt",
        "dolt_database": "aegis_beads",
        "dolt_mode": "server",
    }
    mismatched = [key for key, wanted in expected.items() if value.get(key) != wanted]
    if mismatched:
        raise TaskAuthorityError(
            "primary repository Beads metadata does not name the enrolled "
            f"loopback Aegis Dolt store: {mismatched}"
        )
    project_id = value.get("project_id")
    if type(project_id) is not str or not SAFE_BEADS_PROJECT_ID_RE.fullmatch(project_id):
        raise TaskAuthorityError(
            "primary repository Beads metadata project_id must be a canonical "
            "lowercase UUIDv4"
        )
    config = _read_secure_regular_file(
        beads_dir / "config.yaml",
        label="primary repository Beads config",
        allowed_modes=frozenset({0o600}),
        maximum_bytes=MAX_BEADS_CONFIG_BYTES,
    )
    if config != _BEADS_CANONICAL_CONFIG:
        raise TaskAuthorityError(
            "primary repository Beads config does not name the exact verified "
            "loopback Aegis Dolt endpoint"
        )
    port_file = beads_dir / "dolt-server.port"
    if port_file.exists() or port_file.is_symlink():
        raise TaskAuthorityError(
            "primary repository external Beads binding retained a managed Dolt port mirror"
        )
    return project_id


def load_project_enrollment(project_root: Path) -> ProjectAuthorityEnrollment | None:
    """Load the explicit cutover marker and its external, identity-keyed binding."""

    requested = _absolute_path(Path(project_root), label="project root")
    try:
        (requested / ".git").lstat()
    except FileNotFoundError:
        return None
    identity = repository_identity(project_root)
    try:
        identity.enrollment_pointer.lstat()
    except FileNotFoundError:
        return None
    pointer_content = _read_secure_regular_file(
        identity.enrollment_pointer,
        label="authority enrollment pointer",
        allowed_modes=frozenset({0o600}),
        maximum_bytes=MAX_ENROLLMENT_BYTES,
    )
    pointer = _strict_json_object(
        pointer_content,
        label="authority enrollment pointer",
        keys=_ENROLLMENT_POINTER_KEYS,
        schema=ENROLLMENT_POINTER_SCHEMA,
    )
    repository_key = _required_string(pointer, "repository_key")
    if repository_key != identity.repository_key:
        raise TaskAuthorityError("authority enrollment pointer repository identity mismatch")
    city_root = _secure_city_root(pointer.get("city_root"))
    for directory, label in (
        (city_root / "runtime", "city runtime directory"),
        (city_root / "runtime" / "authority", "authority runtime directory"),
        (
            city_root / ENROLLMENT_BINDING_RELATIVE_ROOT,
            "authority enrollment directory",
        ),
        (city_root / "runtime" / "secrets", "city secrets directory"),
    ):
        _require_private_directory(directory, label=label)
    runtime_relative = _required_string(pointer, "task_authority_runtime")
    runtime_digest = _required_string(pointer, "task_authority_runtime_sha256")
    if not SHA256_RE.fullmatch(runtime_digest):
        raise TaskAuthorityError("task_authority_runtime_sha256 must be a lowercase SHA-256")
    binding_path = city_root / ENROLLMENT_BINDING_RELATIVE_ROOT / f"{repository_key}.json"
    binding_content = _read_secure_regular_file(
        binding_path,
        label="authority enrollment binding",
        allowed_modes=frozenset({0o600}),
        maximum_bytes=MAX_ENROLLMENT_BYTES,
    )
    binding = _strict_json_object(
        binding_content,
        label="authority enrollment binding",
        keys=_ENROLLMENT_BINDING_KEYS,
        schema=ENROLLMENT_BINDING_SCHEMA,
    )
    exact_strings = {
        "repository_key": repository_key,
        "repository_root": str(identity.repository_root),
        "git_common_dir": str(identity.git_common_dir),
        "city_root": str(city_root),
        "rig": "aegis",
        "rig_root": str(identity.repository_root),
        "beads_prefix": "ags",
        "beads_dir": str(identity.repository_root / ".beads"),
        "database": "aegis_beads",
        "dolt_host": "127.0.0.1",
        "dolt_user": "aegis_beads",
        "task_authority_runtime": runtime_relative,
        "task_authority_runtime_sha256": runtime_digest,
    }
    for key, expected in exact_strings.items():
        if binding.get(key) != expected:
            raise TaskAuthorityError(
                f"authority enrollment binding mismatch for {key}: expected {expected!r}"
            )
    if binding.get("dolt_port") != 33071:
        raise TaskAuthorityError("authority enrollment requires loopback Dolt port 33071")
    if binding.get("authority_generation") != 2:
        raise TaskAuthorityError("active authority enrollment requires receipt generation 2")
    beads_dir = identity.repository_root / ".beads"
    _validate_primary_beads_metadata(beads_dir)
    activated_at = _required_string(binding, "activated_at")
    _parse_utc_timestamp(activated_at)
    digest_fields = (
        "authority_receipt_sha256",
        "task_authority_runtime_sha256",
        "bd_sha256",
        "claude_sha256",
        "claude_config_sha256",
        "codex_sha256",
    )
    for key in digest_fields:
        if not SHA256_RE.fullmatch(_required_string(binding, key)):
            raise TaskAuthorityError(f"{key} must be a lowercase SHA-256")
    authority_receipt = _relative_city_path(
        city_root, binding.get("authority_receipt"), label="authority_receipt"
    )
    task_runtime = _relative_city_path(
        city_root, binding.get("task_authority_runtime"), label="task_authority_runtime"
    )
    bd_executable = _relative_city_path(
        city_root, binding.get("bd_executable"), label="bd_executable"
    )
    password_file = _relative_city_path(
        city_root, binding.get("password_file"), label="password_file"
    )
    claude_executable = _relative_city_path(
        city_root, binding.get("claude_executable"), label="claude_executable"
    )
    claude_config = _relative_city_path(
        city_root, binding.get("claude_config"), label="claude_config"
    )
    codex_executable = _relative_city_path(
        city_root, binding.get("codex_executable"), label="codex_executable"
    )
    _inspect_secure_regular_file(
        password_file,
        label="Aegis Dolt application password",
        allowed_modes=frozenset({0o400, 0o600}),
        maximum_bytes=MAX_SECRET_BYTES,
    )
    return ProjectAuthorityEnrollment(
        identity=identity,
        city_root=city_root,
        pointer_path=identity.enrollment_pointer,
        binding_path=binding_path,
        rig="aegis",
        rig_root=identity.repository_root,
        beads_prefix="ags",
        beads_dir=beads_dir,
        database="aegis_beads",
        dolt_host="127.0.0.1",
        dolt_port=33071,
        dolt_user="aegis_beads",
        authority_receipt=authority_receipt,
        authority_generation=2,
        authority_receipt_sha256=_required_string(binding, "authority_receipt_sha256"),
        task_authority_runtime=task_runtime,
        task_authority_runtime_sha256=runtime_digest,
        bd_executable=bd_executable,
        bd_sha256=_required_string(binding, "bd_sha256"),
        password_file=password_file,
        claude_executable=claude_executable,
        claude_sha256=_required_string(binding, "claude_sha256"),
        claude_config=claude_config,
        claude_config_sha256=_required_string(binding, "claude_config_sha256"),
        codex_executable=codex_executable,
        codex_sha256=_required_string(binding, "codex_sha256"),
        activated_at=activated_at,
    )


def validate_project_authority_environment(
    project_root: Path,
    environment: Mapping[str, str] | None = None,
) -> ProjectAuthorityEnrollment | None:
    """Fail closed when an enrolled project lacks its complete exact binding."""

    env = os.environ if environment is None else environment
    enrollment = load_project_enrollment(project_root)
    if enrollment is None:
        return None
    expected = enrollment.expected_environment()
    missing = [key for key in _BOUND_ENVIRONMENT_KEYS if key not in env or not env[key]]
    if missing:
        raise TaskAuthorityError(
            "externally managed project requires the complete authority environment; "
            f"missing={missing}. Launch through aegis-claude or aegis-codex."
        )
    mismatched = [key for key, value in expected.items() if env.get(key) != value]
    if mismatched:
        raise TaskAuthorityError(
            "externally managed project authority environment mismatch: "
            f"{mismatched}"
        )
    receipt = load_authority_receipt(
        enrollment.authority_receipt,
        expected_rig=enrollment.rig,
        expected_beads_prefix=enrollment.beads_prefix,
        expected_database=enrollment.database,
    )
    if receipt.mode is not TaskAuthorityMode.BEADS or receipt.generation != 2:
        raise TaskAuthorityError(
            "active project enrollment requires the live generation-2 Beads receipt"
        )
    if receipt_sha256(receipt) != enrollment.authority_receipt_sha256:
        raise TaskAuthorityError("authority enrollment receipt digest mismatch")
    return enrollment


def _load_receipt_bytes(content: bytes) -> TaskAuthorityReceipt:
    receipt = _receipt_from_mapping(_parse_json(content, label="authority receipt"))
    if content != receipt_bytes(receipt):
        raise TaskAuthorityError("authority receipt is not canonical JSON")
    return receipt


def _require_expected_identity(
    receipt: TaskAuthorityReceipt,
    *,
    expected_rig: str,
    expected_beads_prefix: str,
    expected_database: str,
) -> None:
    _validate_safe_identity(expected_rig, expected_beads_prefix, expected_database)
    if receipt.rig != expected_rig:
        raise TaskAuthorityError(
            f"authority receipt rig mismatch: expected {expected_rig!r}, got {receipt.rig!r}"
        )
    if receipt.beads_prefix != expected_beads_prefix:
        raise TaskAuthorityError(
            "authority receipt Beads prefix mismatch: "
            f"expected {expected_beads_prefix!r}, got {receipt.beads_prefix!r}"
        )
    if receipt.database != expected_database:
        raise TaskAuthorityError(
            "authority receipt Beads database mismatch: "
            f"expected {expected_database!r}, got {receipt.database!r}"
        )


def load_authority_receipt(
    path: Path,
    *,
    expected_rig: str,
    expected_beads_prefix: str,
    expected_database: str,
) -> TaskAuthorityReceipt:
    """Load one explicit receipt and prove its exact deployment identity."""

    receipt = _load_receipt_bytes(_read_private_receipt(path))
    _require_expected_identity(
        receipt,
        expected_rig=expected_rig,
        expected_beads_prefix=expected_beads_prefix,
        expected_database=expected_database,
    )
    return receipt


def load_authority_from_environment(
    environment: Mapping[str, str] | None = None,
    *,
    expected_rig: str | None = None,
    expected_beads_prefix: str | None = None,
    expected_database: str | None = None,
) -> LoadedTaskAuthority:
    """Select authority without inspecting either task store.

    An absent variable is the sole legacy fallback and selects Taskmaster.  A
    present variable, including an empty one, opts into strict receipt loading;
    all expected identity values are then mandatory.
    """

    env = os.environ if environment is None else environment
    if TASK_AUTHORITY_ENV not in env:
        return LoadedTaskAuthority(
            mode=TaskAuthorityMode.TASKMASTER,
            explicit=False,
            receipt=None,
            receipt_path=None,
        )
    raw_path = env[TASK_AUTHORITY_ENV]
    if type(raw_path) is not str or not raw_path:
        raise TaskAuthorityError(
            f"{TASK_AUTHORITY_ENV} must contain an absolute receipt path"
        )
    if (
        expected_rig is None
        or expected_beads_prefix is None
        or expected_database is None
    ):
        raise TaskAuthorityError(
            "explicit authority loading requires expected rig, Beads prefix, and database"
        )
    path = _absolute_path(Path(raw_path), label=TASK_AUTHORITY_ENV)
    receipt = load_authority_receipt(
        path,
        expected_rig=expected_rig,
        expected_beads_prefix=expected_beads_prefix,
        expected_database=expected_database,
    )
    return LoadedTaskAuthority(
        mode=receipt.mode,
        explicit=True,
        receipt=receipt,
        receipt_path=path,
    )


def _hash_secure_executable(path: Path, *, label: str) -> str:
    configured = _absolute_path(path, label=label)
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production is Linux.
        raise TaskAuthorityError(f"this runtime cannot safely hash {label}")
    with _open_parent_directory(configured, create=False) as (parent_fd, name):
        try:
            descriptor = os.open(
                name, os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | no_follow, dir_fd=parent_fd
            )
        except (OSError, ValueError) as exc:
            raise TaskAuthorityError(f"cannot open {label}: {configured}") from exc
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise TaskAuthorityError(f"{label} must be a regular file")
            if before.st_uid != _current_uid() or before.st_nlink != 1:
                raise TaskAuthorityError(f"{label} ownership or hard-link count is unsafe")
            mode = stat.S_IMODE(before.st_mode)
            if mode & 0o022 or not mode & 0o100:
                raise TaskAuthorityError(
                    f"{label} must be owner-executable and not group/world-writable"
                )
            digest = hashlib.sha256()
            with os.fdopen(os.dup(descriptor), "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            after = os.fstat(descriptor)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_mode,
                before.st_uid,
                before.st_nlink,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_mode,
                after.st_uid,
                after.st_nlink,
            )
            if before_identity != after_identity:
                raise TaskAuthorityError(f"{label} changed while it was being hashed")
            return digest.hexdigest()
        finally:
            os.close(descriptor)


def _hash_pinned_runtime(path: Path) -> str:
    content = _read_secure_regular_file(
        path,
        label="task-authority runtime",
        allowed_modes=frozenset({0o444}),
        maximum_bytes=512 * 1024,
    )
    return hashlib.sha256(content).hexdigest()


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _write_private_json(path: Path, value: Mapping[str, Any], *, exclusive: bool) -> None:
    content = _canonical_json_bytes(value)
    configured = _absolute_path(path, label="private JSON path")
    with _open_parent_directory(configured, create=True) as (parent_fd, name):
        parent = os.fstat(parent_fd)
        if parent.st_uid != _current_uid() or stat.S_IMODE(parent.st_mode) != 0o700:
            raise TaskAuthorityError("private JSON parent must be owner-controlled mode 0700")
        _atomic_write_receipt(
            parent_fd,
            name,
            configured,
            content,
            exclusive=exclusive,
        )


def _binding_mapping(
    identity: RepositoryIdentity,
    city_root: Path,
    *,
    activated_at: str,
) -> dict[str, Any]:
    _parse_utc_timestamp(activated_at)
    _validate_primary_beads_metadata(identity.repository_root / ".beads")
    _manual_taskmaster_rollback_tree(identity)
    relative = {
        "authority_receipt": "runtime/authority/aegis.json",
        "task_authority_runtime": "runtime/authority/task-authority.py",
        "bd_executable": "artifacts/bd",
        "password_file": "runtime/secrets/aegis-app-password",
        "claude_executable": "artifacts/claude",
        "claude_config": "provider-config/claude-settings.json",
        "codex_executable": "artifacts/codex/bin/codex",
    }
    paths = {
        key: _relative_city_path(city_root, value, label=key)
        for key, value in relative.items()
    }
    receipt = load_authority_receipt(
        paths["authority_receipt"],
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
    )
    if receipt.mode is not TaskAuthorityMode.BEADS or receipt.generation != 2:
        raise TaskAuthorityError(
            "project enrollment can activate only after generation-2 Beads commits"
        )
    _inspect_secure_regular_file(
        paths["password_file"],
        label="Aegis Dolt application password",
        allowed_modes=frozenset({0o400, 0o600}),
        maximum_bytes=MAX_SECRET_BYTES,
    )
    return {
        "schema_version": ENROLLMENT_BINDING_SCHEMA,
        "repository_key": identity.repository_key,
        "repository_root": str(identity.repository_root),
        "git_common_dir": str(identity.git_common_dir),
        "city_root": str(city_root),
        "rig": "aegis",
        "rig_root": str(identity.repository_root),
        "beads_prefix": "ags",
        "beads_dir": str(identity.repository_root / ".beads"),
        "database": "aegis_beads",
        "dolt_host": "127.0.0.1",
        "dolt_port": 33071,
        "dolt_user": "aegis_beads",
        **relative,
        "authority_generation": 2,
        "authority_receipt_sha256": receipt_sha256(receipt),
        "task_authority_runtime_sha256": _hash_pinned_runtime(
            paths["task_authority_runtime"]
        ),
        "bd_sha256": _hash_secure_executable(paths["bd_executable"], label="pinned bd"),
        "claude_sha256": _hash_secure_executable(
            paths["claude_executable"], label="pinned Claude CLI"
        ),
        "claude_config_sha256": hashlib.sha256(
            _read_secure_regular_file(
                paths["claude_config"],
                label="locked Claude configuration",
                allowed_modes=frozenset({0o400, 0o440, 0o444, 0o600, 0o640, 0o644}),
                maximum_bytes=64 * 1024,
            )
        ).hexdigest(),
        "codex_sha256": _hash_secure_executable(
            paths["codex_executable"], label="pinned Codex CLI"
        ),
        "activated_at": activated_at,
    }


def activate_project_enrollment(
    project_root: Path,
    city_root: Path,
    *,
    activated_at: str,
) -> ProjectAuthorityEnrollment:
    """Publish enrollment only after the external gen2 binding is durable.

    A crash before the final pointer publish leaves the project unenrolled; a
    crash afterwards leaves the complete binding visible.  The operation is
    idempotent for byte-identical staged state and refuses divergent state.
    """

    identity = repository_identity(project_root)
    city = _secure_city_root(str(city_root))
    binding = _binding_mapping(identity, city, activated_at=activated_at)
    binding_path = city / ENROLLMENT_BINDING_RELATIVE_ROOT / f"{identity.repository_key}.json"
    binding_content = _canonical_json_bytes(binding)
    try:
        binding_path.lstat()
    except FileNotFoundError:
        _write_private_json(binding_path, binding, exclusive=True)
    else:
        existing_binding = _read_secure_regular_file(
            binding_path,
            label="authority enrollment binding",
            allowed_modes=frozenset({0o600}),
            maximum_bytes=MAX_ENROLLMENT_BYTES,
        )
        if existing_binding != binding_content:
            raise TaskAuthorityError("existing authority enrollment binding is divergent")
    pointer = {
        "schema_version": ENROLLMENT_POINTER_SCHEMA,
        "repository_key": identity.repository_key,
        "city_root": str(city),
        "task_authority_runtime": str(binding["task_authority_runtime"]),
        "task_authority_runtime_sha256": str(
            binding["task_authority_runtime_sha256"]
        ),
    }
    pointer_content = _canonical_json_bytes(pointer)
    try:
        identity.enrollment_pointer.lstat()
    except FileNotFoundError:
        configured = identity.enrollment_pointer
        with _open_parent_directory(configured, create=False) as (parent_fd, name):
            _atomic_write_receipt(
                parent_fd,
                name,
                configured,
                pointer_content,
                exclusive=True,
            )
    else:
        existing_pointer = _read_secure_regular_file(
            identity.enrollment_pointer,
            label="authority enrollment pointer",
            allowed_modes=frozenset({0o600}),
            maximum_bytes=MAX_ENROLLMENT_BYTES,
        )
        if existing_pointer != pointer_content:
            raise TaskAuthorityError("existing authority enrollment pointer is divergent")
    enrollment = load_project_enrollment(identity.repository_root)
    if enrollment is None:  # pragma: no cover - atomic publish returned but no file.
        raise TaskAuthorityError("authority enrollment pointer publish was not observable")
    return enrollment


def deactivate_project_enrollment_after_rollback(
    project_root: Path,
    *,
    rollback_generation: int = 3,
) -> Path:
    """Atomically archive the marker after a live Taskmaster rollback receipt."""

    identity = repository_identity(project_root)
    archive_name = (
        f"aegis-authority-enrollment.rollback-generation-{rollback_generation:08d}.json"
    )
    archive_path = identity.git_common_dir / archive_name
    enrollment = load_project_enrollment(project_root)
    if enrollment is None:
        try:
            archive_path.lstat()
        except FileNotFoundError as exc:
            raise TaskAuthorityError("project is not actively enrolled") from exc
        archived_content = _read_secure_regular_file(
            archive_path,
            label="rollback enrollment archive",
            allowed_modes=frozenset({0o600}),
            maximum_bytes=MAX_ENROLLMENT_BYTES,
        )
        archived = _strict_json_object(
            archived_content,
            label="rollback enrollment archive",
            keys=_ENROLLMENT_POINTER_KEYS,
            schema=ENROLLMENT_POINTER_SCHEMA,
        )
        if archived.get("repository_key") != identity.repository_key:
            raise TaskAuthorityError("rollback enrollment archive repository mismatch")
        city = _secure_city_root(archived.get("city_root"))
        binding_path = (
            city / ENROLLMENT_BINDING_RELATIVE_ROOT / f"{identity.repository_key}.json"
        )
        binding = _strict_json_object(
            _read_secure_regular_file(
                binding_path,
                label="authority enrollment binding",
                allowed_modes=frozenset({0o600}),
                maximum_bytes=MAX_ENROLLMENT_BYTES,
            ),
            label="authority enrollment binding",
            keys=_ENROLLMENT_BINDING_KEYS,
            schema=ENROLLMENT_BINDING_SCHEMA,
        )
        receipt_path = _relative_city_path(
            city, binding.get("authority_receipt"), label="authority_receipt"
        )
        receipt = load_authority_receipt(
            receipt_path,
            expected_rig="aegis",
            expected_beads_prefix="ags",
            expected_database="aegis_beads",
        )
        if (
            receipt.mode is not TaskAuthorityMode.TASKMASTER
            or receipt.generation != rollback_generation
        ):
            raise TaskAuthorityError(
                "archived enrollment is not backed by the exact Taskmaster rollback receipt"
            )
        return archive_path
    receipt = load_authority_receipt(
        enrollment.authority_receipt,
        expected_rig=enrollment.rig,
        expected_beads_prefix=enrollment.beads_prefix,
        expected_database=enrollment.database,
    )
    if (
        receipt.mode is not TaskAuthorityMode.TASKMASTER
        or receipt.generation != rollback_generation
    ):
        raise TaskAuthorityError(
            "enrollment can deactivate only after the exact Taskmaster rollback receipt commits"
        )
    lock_path = enrollment.identity.git_common_dir / f"{ENROLLMENT_POINTER_NAME}.lock"
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production is Linux.
        raise TaskAuthorityError("this runtime cannot safely deactivate enrollment")
    try:
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | no_follow, 0o600)
    except OSError as exc:
        raise TaskAuthorityError("cannot open enrollment deactivation lock") from exc
    try:
        lock_meta = os.fstat(lock_fd)
        if (
            not stat.S_ISREG(lock_meta.st_mode)
            or stat.S_IMODE(lock_meta.st_mode) != 0o600
            or lock_meta.st_uid != _current_uid()
            or lock_meta.st_nlink != 1
        ):
            raise TaskAuthorityError("enrollment deactivation lock is unsafe")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        if archive_path.exists() or archive_path.is_symlink():
            raise TaskAuthorityError("rollback enrollment archive already exists")
        os.rename(enrollment.pointer_path, archive_path)
        directory_fd = os.open(
            enrollment.identity.git_common_dir,
            os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | no_follow,
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise TaskAuthorityError("cannot atomically deactivate project enrollment") from exc
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)
    return archive_path


def _read_application_password(path: Path) -> str:
    content = _read_secure_regular_file(
        path,
        label="Aegis Dolt application password",
        allowed_modes=frozenset({0o400, 0o600}),
        maximum_bytes=MAX_SECRET_BYTES,
    )
    try:
        value = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TaskAuthorityError("Aegis Dolt application password is not valid UTF-8") from exc
    if value.endswith("\n"):
        value = value[:-1]
    if not 32 <= len(value) <= 4096:
        raise TaskAuthorityError("Aegis Dolt application password has an unsafe length")
    if any(ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        raise TaskAuthorityError("Aegis Dolt application password has unsafe characters")
    return value


def _manual_taskmaster_rollback_tree(identity: RepositoryIdentity) -> Path:
    """Return the real, owner-controlled Taskmaster rollback mountpoint."""

    root = identity.repository_root / ".taskmaster"
    try:
        metadata = root.lstat()
    except OSError as exc:
        raise TaskAuthorityError("preserved Taskmaster rollback tree is missing") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != _current_uid()
    ):
        raise TaskAuthorityError(
            "preserved Taskmaster rollback tree must be one owner-controlled real directory"
        )
    tasks = root / "tasks" / "tasks.json"
    _read_secure_regular_file(
        tasks,
        label="preserved Taskmaster rollback source",
        allowed_modes=frozenset({0o400, 0o440, 0o444, 0o600, 0o640, 0o644}),
        maximum_bytes=MAX_RECEIPT_BYTES * 256,
    )
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise TaskAuthorityError("cannot canonicalize Taskmaster rollback tree") from exc
    if resolved != root:
        raise TaskAuthorityError("Taskmaster rollback tree must not traverse a symlink")
    return resolved


def _manual_boundary_executable() -> Path:
    """Validate the root-owned namespace helper used by attended sessions."""

    path = MANUAL_BOUNDARY_EXECUTABLE
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise TaskAuthorityError("manual read-only boundary executable is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid not in SYSTEM_ROOT_UIDS
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or not stat.S_IMODE(metadata.st_mode) & 0o111
    ):
        raise TaskAuthorityError("manual read-only boundary executable is not root-controlled")
    return path


def _manual_boundary_arguments(
    enrollment: ProjectAuthorityEnrollment,
    executable: Path,
    provider_arguments: Sequence[str],
) -> tuple[Path, list[str]]:
    """Wrap one provider in a mount namespace with immutable Taskmaster state."""

    boundary = _manual_boundary_executable()
    taskmaster = _manual_taskmaster_rollback_tree(enrollment.identity)
    return boundary, [
        str(boundary),
        "--die-with-parent",
        "--bind",
        "/",
        "/",
        "--ro-bind",
        str(taskmaster),
        str(taskmaster),
        "--chdir",
        str(enrollment.identity.repository_root),
        "--",
        str(executable),
        *provider_arguments,
    ]


def manual_launch_environment(
    project_root: Path,
    provider: str,
    environment: Mapping[str, str] | None = None,
) -> tuple[ProjectAuthorityEnrollment, Path, dict[str, str]]:
    """Build the exact child-only environment for a subscription CLI."""

    if provider not in {"claude", "codex"}:
        raise TaskAuthorityError("manual provider must be claude or codex")
    original = dict(os.environ if environment is None else environment)
    forbidden_environment = (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CONFIG_DIR",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_FOUNDRY",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_MODEL",
        "CODEX_API_KEY",
        "CODEX_CONFIG",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_ORG_ID",
        "OPENAI_PROJECT_ID",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "CODEX_HOME",
        "CODEX_MODEL",
    )
    overrides = sorted(key for key in forbidden_environment if original.get(key))
    if overrides:
        raise TaskAuthorityError(
            "manual subscription launcher rejects provider auth/model boundary overrides: "
            f"{overrides}"
        )
    enrollment = load_project_enrollment(project_root)
    if enrollment is None:
        raise TaskAuthorityError("manual authority launcher requires an enrolled project")
    expected_environment = enrollment.expected_environment()
    authority_overrides = sorted(
        key
        for key, expected in expected_environment.items()
        if key in original and original[key] != expected
    )
    if authority_overrides:
        raise TaskAuthorityError(
            "manual launcher rejects alternate project authority endpoints: "
            f"{authority_overrides}"
        )
    runtime_digest = _hash_pinned_runtime(enrollment.task_authority_runtime)
    if runtime_digest != enrollment.task_authority_runtime_sha256:
        raise TaskAuthorityError("task-authority runtime digest mismatch")
    bd_digest = _hash_secure_executable(enrollment.bd_executable, label="pinned bd")
    if bd_digest != enrollment.bd_sha256:
        raise TaskAuthorityError("pinned bd digest mismatch")
    executable = (
        enrollment.claude_executable if provider == "claude" else enrollment.codex_executable
    )
    expected_cli_digest = (
        enrollment.claude_sha256 if provider == "claude" else enrollment.codex_sha256
    )
    if _hash_secure_executable(executable, label=f"pinned {provider} CLI") != expected_cli_digest:
        raise TaskAuthorityError(f"pinned {provider} CLI digest mismatch")
    claude_config = _read_secure_regular_file(
        enrollment.claude_config,
        label="locked Claude configuration",
        allowed_modes=frozenset({0o400, 0o440, 0o444, 0o600, 0o640, 0o644}),
        maximum_bytes=64 * 1024,
    )
    if hashlib.sha256(claude_config).hexdigest() != enrollment.claude_config_sha256:
        raise TaskAuthorityError("locked Claude configuration digest mismatch")
    claude_settings = _parse_json(claude_config, label="locked Claude configuration")
    if claude_settings != {
        "switchModelsOnFlag": False,
        "disableAllHooks": False,
        "enableAllProjectMcpServers": False,
        "skipDangerousModePermissionPrompt": False,
    }:
        raise TaskAuthorityError("locked Claude configuration has unexpected settings")
    receipt = load_authority_receipt(
        enrollment.authority_receipt,
        expected_rig=enrollment.rig,
        expected_beads_prefix=enrollment.beads_prefix,
        expected_database=enrollment.database,
    )
    if (
        receipt.mode is not TaskAuthorityMode.BEADS
        or receipt.generation != enrollment.authority_generation
        or receipt_sha256(receipt) != enrollment.authority_receipt_sha256
    ):
        raise TaskAuthorityError("manual launcher requires the exact live generation-2 receipt")
    child = original
    child.update(expected_environment)
    child.pop("BEADS_DOLT_PASSWORD_FILE", None)
    child.pop("GC_DOLT_PASSWORD_FILE", None)
    application_password = _read_application_password(enrollment.password_file)
    child["BEADS_DOLT_PASSWORD"] = application_password
    child["GC_DOLT_PASSWORD"] = application_password
    actor = child.get("BEADS_ACTOR", "").strip()
    if not actor:
        actor = f"manual-{provider}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:-]{0,127}", actor):
        raise TaskAuthorityError("BEADS_ACTOR has an unsafe shape")
    child["BEADS_ACTOR"] = actor
    session = child.get("GC_SESSION_NAME", "").strip() or f"manual-{provider}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", session):
        raise TaskAuthorityError("GC_SESSION_NAME has an unsafe shape")
    child["GC_SESSION_NAME"] = session
    child["AEGIS_AUTHORITY_LAUNCHER"] = provider
    child["PATH"] = f"{enrollment.city_root / 'bin'}:{child.get('PATH', '')}"
    return enrollment, executable, child


def _manual_provider_arguments(provider: str, arguments: Sequence[str], enrollment: ProjectAuthorityEnrollment) -> list[str]:
    supplied = [str(value) for value in arguments]
    if any("\0" in value for value in supplied):
        raise TaskAuthorityError("provider arguments must not contain NUL bytes")
    if provider == "codex":
        forbidden = {
            "-c",
            "--config",
            "-m",
            "--model",
            "-p",
            "--profile",
            "-s",
            "--sandbox",
            "-a",
            "--ask-for-approval",
            "--oss",
            "--local-provider",
            "--dangerously-bypass-approvals-and-sandbox",
        }
        for argument in supplied:
            option = argument.split("=", 1)[0]
            if option in forbidden or any(
                argument.startswith(prefix) for prefix in ("-c", "-m", "-p", "-s", "-a")
            ):
                raise TaskAuthorityError("manual Codex arguments override locked settings")
        return [
            "--strict-config",
            "--model",
            "gpt-5.6-sol",
            "--sandbox",
            "workspace-write",
            "--ask-for-approval",
            "on-request",
            "--config",
            'model_reasoning_effort="xhigh"',
            "--config",
            "check_for_update_on_startup=false",
            "--config",
            "mcp_servers={}",
            *supplied,
        ]
    forbidden = {
        "-m",
        "--model",
        "--fallback-model",
        "--settings",
        "--setting-sources",
        "--mcp-config",
        "--strict-mcp-config",
        "--agent",
        "--agents",
        "--bare",
        "--safe-mode",
        "--dangerously-skip-permissions",
        "--permission-mode",
    }
    for argument in supplied:
        if argument.split("=", 1)[0] in forbidden or argument.startswith("-m"):
            raise TaskAuthorityError("manual Claude arguments override locked settings")
    return [
        "--model",
        "claude-fable-5",
        "--settings",
        str(enrollment.claude_config),
        "--setting-sources",
        "user",
        "--strict-mcp-config",
        "--permission-mode",
        "acceptEdits",
        *supplied,
    ]


def exec_manual_provider(
    project_root: Path,
    provider: str,
    arguments: Sequence[str],
    environment: Mapping[str, str] | None = None,
) -> None:
    """Validate everything, then replace this process with the pinned CLI."""

    enrollment, executable, child = manual_launch_environment(
        project_root, provider, environment
    )
    provider_arguments = _manual_provider_arguments(provider, arguments, enrollment)
    boundary, argv = _manual_boundary_arguments(
        enrollment, executable, provider_arguments
    )
    os.execve(boundary, argv, child)


@contextmanager
def _transition_lock(path: Path) -> Iterator[tuple[int, str]]:
    receipt_path = _absolute_path(path, label="authority receipt path")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - Gas City workers are Linux.
        raise TaskAuthorityError("this runtime cannot safely lock an authority receipt")
    with _open_parent_directory(receipt_path, create=True) as (parent_fd, name):
        parent_metadata = os.fstat(parent_fd)
        if stat.S_IMODE(parent_metadata.st_mode) != 0o700:
            raise TaskAuthorityError(
                "authority receipt parent permissions must be exactly 0700"
            )
        if parent_metadata.st_uid != _current_uid():
            raise TaskAuthorityError(
                "authority receipt parent must be owned by the current user"
            )
        lock_name = f"{name}.lock"
        try:
            descriptor = os.open(
                lock_name,
                os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | no_follow,
                0o600,
                dir_fd=parent_fd,
            )
        except OSError as exc:
            raise TaskAuthorityError(
                f"cannot open authority transition lock: {receipt_path}.lock"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise TaskAuthorityError("authority transition lock must be a regular file")
            if stat.S_IMODE(metadata.st_mode) != 0o600:
                raise TaskAuthorityError(
                    "authority transition lock permissions must be exactly 0600"
                )
            if metadata.st_uid != _current_uid():
                raise TaskAuthorityError(
                    "authority transition lock must be owned by the current user"
                )
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
            except OSError as exc:
                raise TaskAuthorityError("cannot acquire authority transition lock") from exc
            yield parent_fd, name
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)


def _create_temporary_receipt(parent_fd: int, name: str) -> tuple[int, str]:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - Gas City workers are Linux.
        raise TaskAuthorityError("this runtime cannot safely create an authority receipt")
    for _ in range(128):
        temporary = f".{name}.{secrets.token_hex(16)}"
        try:
            descriptor = os.open(
                temporary,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | os.O_CLOEXEC
                | no_follow,
                0o600,
                dir_fd=parent_fd,
            )
        except FileExistsError:
            continue
        except OSError as exc:
            raise TaskAuthorityError("cannot create a temporary authority receipt") from exc
        try:
            os.fchmod(descriptor, 0o600)
        except OSError as exc:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except OSError:
                pass
            raise TaskAuthorityError(
                "cannot secure a temporary authority receipt"
            ) from exc
        return descriptor, temporary
    raise TaskAuthorityError("cannot allocate a unique temporary authority receipt")


def _raise_committed_or_uncertain(
    parent_fd: int,
    name: str,
    display_path: Path,
    content: bytes,
    cause: BaseException,
) -> None:
    try:
        observed = _read_private_receipt_at(parent_fd, name, display_path)
    except TaskAuthorityError:
        raise TaskAuthorityError(
            f"authority receipt commit status is uncertain: {display_path}"
        ) from cause
    if observed == content:
        raise TaskAuthorityCommittedError(
            _load_receipt_bytes(content), display_path
        ) from cause
    raise TaskAuthorityError(
        f"authority receipt commit status is uncertain: {display_path}"
    ) from cause


def _atomic_write_receipt(
    parent_fd: int,
    name: str,
    display_path: Path,
    content: bytes,
    *,
    exclusive: bool,
) -> None:
    temporary: str | None = None
    committed = False
    try:
        descriptor, temporary = _create_temporary_receipt(parent_fd, name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            try:
                os.link(
                    temporary,
                    name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise TaskAuthorityError(
                    "authority receipt already exists; refusing to infer state: "
                    f"{display_path}"
                ) from exc
            committed = True
            os.unlink(temporary, dir_fd=parent_fd)
            temporary = None
        else:
            os.replace(
                temporary,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            committed = True
            temporary = None
        os.fsync(parent_fd)
    except TaskAuthorityError:
        raise
    except OSError as exc:
        if committed:
            _raise_committed_or_uncertain(parent_fd, name, display_path, content, exc)
        raise TaskAuthorityError(
            f"cannot atomically write authority receipt: {display_path}"
        ) from exc
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except OSError:
                pass


def initialize_taskmaster_authority(
    path: Path,
    *,
    rig: str,
    beads_prefix: str,
    database: str,
    evidence: TaskAuthorityEvidence,
    activated_at: str,
) -> TaskAuthorityReceipt:
    """Create generation 1 in Taskmaster mode, without inferring prior state."""

    receipt_path = _absolute_path(path, label="authority receipt path")
    _validate_safe_identity(rig, beads_prefix, database)
    receipt = TaskAuthorityReceipt(
        rig=rig,
        mode=TaskAuthorityMode.TASKMASTER,
        beads_prefix=beads_prefix,
        database=database,
        evidence=evidence,
        generation=INITIAL_GENERATION,
        activated_at=activated_at,
        previous_receipt_sha256=None,
    )
    with _transition_lock(receipt_path) as (parent_fd, name):
        _atomic_write_receipt(
            parent_fd,
            name,
            receipt_path,
            receipt_bytes(receipt),
            exclusive=True,
        )
    return load_authority_receipt(
        receipt_path,
        expected_rig=rig,
        expected_beads_prefix=beads_prefix,
        expected_database=database,
    )


def transition_authority(
    path: Path,
    *,
    target_mode: TaskAuthorityMode,
    expected_generation: int,
    expected_rig: str,
    expected_beads_prefix: str,
    expected_database: str,
    expected_evidence: TaskAuthorityEvidence,
    activated_at: str,
) -> TaskAuthorityReceipt:
    """Atomically switch between Taskmaster and Beads authority.

    The compare-and-swap generation prevents stale transitions.  Evidence and
    deployment identity are copied from the current receipt only after exact
    caller-provided expectations match.  The operation never removes a task
    store and same-mode transitions are invalid.
    """

    receipt_path = _absolute_path(path, label="authority receipt path")
    if not isinstance(target_mode, TaskAuthorityMode):
        raise TaskAuthorityError("target_mode must be TaskAuthorityMode")
    if type(expected_generation) is not int or expected_generation < INITIAL_GENERATION:
        raise TaskAuthorityError(
            "expected_generation must be an integer greater than or equal to 1"
        )
    if not isinstance(expected_evidence, TaskAuthorityEvidence):
        raise TaskAuthorityError("expected_evidence must be TaskAuthorityEvidence")
    transition_time = _parse_utc_timestamp(activated_at)
    _validate_safe_identity(expected_rig, expected_beads_prefix, expected_database)
    with _transition_lock(receipt_path) as (parent_fd, name):
        current_bytes = _read_private_receipt_at(parent_fd, name, receipt_path)
        current = _load_receipt_bytes(current_bytes)
        _require_expected_identity(
            current,
            expected_rig=expected_rig,
            expected_beads_prefix=expected_beads_prefix,
            expected_database=expected_database,
        )
        if current.evidence != expected_evidence:
            raise TaskAuthorityError("authority evidence digests do not match expectations")
        if current.generation != expected_generation:
            raise TaskAuthorityError(
                "authority generation mismatch: "
                f"expected {expected_generation}, got {current.generation}"
            )
        allowed_target = {
            TaskAuthorityMode.TASKMASTER: TaskAuthorityMode.BEADS,
            TaskAuthorityMode.BEADS: TaskAuthorityMode.TASKMASTER,
        }[current.mode]
        if target_mode is not allowed_target:
            raise TaskAuthorityError(
                f"invalid authority transition: {current.mode.value} -> {target_mode.value}"
            )
        if transition_time <= _parse_utc_timestamp(current.activated_at):
            raise TaskAuthorityError("activated_at must increase across receipt generations")
        next_receipt = TaskAuthorityReceipt(
            rig=current.rig,
            mode=target_mode,
            beads_prefix=current.beads_prefix,
            database=current.database,
            evidence=current.evidence,
            generation=current.generation + 1,
            activated_at=activated_at,
            previous_receipt_sha256=hashlib.sha256(current_bytes).hexdigest(),
        )
        # Re-read immediately before replacement so an uncooperative writer
        # cannot silently bypass the compare-and-swap while our lock is held.
        if _read_private_receipt_at(parent_fd, name, receipt_path) != current_bytes:
            raise TaskAuthorityError("authority receipt changed during transition")
        _atomic_write_receipt(
            parent_fd,
            name,
            receipt_path,
            receipt_bytes(next_receipt),
            exclusive=False,
        )
    return load_authority_receipt(
        receipt_path,
        expected_rig=expected_rig,
        expected_beads_prefix=expected_beads_prefix,
        expected_database=expected_database,
    )


def _operator_main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Activate or deactivate one external Aegis authority enrollment."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    activate = subparsers.add_parser("activate-enrollment")
    activate.add_argument("--project-root", required=True)
    activate.add_argument("--city-root", required=True)
    activate.add_argument("--activated-at", required=True)
    deactivate = subparsers.add_parser("deactivate-enrollment")
    deactivate.add_argument("--project-root", required=True)
    deactivate.add_argument("--rollback-generation", type=int, default=3)
    status_parser = subparsers.add_parser("enrollment-status")
    status_parser.add_argument("--project-root", required=True)
    parsed = parser.parse_args(arguments)
    try:
        if parsed.operation == "activate-enrollment":
            enrollment = activate_project_enrollment(
                Path(parsed.project_root),
                Path(parsed.city_root),
                activated_at=parsed.activated_at,
            )
            payload = {
                "status": "active",
                "repository_key": enrollment.identity.repository_key,
                "pointer": str(enrollment.pointer_path),
                "binding": str(enrollment.binding_path),
                "authority_generation": enrollment.authority_generation,
                "authority_mode": "beads",
            }
        elif parsed.operation == "deactivate-enrollment":
            archive = deactivate_project_enrollment_after_rollback(
                Path(parsed.project_root),
                rollback_generation=parsed.rollback_generation,
            )
            payload = {
                "status": "inactive_taskmaster_rollback",
                "archive": str(archive),
                "rollback_generation": parsed.rollback_generation,
            }
        else:
            enrollment = load_project_enrollment(Path(parsed.project_root))
            payload = (
                {"status": "unenrolled"}
                if enrollment is None
                else {
                    "status": "active",
                    "repository_key": enrollment.identity.repository_key,
                    "pointer": str(enrollment.pointer_path),
                    "binding": str(enrollment.binding_path),
                    "authority_generation": enrollment.authority_generation,
                    "authority_mode": "beads",
                }
            )
    except TaskAuthorityError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_operator_main())
