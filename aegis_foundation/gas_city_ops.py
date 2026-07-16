"""Fail-closed production operations for the shared Gas City control plane.

The module deliberately separates *planning and evidence* from service
activation.  It never discovers a project by guessing, never places a secret
on a command line, and never treats a Beads JSONL export as a database backup.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import copy
import ctypes
import dataclasses
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from typing import Any

from aegis_foundation import task_authority, taskmaster_beads

LOCK_SCHEMA_VERSION = 1
LOCK_REQUIRED_TOOLS = ("gc", "bd", "dolt")
LOCK_ALLOWED_STATUSES = frozenset(
    {
        "staged_pending_provisioning",
        "provisioned_pending_canary",
        "canary_passed_soaking",
        "production",
    }
)
LOCK_REQUIRED_PACKS = frozenset({"gascity_core_bd", "gastown"})
CODEX_REQUIRED_HELPERS = frozenset({"codex-code-mode-host", "rg", "zsh"})
CODEX_PREFLIGHT_CATALOG_FIELDS = frozenset(
    {
        "source_path",
        "image_path",
        "sha256",
        "upstream_source_tag",
        "upstream_source_commit",
        "advertised_tools",
        "tool_invocation_policy",
    }
)
CODEX_PREFLIGHT_CATALOG_SOURCE_PATH = "config/codex-preflight-models.json"
CODEX_PREFLIGHT_CATALOG_IMAGE_PATH = "/opt/gas-city/codex-preflight-models.json"
CODEX_PREFLIGHT_UPSTREAM_TAG = "rust-v0.144.4"
CODEX_PREFLIGHT_UPSTREAM_COMMIT = "8c68d4c87dc54d38861f5114e920c3de2efa5876"
MODEL_RECEIPT_SCHEMA_VERSION = 1
PROMOTION_RECEIPT_SCHEMA_VERSION = 1
LOCK_IMAGE_TARGETS = {
    "dolt_server": "dolt-server",
    "egress_proxy": "egress-proxy",
    "claude_worker": "claude-worker",
    "codex_worker": "codex-worker",
}
BUILD_CONTEXT_FILES = frozenset(
    {
        ".dockerignore",
        "docker/Dockerfile",
        "docker/aegis-polecat-startup.py",
        "docker/aegis-runtime-shim.py",
        "docker/dolt-bootstrap.yaml",
        "docker/dolt-entrypoint.sh",
        "docker/dolt-healthcheck.sh",
        "docker/dolt-server.yaml",
        "docker/git-credential-github.sh",
        "docker/provider-supervisor.py",
        "docker/task-authority.py",
        "docker/tinyproxy.conf",
        "docker/tinyproxy.filter",
        "config/city.worker.toml",
        "config/codex-preflight-models.json",
        "artifacts/README.md",
        "artifacts/aegis-runtime.whl",
        "artifacts/gc",
        "artifacts/bd",
        "artifacts/dolt",
        "artifacts/claude",
        "artifacts/codex/bin/codex",
        "artifacts/codex/bin/codex-code-mode-host",
        "artifacts/codex/codex-path/rg",
        "artifacts/codex/codex-resources/zsh/bin/zsh",
        "formulas/aegis/mol-polecat-work.toml",
    }
)
CANARY_EVIDENCE_KINDS = (
    "backup",
    "migration",
    "recovery",
    "authority",
    "provider",
    "github",
    "obsidian",
    "canary",
)
PRODUCTION_EVIDENCE_KINDS = (*CANARY_EVIDENCE_KINDS, "soak")
SOAK_REQUIRED_CHECKS = frozenset(
    {
        "models",
        "beads",
        "reconciliation",
        "projection",
        "supervisor",
        "authority",
    }
)
TASK_AUTHORITY_RUNTIME_FIELDS = frozenset({"source_path", "image_path", "sha256"})
TASK_AUTHORITY_SOURCE_PATH = "docker/task-authority.py"
TASK_AUTHORITY_IMAGE_PATH = "/opt/gas-city/task-authority.py"
GIT_WORKTREE_BROKER_FIELDS = frozenset({"source_path", "deployed_path", "sha256"})
GIT_WORKTREE_BROKER_SOURCE_PATH = "bin/git-worktree-broker"
GIT_WORKTREE_BROKER_DEPLOYED_PATH = "bin/git-worktree-broker"
MODEL_EVIDENCE_BROKER_FIELDS = frozenset({"source_path", "deployed_path", "sha256"})
MODEL_EVIDENCE_BROKER_SOURCE_PATH = "bin/model-evidence-broker"
MODEL_EVIDENCE_BROKER_DEPLOYED_PATH = "bin/model-evidence-broker"
GITHUB_DELIVERY_FIELDS = frozenset(
    {
        "broker_source_path",
        "broker_deployed_path",
        "broker_sha256",
        "repository",
        "default_branch",
        "permissions",
        "required_default_branch_rules",
        "maximum_lifetime_seconds",
    }
)
GITHUB_DELIVERY_BROKER_SOURCE_PATH = "bin/github-app-token-broker"
GITHUB_DELIVERY_BROKER_DEPLOYED_PATH = "bin/github-app-token-broker"
GITHUB_DELIVERY_REPOSITORY = "loucmane/codex-starter-pack"
GITHUB_DELIVERY_PERMISSIONS = {
    "contents": "write",
    "metadata": "read",
    "pull_requests": "write",
}
GITHUB_DELIVERY_REQUIRED_RULES = [
    "deletion",
    "non_fast_forward",
    "pull_request",
    "required_status_checks",
]
AEGIS_POLECAT_STARTUP_FIELDS = frozenset(
    {
        "source_path",
        "image_path",
        "sha256",
        "receipt_path",
        "formula_path",
        "formula_sha256",
        "upstream_formula_sha256",
        "runtime_artifact_source_path",
        "runtime_artifact_image_path",
        "runtime_artifact_sha256",
        "runtime_shim_source_path",
        "runtime_shim_image_path",
        "runtime_shim_sha256",
        "local_launcher_path",
        "local_launcher_sha256",
    }
)
AEGIS_POLECAT_STARTUP_FIXED_PATHS = {
    "source_path": "docker/aegis-polecat-startup.py",
    "image_path": "/opt/gas-city/aegis-polecat-startup.py",
    "receipt_path": "/run/gas-city/aegis-startup-receipt.json",
    "formula_path": "formulas/aegis/mol-polecat-work.toml",
    "runtime_artifact_source_path": "artifacts/aegis-runtime.whl",
    "runtime_artifact_image_path": "/opt/gas-city/aegis-runtime.whl",
    "runtime_shim_source_path": "docker/aegis-runtime-shim.py",
    "runtime_shim_image_path": "/opt/gas-city/aegis-runtime-shim.py",
    "local_launcher_path": ".aegis/bin/aegis",
}
AEGIS_POLECAT_STARTUP_DIGEST_FIELDS = frozenset(
    {
        "sha256",
        "formula_sha256",
        "upstream_formula_sha256",
        "runtime_artifact_sha256",
        "runtime_shim_sha256",
        "local_launcher_sha256",
    }
)
AEGIS_POLECAT_BUILD_SOURCE_DIGEST_FIELDS = (
    ("source_path", "sha256"),
    ("formula_path", "formula_sha256"),
    ("runtime_artifact_source_path", "runtime_artifact_sha256"),
    ("runtime_shim_source_path", "runtime_shim_sha256"),
)
AEGIS_POLECAT_LOCAL_LAUNCHER_CONTENT = (
    b"#!/bin/sh\n"
    b"set -eu\n"
    b'exec /usr/bin/python3 -I /opt/gas-city/aegis-runtime-shim.py "$@"\n'
)
LIVE_AUTHORITY_RECEIPT_PATH = "runtime/authority/aegis.json"
LIVE_AUTHORITY_IDENTITY = {
    "rig": "aegis",
    "beads_prefix": "ags",
    "database": "aegis_beads",
}
HQ_DOLT_CONTAINER_NAME = "gas-city-hq-dolt"
HQ_DOLT_ENDPOINT_HOST = "127.0.0.1"
HQ_DOLT_ENDPOINT_PORT = 33070
HQ_DOLT_DATABASE_RELATIVE_PATH = "hq"
STOPPED_WORKERS_KIND = "gas-city-workers-stopped"
STOPPED_WORKER_PHASES = frozenset({"before-attempt", "before-transition", "after-transition"})
CANARY_RUN_SCHEMA = "gas-city-controlled-canary-intent/v2"
OBSIDIAN_EVIDENCE_SCHEMA_VERSION = 3
CANARY_EVIDENCE_SCHEMA_VERSION = 3
AEGIS_MIGRATION_TARGET_FIELDS = frozenset(
    {
        "generation",
        "generation_record_sha256",
        "repository_root",
        "git_common_dir",
        "repository_key",
    }
)
CANARY_RUN_MAX_AGE = dt.timedelta(hours=24)
CANARY_POLECAT_ASSIGNEE_RE = re.compile(r"aegis/gastown\.polecat_[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")
CANARY_REFINERY_ASSIGNEE = "aegis/gastown.refinery"
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
GIT_REF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}\Z")
SOAK_MINIMUM_SECONDS = 24 * 60 * 60
SOAK_MAX_OBSERVATION_GAP_SECONDS = 60 * 60
SOAK_BOUNDARY_TOLERANCE_SECONDS = 5 * 60
SOAK_MAX_SESSION_RECEIPT_AGE_SECONDS = 6 * 60 * 60
SOAK_MIN_DISTINCT_SESSION_RECEIPTS = 4
SOAK_AGENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
SOAK_SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,47}\Z")
HOST_MODEL_ATTESTATION_SCOPE = "isolated-zero-tool-invocation-preflight-gates-session"
HOST_MODEL_SESSION_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "kind",
        "status",
        "phase",
        "provider",
        "expected_model",
        "expected_effort",
        "observed_model",
        "observed_effort",
        "provider_exit_code",
        "event_sha256",
        "transcript_sha256",
        "transcript_locator",
        "tool_free",
        "challenge_sha256",
        "container_name",
        "container_image_id",
        "container_boundary",
        "model_source_phase",
        "model_attestation_scope",
        "evidence_id",
        "run_generation",
        "run_id_sha256",
        "session_id_sha256",
        "git_broker_id",
        "git_broker_receipt_sha256",
        "git_startup_receipt_sha256",
        "git_source_starting_oid",
        "git_authorized_ref",
        "container_init_host_pid",
        "supervisor_host_pid",
        "supervisor_host_uid",
        "supervisor_host_gid",
        "supervisor_starttime_ticks",
        "preflight_receipt_sha256",
        "recorded_at",
    }
)
CANARY_REQUIRED_CHECKS = frozenset(
    {
        "authority",
        "beads_write_read",
        "reconciliation",
        "claude_worker",
        "codex_worker",
        "github_delivery",
        "obsidian_projection",
        "crash_restart",
    }
)
MIGRATION_REQUIRED_ARTIFACTS = frozenset(
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
TOOL_VERSION_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "gc": ("version",),
    "bd": ("--version",),
    "dolt": ("version",),
}
REQUIRED_EXCLUSIONS = frozenset({"graphiti", "cognee", "ollama"})
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SAFE_NAME_RE = re.compile(r"[a-z][a-z0-9_-]{0,62}\Z")
SECRET_KEY_RE = re.compile(r"(?:password|token|secret|credential|private[_-]?key)", re.I)

GAS_CITY_REQUIRED_CUSTOM_TYPES = (
    "molecule,convoy,message,event,gate,merge-request,agent,role,rig,session,"
    "spec,convergence,step"
)
AEGIS_BEADS_INIT_SCHEMA = "gas-city-aegis-beads-initialization/v3"
AEGIS_BEADS_INIT_POINTER_SCHEMA = "gas-city-aegis-beads-initialization-pointer/v3"
AEGIS_BEADS_INIT_PREFIX = "ags"
AEGIS_BEADS_INIT_HOST = "127.0.0.1"
AEGIS_BEADS_INIT_PORT = 33071
AEGIS_BEADS_INIT_USER = "aegis_beads"
AEGIS_BEADS_INIT_DATABASE = "aegis_beads"
AEGIS_RECOVERY_USER = "root"
AEGIS_BEADS_INIT_BD_VERSION_OUTPUT = "bd version 1.1.0 (8e4e59d39)"
AEGIS_BEADS_INIT_DOLT_VERSION_OUTPUT = "dolt version 2.2.0"
AEGIS_BEADS_CANONICAL_CONFIG = (
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
    + f"types.custom: {GAS_CITY_REQUIRED_CUSTOM_TYPES}\n".encode("ascii")
)
AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK = (
    b"# Beads stealth mode (added by bd init --stealth)\n"
    b".beads/\n"
    b".claude/settings.local.json\n"
    b"\n"
    b"# Beads: Dolt files kept local via .git/info/exclude (stealth / no-git-ops)\n"
    b".dolt/\n"
    b"*.db\n"
    b".beads-credential-key\n"
    b".beads/proxieddb/\n"
)
AEGIS_BEADS_INIT_POINTER_NAME = "gas-city-aegis-beads-initialization.json"
AEGIS_BEADS_INIT_STATE_DIRECTORY = "gas-city-aegis-beads-initialization"
AEGIS_BEADS_INIT_MAX_FILE_BYTES = 16 * 1024 * 1024
NATIVE_RESTORE_SCHEMA_VERSION = 4
NATIVE_BACKUP_MANIFEST_SCHEMA_VERSION = 1
NATIVE_BACKUP_MANIFEST_SUFFIX = ".gas-city-native-backup-manifest.json"
DOLT_DATA_MOUNT_DESTINATION = "/var/lib/dolt/data"


class GasCityOpsError(RuntimeError):
    """A production operation could not prove its safety contract."""


@dataclasses.dataclass(frozen=True)
class DoltEndpoint:
    """Non-secret connection identity for one externally managed Dolt server."""

    host: str
    port: int
    user: str
    database: str

    def validate(self, *, label: str) -> None:
        if not self.host.strip() or any(char.isspace() for char in self.host):
            raise GasCityOpsError(f"{label} host must be a non-empty hostname or address")
        if not 1 <= self.port <= 65535:
            raise GasCityOpsError(f"{label} port must be between 1 and 65535")
        for field, value in (("user", self.user), ("database", self.database)):
            if not SAFE_NAME_RE.fullmatch(value):
                raise GasCityOpsError(f"{label} {field} must match [a-z][a-z0-9_-]{{0,62}}")


Runner = Callable[[Sequence[str], Path, Mapping[str, str]], subprocess.CompletedProcess[str]]


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GasCityOpsError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite_json(value: str) -> None:
    raise GasCityOpsError(f"non-finite JSON number is not allowed: {value}")


def _load_json_bytes(content: bytes, *, label: str) -> Any:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GasCityOpsError(f"{label} is not valid UTF-8") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_json,
        )
    except json.JSONDecodeError as exc:
        raise GasCityOpsError(f"{label} is not valid JSON: {exc}") from exc


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _utc_timestamp(value: str, *, label: str) -> dt.datetime:
    if not isinstance(value, str):
        raise GasCityOpsError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GasCityOpsError(f"{label} must be an RFC3339 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise GasCityOpsError(f"{label} must use UTC")
    return parsed


def _format_utc(value: dt.datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != dt.timedelta(0):
        raise GasCityOpsError("clock returned a non-UTC time")
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _canonical_path(path: Path, *, must_exist: bool, label: str) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise GasCityOpsError(f"{label} must be an absolute path")
    try:
        return expanded.resolve(strict=must_exist)
    except OSError as exc:
        raise GasCityOpsError(f"cannot resolve {label}: {expanded}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _regular_file_bytes(path: Path, *, label: str) -> bytes:
    if path.is_symlink():
        raise GasCityOpsError(f"{label} must not be a symlink: {path}")
    if not path.is_file():
        raise GasCityOpsError(f"{label} must be a regular file: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o022:
        raise GasCityOpsError(f"{label} must not be group/world writable: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GasCityOpsError(f"cannot read {label}: {path}") from exc


def _make_private_parents(parent: Path) -> None:
    missing: list[Path] = []
    cursor = parent
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    for directory in reversed(missing):
        os.chmod(directory, 0o700)
    os.chmod(parent, 0o700)


def _atomic_write(
    path: Path,
    content: bytes,
    *,
    mode: int = 0o600,
    exclusive: bool = False,
) -> None:
    parent = path.parent
    _make_private_parents(parent)
    if parent.is_symlink() or path.is_symlink():
        raise GasCityOpsError(f"atomic output path must not traverse a symlink: {path}")
    try:
        os.chmod(parent, 0o700)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
        try:
            os.fchmod(fd, mode)
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            if exclusive:
                try:
                    os.link(temporary, path, follow_symlinks=False)
                except FileExistsError as exc:
                    raise GasCityOpsError(
                        f"output already exists; evidence is append-only: {path}"
                    ) from exc
                os.unlink(temporary)
            else:
                os.replace(temporary, path)
            os.chmod(path, mode)
            directory_fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
    except OSError as exc:
        raise GasCityOpsError(f"cannot write atomic output: {path}") from exc


def _walk_secret_values(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if SECRET_KEY_RE.search(str(key)) and child not in (None, "", False, [], {}):
                raise GasCityOpsError(
                    f"runtime lock must not contain secret material: {child_path}"
                )
            _walk_secret_values(child, path=child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_secret_values(child, path=f"{path}[{index}]")


def _locked_build_source_artifacts(lock: Mapping[str, Any]) -> dict[str, str]:
    """Return the exact source artifact set cryptographically bound to an image build."""

    authority = lock["task_authority_runtime"]
    startup = lock["aegis_polecat_startup"]
    codex_preflight = lock["codex_preflight_catalog"]
    artifacts = {
        str(authority["source_path"]): str(authority["sha256"]),
        str(codex_preflight["source_path"]): str(codex_preflight["sha256"]),
        **{
            str(startup[path_field]): str(startup[digest_field])
            for path_field, digest_field in AEGIS_POLECAT_BUILD_SOURCE_DIGEST_FIELDS
        },
    }
    if len(artifacts) != 2 + len(AEGIS_POLECAT_BUILD_SOURCE_DIGEST_FIELDS):
        raise GasCityOpsError("runtime lock aliases two immutable build artifacts")
    if set(artifacts) - BUILD_CONTEXT_FILES:
        raise GasCityOpsError(
            "runtime lock immutable build artifacts are absent from the audited context"
        )
    return dict(sorted(artifacts.items()))


def _validate_image_build_receipt_shape(
    value: Any,
    *,
    expected_images: Mapping[str, str],
    expected_source_artifacts: Mapping[str, str],
) -> None:
    if not isinstance(value, dict):
        raise GasCityOpsError("image build receipt must contain one object")
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "built_at",
            "source_lock_sha256",
            "lock_schema_version",
            "source_artifacts",
            "build_context",
            "docker",
            "targets",
            "images",
        }
        or value.get("schema_version") != 1
        or value.get("kind") != "immutable-image-build"
        or value.get("status") != "pass"
        or value.get("lock_schema_version") != LOCK_SCHEMA_VERSION
        or value.get("targets") != LOCK_IMAGE_TARGETS
        or value.get("images") != dict(expected_images)
        or value.get("source_artifacts") != dict(expected_source_artifacts)
        or set(expected_images) != set(LOCK_IMAGE_TARGETS)
        or any(
            not isinstance(image_id, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None
            for image_id in expected_images.values()
        )
        or not isinstance(value.get("source_lock_sha256"), str)
        or SHA256_RE.fullmatch(str(value["source_lock_sha256"])) is None
        or set(expected_source_artifacts) - BUILD_CONTEXT_FILES
        or any(
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or Path(path).as_posix() != path
            or not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            for path, digest in expected_source_artifacts.items()
        )
    ):
        raise GasCityOpsError("image build receipt does not prove locked immutable images")
    _utc_timestamp(value.get("built_at"), label="image build receipt built_at")
    build_context = value.get("build_context")
    if (
        not isinstance(build_context, dict)
        or set(build_context)
        != {
            "manifest_sha256",
            "file_count",
            "dockerfile_sha256",
            "dockerignore_sha256",
        }
        or any(
            not isinstance(build_context.get(name), str)
            or SHA256_RE.fullmatch(str(build_context[name])) is None
            for name in ("manifest_sha256", "dockerfile_sha256", "dockerignore_sha256")
        )
        or not isinstance(build_context.get("file_count"), int)
        or build_context["file_count"] < 1
    ):
        raise GasCityOpsError("image build receipt has invalid context provenance")
    docker = value.get("docker")
    if (
        not isinstance(docker, dict)
        or set(docker)
        != {
            "binary",
            "binary_sha256",
            "client_version",
            "tagged",
            "pull",
            "no_cache",
        }
        or docker.get("tagged") is not False
        or docker.get("pull") is not False
        or docker.get("no_cache") is not True
        or not isinstance(docker.get("binary"), str)
        or not docker["binary"]
        or not isinstance(docker.get("binary_sha256"), str)
        or SHA256_RE.fullmatch(str(docker["binary_sha256"])) is None
        or not isinstance(docker.get("client_version"), str)
        or not docker["client_version"]
    ):
        raise GasCityOpsError("image build receipt has invalid Docker provenance")


def load_runtime_lock(
    path: Path,
    *,
    require_observed_models: bool = False,
    _validate_promotions: bool = True,
) -> dict[str, Any]:
    """Load and strictly validate the immutable, secret-free runtime lock."""

    lock_path = _canonical_path(path, must_exist=True, label="runtime lock")
    value = _load_json_bytes(
        _regular_file_bytes(lock_path, label="runtime lock"),
        label="runtime lock",
    )
    if not isinstance(value, dict):
        raise GasCityOpsError("runtime lock must contain one JSON object")
    _walk_secret_values(value)
    expected_root_fields = {
        "schema_version",
        "status",
        "tools",
        "packs",
        "task_authority_runtime",
        "aegis_polecat_startup",
        "git_worktree_broker",
        "model_evidence_broker",
        "github_delivery",
        "codex_preflight_catalog",
        "control_plane_manifest",
        "images",
        "image_receipt",
        "promotion",
        "providers",
        "exclusions",
    }
    if set(value) != expected_root_fields:
        raise GasCityOpsError(
            "runtime lock fields must be exact; "
            f"missing={sorted(expected_root_fields - set(value))}, "
            f"unexpected={sorted(set(value) - expected_root_fields)}"
        )
    if value.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise GasCityOpsError(f"runtime lock schema_version must be {LOCK_SCHEMA_VERSION}")
    if value.get("status") not in LOCK_ALLOWED_STATUSES:
        raise GasCityOpsError("runtime lock status is invalid")

    control_plane_manifest = value.get("control_plane_manifest")
    if (
        type(control_plane_manifest) is not dict
        or set(control_plane_manifest) != {"path", "sha256"}
        or control_plane_manifest.get("path") != "control-plane-manifest.json"
        or type(control_plane_manifest.get("sha256")) is not str
        or SHA256_RE.fullmatch(control_plane_manifest["sha256"]) is None
    ):
        raise GasCityOpsError("runtime lock control-plane manifest binding is invalid")
    control_plane_manifest_path = lock_path.parent / control_plane_manifest["path"]
    control_plane_manifest_bytes = _regular_file_bytes(
        control_plane_manifest_path,
        label="runtime lock control-plane manifest",
    )
    if _sha256(control_plane_manifest_bytes) != control_plane_manifest["sha256"]:
        raise GasCityOpsError("runtime lock control-plane manifest content digest mismatch")

    tools = value.get("tools")
    if not isinstance(tools, dict) or set(tools) != set(LOCK_REQUIRED_TOOLS):
        raise GasCityOpsError(f"runtime lock tools must be exactly {list(LOCK_REQUIRED_TOOLS)}")
    for name in LOCK_REQUIRED_TOOLS:
        record = tools[name]
        if not isinstance(record, dict) or set(record) != {
            "version",
            "binary_sha256",
            "archive_sha256",
        }:
            raise GasCityOpsError(
                f"runtime lock tools.{name} must contain exactly version, "
                "binary_sha256, and archive_sha256"
            )
        version = record.get("version")
        digest = record.get("binary_sha256")
        if not isinstance(version, str) or not version.strip():
            raise GasCityOpsError(f"runtime lock tools.{name}.version must be non-empty")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise GasCityOpsError(f"runtime lock tools.{name}.binary_sha256 is invalid")
        archive_digest = record.get("archive_sha256")
        if not isinstance(archive_digest, str) or not SHA256_RE.fullmatch(archive_digest):
            raise GasCityOpsError(f"runtime lock tools.{name}.archive_sha256 is invalid")

    packs = value.get("packs")
    if not isinstance(packs, dict) or set(packs) != LOCK_REQUIRED_PACKS:
        raise GasCityOpsError("runtime lock packs must be exactly gascity_core_bd and gastown")
    for name, record in packs.items():
        if not isinstance(record, dict) or set(record) != {"commit"}:
            raise GasCityOpsError(f"runtime lock packs.{name} must contain only commit")
        commit = record.get("commit")
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise GasCityOpsError(f"runtime lock packs.{name}.commit is invalid")

    authority_runtime = value.get("task_authority_runtime")
    if (
        not isinstance(authority_runtime, dict)
        or set(authority_runtime) != TASK_AUTHORITY_RUNTIME_FIELDS
        or authority_runtime.get("source_path") != TASK_AUTHORITY_SOURCE_PATH
        or authority_runtime.get("image_path") != TASK_AUTHORITY_IMAGE_PATH
        or not isinstance(authority_runtime.get("sha256"), str)
        or SHA256_RE.fullmatch(str(authority_runtime["sha256"])) is None
    ):
        raise GasCityOpsError("runtime lock task-authority runtime is invalid")

    startup = value.get("aegis_polecat_startup")
    if not isinstance(startup, dict) or set(startup) != AEGIS_POLECAT_STARTUP_FIELDS:
        raise GasCityOpsError("runtime lock Aegis polecat startup fields are not exact")
    if any(
        startup.get(field) != expected
        for field, expected in AEGIS_POLECAT_STARTUP_FIXED_PATHS.items()
    ):
        raise GasCityOpsError("runtime lock Aegis polecat startup paths are invalid")
    if any(
        not isinstance(startup.get(field), str) or SHA256_RE.fullmatch(str(startup[field])) is None
        for field in AEGIS_POLECAT_STARTUP_DIGEST_FIELDS
    ):
        raise GasCityOpsError("runtime lock Aegis polecat startup digest is invalid")
    if startup["local_launcher_sha256"] != _sha256(AEGIS_POLECAT_LOCAL_LAUNCHER_CONTENT):
        raise GasCityOpsError(
            "runtime lock Aegis polecat local launcher does not match the immutable contract"
        )
    git_broker = value.get("git_worktree_broker")
    if (
        not isinstance(git_broker, dict)
        or set(git_broker) != GIT_WORKTREE_BROKER_FIELDS
        or git_broker.get("source_path") != GIT_WORKTREE_BROKER_SOURCE_PATH
        or git_broker.get("deployed_path") != GIT_WORKTREE_BROKER_DEPLOYED_PATH
        or not isinstance(git_broker.get("sha256"), str)
        or SHA256_RE.fullmatch(str(git_broker["sha256"])) is None
    ):
        raise GasCityOpsError("runtime lock Git worktree broker contract is invalid")
    model_broker = value.get("model_evidence_broker")
    if (
        not isinstance(model_broker, dict)
        or set(model_broker) != MODEL_EVIDENCE_BROKER_FIELDS
        or model_broker.get("source_path") != MODEL_EVIDENCE_BROKER_SOURCE_PATH
        or model_broker.get("deployed_path") != MODEL_EVIDENCE_BROKER_DEPLOYED_PATH
        or not isinstance(model_broker.get("sha256"), str)
        or SHA256_RE.fullmatch(str(model_broker["sha256"])) is None
    ):
        raise GasCityOpsError("runtime lock model evidence broker contract is invalid")
    github_delivery = value.get("github_delivery")
    if (
        not isinstance(github_delivery, dict)
        or set(github_delivery) != GITHUB_DELIVERY_FIELDS
        or github_delivery.get("broker_source_path") != GITHUB_DELIVERY_BROKER_SOURCE_PATH
        or github_delivery.get("broker_deployed_path") != GITHUB_DELIVERY_BROKER_DEPLOYED_PATH
        or not isinstance(github_delivery.get("broker_sha256"), str)
        or SHA256_RE.fullmatch(str(github_delivery["broker_sha256"])) is None
        or github_delivery.get("repository") != GITHUB_DELIVERY_REPOSITORY
        or github_delivery.get("default_branch") != "main"
        or github_delivery.get("permissions") != GITHUB_DELIVERY_PERMISSIONS
        or github_delivery.get("required_default_branch_rules") != GITHUB_DELIVERY_REQUIRED_RULES
        or github_delivery.get("maximum_lifetime_seconds") != 65 * 60
    ):
        raise GasCityOpsError("runtime lock GitHub delivery contract is invalid")
    codex_preflight = value.get("codex_preflight_catalog")
    if (
        not isinstance(codex_preflight, dict)
        or set(codex_preflight) != CODEX_PREFLIGHT_CATALOG_FIELDS
        or codex_preflight.get("source_path") != CODEX_PREFLIGHT_CATALOG_SOURCE_PATH
        or codex_preflight.get("image_path") != CODEX_PREFLIGHT_CATALOG_IMAGE_PATH
        or not isinstance(codex_preflight.get("sha256"), str)
        or SHA256_RE.fullmatch(str(codex_preflight["sha256"])) is None
        or codex_preflight.get("upstream_source_tag") != CODEX_PREFLIGHT_UPSTREAM_TAG
        or codex_preflight.get("upstream_source_commit") != CODEX_PREFLIGHT_UPSTREAM_COMMIT
        or codex_preflight.get("advertised_tools") != ["update_plan", "view_image"]
        or codex_preflight.get("tool_invocation_policy") != "zero"
    ):
        raise GasCityOpsError("runtime lock Codex preflight catalog contract is invalid")
    _locked_build_source_artifacts(value)

    images = value.get("images")
    if not isinstance(images, dict) or set(images) != set(LOCK_IMAGE_TARGETS):
        raise GasCityOpsError("runtime lock image set is invalid")
    image_ids: dict[str, str] = {}
    for name, target in LOCK_IMAGE_TARGETS.items():
        record = images[name]
        if not isinstance(record, dict) or set(record) != {"target", "image_id"}:
            raise GasCityOpsError(
                f"runtime lock images.{name} must contain only target and image_id"
            )
        if record.get("target") != target:
            raise GasCityOpsError(f"runtime lock images.{name}.target is invalid")
        image_id = record.get("image_id")
        if image_id is not None and (
            not isinstance(image_id, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", image_id) is None
        ):
            raise GasCityOpsError(f"runtime lock images.{name}.image_id is invalid")
        if isinstance(image_id, str):
            image_ids[name] = image_id

    image_receipt = value.get("image_receipt")
    if not isinstance(image_receipt, dict) or set(image_receipt) != {"path", "sha256"}:
        raise GasCityOpsError("runtime lock image_receipt is invalid")
    image_receipt_path_value = image_receipt.get("path")
    if (
        not isinstance(image_receipt_path_value, str)
        or not image_receipt_path_value
        or Path(image_receipt_path_value).is_absolute()
        or ".." in Path(image_receipt_path_value).parts
    ):
        raise GasCityOpsError("runtime lock image_receipt.path must be safe and relative")
    image_receipt_digest = image_receipt.get("sha256")
    if image_receipt_digest is not None and (
        not isinstance(image_receipt_digest, str) or not SHA256_RE.fullmatch(image_receipt_digest)
    ):
        raise GasCityOpsError("runtime lock image_receipt.sha256 is invalid")
    if value["status"] != "staged_pending_provisioning":
        if set(image_ids) != set(LOCK_IMAGE_TARGETS):
            raise GasCityOpsError("provisioned runtime lock lacks immutable image IDs")
        if not isinstance(image_receipt_digest, str):
            raise GasCityOpsError("provisioned runtime lock lacks an image receipt")
        receipt_bytes = _regular_file_bytes(
            lock_path.parent / image_receipt_path_value,
            label="runtime lock image receipt",
        )
        if stat.S_IMODE((lock_path.parent / image_receipt_path_value).stat().st_mode) & 0o077:
            raise GasCityOpsError("runtime lock image receipt must be owner-only")
        if _sha256(receipt_bytes) != image_receipt_digest:
            raise GasCityOpsError("runtime lock image receipt content digest mismatch")
        receipt_value = _load_json_bytes(receipt_bytes, label="runtime lock image receipt")
        _validate_image_build_receipt_shape(
            receipt_value,
            expected_images=image_ids,
            expected_source_artifacts=_locked_build_source_artifacts(value),
        )

    exclusions = value.get("exclusions")
    if not isinstance(exclusions, list) or any(not isinstance(item, str) for item in exclusions):
        raise GasCityOpsError("runtime lock exclusions must be an array of strings")
    if not REQUIRED_EXCLUSIONS.issubset({item.lower() for item in exclusions}):
        raise GasCityOpsError("runtime lock must exclude Graphiti, Cognee, and Ollama")

    providers = value.get("providers")
    if not isinstance(providers, dict) or set(providers) != {"claude", "codex"}:
        raise GasCityOpsError("runtime lock providers must be exactly claude and codex")
    expected = {
        "claude": ("claude-fable-5", None),
        "codex": ("gpt-5.6-sol", "xhigh"),
    }
    for name, (model, effort) in expected.items():
        record = providers[name]
        if not isinstance(record, dict) or record.get("requested_model") != model:
            raise GasCityOpsError(f"runtime lock provider {name} must request {model}")
        cli_version = record.get("cli_version")
        binary_digest = record.get("binary_sha256")
        if not isinstance(cli_version, str) or not cli_version.strip():
            raise GasCityOpsError(f"runtime lock provider {name} cli_version is invalid")
        if not isinstance(binary_digest, str) or not SHA256_RE.fullmatch(binary_digest):
            raise GasCityOpsError(f"runtime lock provider {name} binary_sha256 is invalid")
        if effort is not None and record.get("reasoning_effort") != effort:
            raise GasCityOpsError(f"runtime lock provider {name} must use {effort}")
        if name == "codex":
            if record.get("package") != f"@openai/codex@{cli_version}-linux-x64":
                raise GasCityOpsError("runtime lock Codex package does not match cli_version")
            sri = record.get("package_sri")
            if (
                not isinstance(sri, str)
                or re.fullmatch(r"sha512-[A-Za-z0-9+/]+={0,2}", sri) is None
            ):
                raise GasCityOpsError("runtime lock Codex package_sri is invalid")
            archive_digest = record.get("archive_sha256")
            if not isinstance(archive_digest, str) or not SHA256_RE.fullmatch(archive_digest):
                raise GasCityOpsError("runtime lock Codex archive_sha256 is invalid")
            helpers = record.get("helper_sha256")
            if not isinstance(helpers, dict) or set(helpers) != CODEX_REQUIRED_HELPERS:
                raise GasCityOpsError("runtime lock Codex helper set is invalid")
            if any(
                not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)
                for digest in helpers.values()
            ):
                raise GasCityOpsError("runtime lock Codex helper digest is invalid")
        observed = record.get("observed_model")
        receipt = record.get("receipt_sha256")
        receipt_path_value = record.get("receipt_path")
        if (
            not isinstance(receipt_path_value, str)
            or not receipt_path_value
            or Path(receipt_path_value).is_absolute()
            or ".." in Path(receipt_path_value).parts
        ):
            raise GasCityOpsError(
                f"runtime lock provider {name} receipt_path must be safe and relative"
            )
        if observed is None and receipt is not None:
            raise GasCityOpsError(
                f"runtime lock provider {name} cannot have a receipt without an observation"
            )
        receipt_required = require_observed_models or value["status"] in {
            "canary_passed_soaking",
            "production",
        }
        if receipt_required:
            if observed != model:
                raise GasCityOpsError(f"runtime lock provider {name} lacks an exact model receipt")
            if not isinstance(receipt, str) or not SHA256_RE.fullmatch(receipt):
                raise GasCityOpsError(f"runtime lock provider {name} receipt digest is invalid")
            receipt_path = lock_path.parent / receipt_path_value
            receipt_bytes = _regular_file_bytes(
                receipt_path,
                label=f"runtime lock provider {name} receipt",
            )
            if stat.S_IMODE(receipt_path.stat().st_mode) & 0o077:
                raise GasCityOpsError(f"runtime lock provider {name} receipt must be owner-only")
            if _sha256(receipt_bytes) != receipt:
                raise GasCityOpsError(
                    f"runtime lock provider {name} receipt content digest mismatch"
                )
            receipt_value = _load_json_bytes(
                receipt_bytes,
                label=f"runtime lock provider {name} receipt",
            )
            if not isinstance(receipt_value, dict):
                raise GasCityOpsError(
                    f"runtime lock provider {name} receipt must contain one object"
                )
            if (
                receipt_value.get("schema_version") != MODEL_RECEIPT_SCHEMA_VERSION
                or receipt_value.get("status") not in {"pass", "verified"}
                or receipt_value.get("provider") != name
                or receipt_value.get("observed_model") != model
                or receipt_value.get("expected_model", model) != model
                or receipt_value.get("reasoning_effort", effort) != effort
                or receipt_value.get("observed_effort", effort) != effort
            ):
                raise GasCityOpsError(
                    f"runtime lock provider {name} receipt does not prove the locked model"
                )
            transcript_digest = receipt_value.get("transcript_sha256")
            if not isinstance(transcript_digest, str) or not SHA256_RE.fullmatch(transcript_digest):
                raise GasCityOpsError(
                    f"runtime lock provider {name} receipt lacks a transcript digest"
                )
        elif observed not in (None, model):
            raise GasCityOpsError(f"runtime lock provider {name} observed an unexpected model")
    if _validate_promotions:
        _validate_runtime_promotion_records(lock_path, value)
    return value


def _default_runner(
    argv: Sequence[str], cwd: Path, environment: Mapping[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(environment),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _redact(text: str, secrets: Sequence[str]) -> str:
    result = text
    for secret in sorted({item for item in secrets if item}, key=len, reverse=True):
        result = result.replace(secret, "<redacted>")
    return result


def _checked(
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    runner: Runner,
    secrets: Sequence[str] = (),
) -> subprocess.CompletedProcess[str]:
    if any(secret and secret in argument for secret in secrets for argument in argv):
        raise GasCityOpsError("secret material must not appear in command arguments")
    result = runner(tuple(argv), cwd, environment)
    if result.returncode != 0:
        detail = _redact((result.stderr or result.stdout).strip(), secrets)
        if len(detail) > 4096:
            detail = detail[-4096:]
        raise GasCityOpsError(f"command failed ({argv[0]}): {detail}")
    return result


def verify_installed_toolchain(
    city_root: Path,
    lock_path: Path,
    *,
    require_observed_models: bool = False,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Verify installed binaries byte-for-byte against the source-controlled lock."""

    root = _canonical_path(city_root, must_exist=True, label="city root")
    lock = load_runtime_lock(lock_path, require_observed_models=require_observed_models)
    env = dict(os.environ if environment is None else environment)
    evidence: dict[str, Any] = {"status": "pass", "city_root": root.as_posix(), "tools": {}}
    for name in LOCK_REQUIRED_TOOLS:
        binary = root / "bin" / name
        content = _regular_file_bytes(binary, label=f"installed {name}")
        observed_digest = _sha256(content)
        record = lock["tools"][name]
        if observed_digest != record["binary_sha256"]:
            raise GasCityOpsError(
                f"installed {name} digest mismatch: expected {record['binary_sha256']}, "
                f"observed {observed_digest}"
            )
        result = _checked(
            (binary.as_posix(), *TOOL_VERSION_ARGUMENTS[name]),
            cwd=root,
            environment=env,
            runner=runner,
        )
        version_text = (result.stdout or result.stderr).strip()
        version_pattern = re.compile(
            rf"(?<![0-9A-Za-z]){re.escape(record['version'])}(?![0-9A-Za-z])"
        )
        if not version_pattern.search(version_text):
            raise GasCityOpsError(
                f"installed {name} version output does not contain {record['version']!r}"
            )
        evidence["tools"][name] = {
            "version": record["version"],
            "binary_sha256": observed_digest,
            "version_output": version_text,
        }
    canonical_lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    evidence["lock_sha256"] = _sha256(_regular_file_bytes(canonical_lock, label="runtime lock"))
    return evidence


def locked_operation_toolchain_attestation(
    lock_path: Path,
    supplied_tools: Mapping[str, Path],
    *,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Bind an operation to exact installed tools from one deployed city lock.

    Version output alone is deliberately insufficient: every supplied path must
    be the canonical ``city/bin/<name>`` file and its bytes must match the
    runtime lock before an operation can receive this attestation.
    """

    if set(supplied_tools) != {"bd", "dolt"}:
        raise GasCityOpsError("locked operation requires exactly bd and dolt")
    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    city = lock.parent
    verified = verify_installed_toolchain(
        city,
        lock,
        runner=runner,
        environment=environment,
    )
    locked = load_runtime_lock(lock)
    tools: dict[str, dict[str, str]] = {}
    for name in ("bd", "dolt"):
        expected = _canonical_path(
            city / "bin" / name,
            must_exist=True,
            label=f"installed {name}",
        )
        supplied = _canonical_path(
            supplied_tools[name],
            must_exist=True,
            label=f"supplied {name}",
        )
        if supplied != expected:
            raise GasCityOpsError(f"operation must use the exact lock-bound city/bin/{name}")
        tools[name] = {
            "path": expected.as_posix(),
            "version": str(locked["tools"][name]["version"]),
            "binary_sha256": str(verified["tools"][name]["binary_sha256"]),
        }
    return {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock.as_posix(),
        "runtime_lock_sha256": str(verified["lock_sha256"]),
        "tools": tools,
    }


def validate_locked_operation_toolchain_evidence(
    lock_path: Path,
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Reverify a recorded operation toolchain against the deployed city.

    Runtime-lock status and promotion receipts legitimately change after the
    migration, so the historical whole-file lock digest is retained as
    provenance rather than compared with the current mutable lock.  The
    security-relevant tool records are re-bound to the current lock and the
    exact deployed binary bytes every time the evidence is consumed.
    """

    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    # This helper is itself called while promotion evidence is being checked.
    # Revalidating promotion records here would recurse back into the same
    # migration report. All non-promotion lock fields remain fully validated.
    locked = load_runtime_lock(lock, _validate_promotions=False)
    if type(value) is not dict or set(value) != {
        "schema_version",
        "runtime_lock_path",
        "runtime_lock_sha256",
        "tools",
    }:
        raise GasCityOpsError("locked operation toolchain evidence fields are not exact")
    tools = value.get("tools")
    if (
        value.get("schema_version") != taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA
        or value.get("runtime_lock_path") != lock.as_posix()
        or type(value.get("runtime_lock_sha256")) is not str
        or SHA256_RE.fullmatch(value["runtime_lock_sha256"]) is None
        or type(tools) is not dict
        or set(tools) != {"bd", "dolt"}
    ):
        raise GasCityOpsError("locked operation toolchain evidence is invalid")

    normalized: dict[str, dict[str, str]] = {}
    for name in ("bd", "dolt"):
        expected_path = lock.parent / "bin" / name
        record = tools.get(name)
        expected_lock_record = locked["tools"][name]
        if (
            type(record) is not dict
            or set(record) != {"path", "version", "binary_sha256"}
            or record.get("path") != expected_path.as_posix()
            or record.get("version") != expected_lock_record["version"]
            or record.get("binary_sha256") != expected_lock_record["binary_sha256"]
        ):
            raise GasCityOpsError(
                f"locked operation toolchain evidence does not bind city/bin/{name}"
            )
        content = _regular_file_bytes(expected_path, label=f"installed {name}")
        if _sha256(content) != expected_lock_record["binary_sha256"]:
            raise GasCityOpsError(f"locked operation toolchain installed {name} digest mismatch")
        normalized[name] = dict(record)

    return {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock.as_posix(),
        "runtime_lock_sha256": value["runtime_lock_sha256"],
        "tools": normalized,
    }


def _strict_json_object(text: str, *, label: str) -> dict[str, Any]:
    value = _load_json_bytes(text.encode("utf-8"), label=label)
    if type(value) is not dict:
        raise GasCityOpsError(f"{label} must contain exactly one JSON object")
    return value


def _worker_identity_from_environment(
    environment: Mapping[str, str],
) -> tuple[dict[str, str], bool]:
    observed = {
        "rig": environment.get("GC_RIG", ""),
        "beads_prefix": environment.get("GC_BEADS_PREFIX", ""),
        "database": environment.get("GC_DOLT_DATABASE", ""),
    }
    return observed, any(observed.values())


def _classify_worker_identity(observed: Mapping[str, str], *, label: str) -> bool:
    """Return whether a worker is exactly Aegis, rejecting partial identities.

    A fully populated non-Aegis identity belongs to another rig and is ignored.
    Any identity which overlaps Aegis but is incomplete or contradictory is
    unsafe: silently treating it as another rig could permit an Aegis worker to
    race an authority transition.
    """

    expected = LIVE_AUTHORITY_IDENTITY
    populated = {key: value for key, value in observed.items() if value}
    if not populated:
        raise GasCityOpsError(f"{label} lacks a Gas City worker identity")
    if populated == expected:
        return True
    if any(populated.get(key) == value for key, value in expected.items()):
        raise GasCityOpsError(f"{label} has an ambiguous partial Aegis identity")
    if set(populated) != set(expected):
        raise GasCityOpsError(f"{label} has an incomplete Gas City worker identity")
    return False


def _parse_environment_bytes(content: bytes, *, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        entries = content.split(b"\0")
        for entry in entries:
            if not entry:
                continue
            key_bytes, separator, value_bytes = entry.partition(b"=")
            if not separator:
                raise GasCityOpsError(f"{label} contains a malformed entry")
            key = key_bytes.decode("utf-8")
            value = value_bytes.decode("utf-8")
            if key in result:
                raise GasCityOpsError(f"{label} contains duplicate variable {key!r}")
            result[key] = value
    except UnicodeDecodeError as exc:
        raise GasCityOpsError(f"{label} is not valid UTF-8") from exc
    return result


def _supervisor_socket_paths(environment: Mapping[str, str]) -> list[str]:
    raw_home = environment.get("HOME")
    if not raw_home:
        raise GasCityOpsError("gc supervisor proof requires an explicit HOME")
    raw_runtime = environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    normalized: list[Path] = []
    for raw, label in ((raw_runtime, "XDG_RUNTIME_DIR"), (raw_home, "HOME")):
        path = Path(raw).expanduser()
        if not path.is_absolute() or ".." in path.parts:
            raise GasCityOpsError(f"gc supervisor {label} must be an absolute path")
        normalized.append(Path(os.path.normpath(path.as_posix())))
    runtime, home = normalized
    return [
        (runtime / "gc" / "supervisor.sock").as_posix(),
        (home / ".gc" / "supervisor.sock").as_posix(),
    ]


def _validate_supervisor_stopped(
    value: Mapping[str, Any], *, environment: Mapping[str, str]
) -> None:
    required = {
        "schema_version",
        "ok",
        "checked_paths",
        "pid",
        "running",
        "socket_path",
    }
    if (
        not required.issubset(value)
        or value.get("schema_version") != "1"
        or value.get("ok") is not True
        or value.get("checked_paths") != _supervisor_socket_paths(environment)
        or type(value.get("pid")) is not int
        or value.get("pid") != 0
        or value.get("running") is not False
        or value.get("socket_path") != ""
    ):
        raise GasCityOpsError("gc supervisor status does not prove the supervisor is stopped")


def _validate_rig_stopped(value: Mapping[str, Any], *, city: Path) -> None:
    required_root = {"schema_version", "ok", "city_path", "city_name", "rig", "agents"}
    if (
        not required_root.issubset(value)
        or value.get("schema_version") != "1"
        or value.get("ok") is not True
        or value.get("city_path") != city.as_posix()
        or type(value.get("city_name")) is not str
        or type(value.get("rig")) is not dict
        or type(value.get("agents")) is not list
    ):
        raise GasCityOpsError("gc rig status does not describe the exact Aegis city")
    rig = value["rig"]
    required_rig = {"name", "path", "prefix", "suspended", "beads"}
    if (
        not required_rig.issubset(rig)
        or rig.get("name") != LIVE_AUTHORITY_IDENTITY["rig"]
        or rig.get("prefix") != LIVE_AUTHORITY_IDENTITY["beads_prefix"]
        or type(rig.get("suspended")) is not bool
        or type(rig.get("path")) is not str
        or type(rig.get("beads")) is not str
    ):
        raise GasCityOpsError("gc rig status does not prove exact Aegis identity")
    required_agent = {
        "name",
        "qualified_name",
        "runtime_session_name",
        "running",
        "suspended",
        "draining",
        "status",
    }
    for number, agent in enumerate(value["agents"], start=1):
        if (
            type(agent) is not dict
            or not required_agent.issubset(agent)
            or type(agent.get("name")) is not str
            or type(agent.get("qualified_name")) is not str
            or type(agent.get("runtime_session_name")) is not str
            or agent.get("running") is not False
            or agent.get("draining") is not False
            or type(agent.get("suspended")) is not bool
            or type(agent.get("status")) is not str
        ):
            raise GasCityOpsError(f"gc Aegis agent {number} is active or malformed")


def _validated_suspension_state(city: Path) -> dict[str, Any]:
    path = city / ".gc" / "runtime" / "suspension-state.json"
    content = _regular_file_bytes(path, label="Gas City suspension state")
    value = _load_json_bytes(content, label="Gas City suspension state")
    if (
        type(value) is not dict
        or set(value)
        not in (
            {"city", "rigs", "updated_at"},
            {"city", "rigs", "agents", "updated_at"},
        )
        or value.get("city") != {"suspended": True}
        or value.get("rigs") != {"aegis": {"suspended": True}}
        or ("agents" in value and value.get("agents") != {})
    ):
        raise GasCityOpsError(
            "Gas City suspension state does not explicitly suspend city and Aegis"
        )
    _utc_timestamp(value["updated_at"], label="Gas City suspension updated_at")
    return {
        "path": path.relative_to(city).as_posix(),
        "sha256": _sha256(content),
        "city_suspended": True,
        "aegis_suspended": True,
        "updated_at": value["updated_at"],
    }


def _validate_no_active_sessions(value: Mapping[str, Any]) -> None:
    filters = value.get("filters")
    if (
        set(value) != {"schema_version", "ok", "filters", "sessions", "summary"}
        or value.get("schema_version") != "1"
        or value.get("ok") is not True
        or type(filters) is not dict
        or not set(filters).issubset({"state", "template"})
        or filters.get("state") != "active"
        or ("template" in filters and type(filters["template"]) is not str)
        or value.get("sessions") != []
        or type(value.get("summary")) is not dict
        or set(value["summary"]) != {"total", "active", "suspended", "closed"}
        or any(type(value["summary"].get(key)) is not int for key in value["summary"])
        or value["summary"].get("total") != 0
        or value["summary"].get("active") != 0
    ):
        raise GasCityOpsError("gc session list does not prove an empty active Aegis set")


def _probe_aegis_stopped_workers(
    city_root: Path,
    lock_path: Path,
    *,
    gc_binary: Path | None = None,
    docker_binary: Path = Path("/usr/bin/docker"),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    """Directly prove that no exact or ambiguous Aegis worker is live."""

    city = _canonical_path(city_root, must_exist=True, label="city root")
    if city.is_symlink() or not city.is_dir():
        raise GasCityOpsError("city root must be a real non-symlink directory")
    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    if lock != city / "runtime-lock.json":
        raise GasCityOpsError("stopped-worker proof requires the exact city runtime-lock.json")
    locked = load_runtime_lock(lock)
    expected_gc = city / "bin" / "gc"
    gc = _canonical_path(
        expected_gc if gc_binary is None else gc_binary,
        must_exist=True,
        label="gc binary",
    )
    if gc != expected_gc:
        raise GasCityOpsError("stopped-worker proof requires the exact city/bin/gc")
    if (
        _sha256(_regular_file_bytes(gc, label="gc binary"))
        != locked["tools"]["gc"]["binary_sha256"]
    ):
        raise GasCityOpsError("stopped-worker gc binary does not match the runtime lock")
    docker = _canonical_path(docker_binary, must_exist=True, label="Docker binary")
    env = dict(os.environ if environment is None else environment)
    # gc 1.3.5 can fall back from its native read path to the bd store. Force
    # that lookup to the manifest-verified city binary instead of depending on
    # an attended operator shell (or accepting another same-named executable).
    env["PATH"] = f"{city / 'bin'}:/usr/bin:/bin"
    # External HQ authentication is needed by the pinned gc session probe, but
    # Docker inspection has no reason to inherit either the secret itself or
    # the attended secret-file path.  Keep the credential boundary narrower
    # than this composite proof instead of leaking it to every child process.
    nonsecret_env = {
        key: value
        for key, value in env.items()
        if key
        not in {
            "BEADS_DOLT_PASSWORD",
            "DOLT_CLI_PASSWORD",
            "GC_DOLT_PASSWORD",
            "GAS_CITY_HQ_DOLT_PASSWORD_FILE",
        }
    }

    supervisor = _strict_json_object(
        _checked(
            (gc.as_posix(), "--city", city.as_posix(), "supervisor", "status", "--json"),
            cwd=city,
            environment=env,
            runner=runner,
        ).stdout,
        label="gc supervisor status",
    )
    _validate_supervisor_stopped(supervisor, environment=env)
    rig_status = _strict_json_object(
        _checked(
            (gc.as_posix(), "--city", city.as_posix(), "rig", "status", "aegis", "--json"),
            cwd=city,
            environment=env,
            runner=runner,
        ).stdout,
        label="gc rig status",
    )
    _validate_rig_stopped(rig_status, city=city)
    suspension_state = _validated_suspension_state(city)
    sessions = _strict_json_object(
        _checked(
            (
                gc.as_posix(),
                "--city",
                city.as_posix(),
                "--rig",
                "aegis",
                "session",
                "list",
                "--state",
                "active",
                "--json",
            ),
            cwd=city,
            environment=env,
            runner=runner,
        ).stdout,
        label="gc active session list",
    )
    _validate_no_active_sessions(sessions)

    container_ids = _checked(
        (
            docker.as_posix(),
            "ps",
            "--filter",
            "label=com.gascity.boundary=isolated-worker",
            "--format",
            "{{.ID}}",
        ),
        cwd=city,
        environment=nonsecret_env,
        runner=runner,
    ).stdout.splitlines()
    if len(container_ids) != len(set(container_ids)) or any(
        re.fullmatch(r"[0-9a-f]{12,64}", item) is None for item in container_ids
    ):
        raise GasCityOpsError("Docker returned malformed or duplicate worker container IDs")
    for container_id in container_ids:
        inspected = _strict_json_object(
            _checked(
                (docker.as_posix(), "inspect", "--format", "{{json .}}", container_id),
                cwd=city,
                environment=nonsecret_env,
                runner=runner,
            ).stdout,
            label=f"Docker worker inspection {container_id}",
        )
        config = inspected.get("Config")
        state = inspected.get("State")
        name = inspected.get("Name")
        if type(config) is not dict or type(state) is not dict or type(name) is not str:
            raise GasCityOpsError("Docker worker inspection has an unexpected shape")
        raw_env = config.get("Env")
        labels = config.get("Labels")
        if type(raw_env) is not list or any(type(item) is not str for item in raw_env):
            raise GasCityOpsError("Docker worker environment is malformed")
        if type(labels) is not dict or labels.get("com.gascity.boundary") != "isolated-worker":
            raise GasCityOpsError("Docker worker lost its isolated-worker boundary label")
        parsed_env: dict[str, str] = {}
        for item in raw_env:
            key, separator, value = item.partition("=")
            if not separator or key in parsed_env:
                raise GasCityOpsError("Docker worker environment is ambiguous")
            parsed_env[key] = value
        identity, has_identity = _worker_identity_from_environment(parsed_env)
        if not has_identity:
            label_identity = {
                "rig": str(labels.get("com.gascity.rig", "")),
                "beads_prefix": str(labels.get("com.gascity.beads-prefix", "")),
                "database": str(labels.get("com.gascity.database", "")),
            }
            identity = label_identity
        exact_aegis = _classify_worker_identity(identity, label=f"Docker worker {container_id}")
        if exact_aegis and state.get("Running") is True:
            raise GasCityOpsError(f"active Aegis provider container detected: {name}")
        if exact_aegis:
            raise GasCityOpsError(
                f"Aegis provider container appeared in Docker's active set: {name}"
            )

    proc = _canonical_path(proc_root, must_exist=True, label="proc root")
    if not proc.is_dir():
        raise GasCityOpsError("proc root must be a directory")
    for process in sorted(proc.iterdir(), key=lambda item: item.name):
        if not process.name.isdigit() or int(process.name) == os.getpid():
            continue
        try:
            cmdline_bytes = (process / "cmdline").read_bytes()
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            raise GasCityOpsError(
                f"cannot inspect process {process.name} while proving workers stopped"
            ) from exc
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ESRCH}:
                continue
            raise GasCityOpsError(
                f"cannot inspect process {process.name} while proving workers stopped"
            ) from exc
        argv_basenames = {
            Path(argument.decode("utf-8", errors="surrogateescape")).name
            for argument in cmdline_bytes.split(b"\0")
            if argument
        }
        if not {"provider-supervisor.py", "provider-container"} & argv_basenames:
            continue
        try:
            process_env = _parse_environment_bytes(
                (process / "environ").read_bytes(),
                label=f"provider process {process.name} environment",
            )
        except (FileNotFoundError, ProcessLookupError):
            # The process exited after its provider command line was observed.
            # A vanished PID is not an active worker; all surviving/reused PIDs
            # still have to pass the exact environment-identity proof below.
            continue
        except PermissionError as exc:
            raise GasCityOpsError(
                f"cannot inspect provider process {process.name} identity"
            ) from exc
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ESRCH}:
                continue
            raise GasCityOpsError(
                f"cannot inspect provider process {process.name} identity"
            ) from exc
        identity, has_identity = _worker_identity_from_environment(process_env)
        if not has_identity:
            raise GasCityOpsError(
                f"provider process {process.name} lacks an exact Gas City identity"
            )
        if _classify_worker_identity(identity, label=f"provider process {process.name}"):
            raise GasCityOpsError(f"active Aegis provider process detected: {process.name}")

    return {
        "supervisor_running": False,
        "active_provider_containers": [],
        "active_sessions": [],
        "suspension_state": suspension_state,
    }


def capture_aegis_stopped_workers_evidence(
    city_root: Path,
    lock_path: Path,
    output_path: Path,
    *,
    gc_binary: Path | None = None,
    docker_binary: Path = Path("/usr/bin/docker"),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    proc_root: Path = Path("/proc"),
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Capture real, append-only stopped-worker evidence for exact Aegis."""

    city = _canonical_path(city_root, must_exist=True, label="city root")
    observed = _probe_aegis_stopped_workers(
        city,
        lock_path,
        gc_binary=gc_binary,
        docker_binary=docker_binary,
        runner=runner,
        environment=environment,
        proc_root=proc_root,
    )
    destination = _safe_evidence_output(city, output_path, label="stopped-worker output")
    expected_root = city / "runtime" / "evidence" / "workers"
    if not _is_within(destination, expected_root) or destination == expected_root:
        raise GasCityOpsError(
            "stopped-worker output must be a file beneath runtime/evidence/workers"
        )
    value = {
        "schema_version": 1,
        "kind": STOPPED_WORKERS_KIND,
        "status": "pass",
        "rig": LIVE_AUTHORITY_IDENTITY["rig"],
        "observed_at": _format_utc(clock()),
        **observed,
    }
    _, digest = _write_append_only_json(destination, value)
    return {**value, "evidence_path": destination.as_posix(), "evidence_sha256": digest}


@dataclasses.dataclass(frozen=True)
class AegisStoppedWorkersHook:
    """Lifecycle hook which re-probes real state at every commit phase."""

    city_root: Path
    lock_path: Path
    gc_binary: Path | None = None
    docker_binary: Path = Path("/usr/bin/docker")
    runner: Runner = _default_runner
    environment: Mapping[str, str] | None = None
    proc_root: Path = Path("/proc")

    def __call__(self, phase: str, path: Path, evidence: Mapping[str, Any]) -> bool:
        if phase not in STOPPED_WORKER_PHASES:
            raise GasCityOpsError(f"unexpected stopped-worker hook phase: {phase}")
        content = _regular_file_bytes(Path(path), label="stopped-worker hook evidence")
        loaded = _load_json_bytes(content, label="stopped-worker hook evidence")
        if type(loaded) is not dict or loaded != dict(evidence):
            raise GasCityOpsError("stopped-worker evidence changed before lifecycle commit")
        state = _probe_aegis_stopped_workers(
            self.city_root,
            self.lock_path,
            gc_binary=self.gc_binary,
            docker_binary=self.docker_binary,
            runner=self.runner,
            environment=self.environment,
            proc_root=self.proc_root,
        )
        return state == {
            "supervisor_running": False,
            "active_provider_containers": [],
            "active_sessions": [],
            "suspension_state": evidence.get("suspension_state"),
        }


def _stable_read(path: Path, *, label: str) -> tuple[bytes, os.stat_result]:
    if path.is_symlink() or not path.is_file():
        raise GasCityOpsError(f"{label} must be a regular non-symlink file: {path}")
    before = path.stat()
    content = path.read_bytes()
    after = path.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(content) != after.st_size:
        raise GasCityOpsError(f"{label} changed while it was being captured")
    return content, after


def taskmaster_source_fingerprint(repo_root: Path) -> dict[str, Any]:
    """Return a stable, parsed fingerprint for the Taskmaster authority file."""

    repo = _canonical_path(repo_root, must_exist=True, label="repository root")
    source = repo / ".taskmaster" / "tasks" / "tasks.json"
    content, source_stat = _stable_read(source, label="Taskmaster source")
    parsed = _load_json_bytes(content, label="Taskmaster source")
    if not isinstance(parsed, dict):
        raise GasCityOpsError("Taskmaster source must contain one JSON object")
    return {
        "sha256": _sha256(content),
        "size_bytes": len(content),
        "mtime_ns": source_stat.st_mtime_ns,
    }


def capture_taskmaster_snapshot(
    repo_root: Path,
    output_dir: Path,
    *,
    captured_at: str,
    git_head: str,
    dirty_paths: Sequence[str],
    health_evidence: str,
    expected_source_sha256: str,
) -> dict[str, Any]:
    """Atomically freeze Taskmaster bytes and their cutover boundary.

    Callers obtain Git and full-graph health evidence immediately before this
    function.  The output must live outside the project so an agent worktree
    cannot overwrite rollback evidence.
    """

    repo = _canonical_path(repo_root, must_exist=True, label="repository root")
    destination = _canonical_path(output_dir, must_exist=False, label="snapshot directory")
    if _is_within(destination, repo) or _is_within(repo, destination):
        raise GasCityOpsError("snapshot directory and repository must be disjoint")
    if not re.fullmatch(r"[0-9a-f]{40,64}", git_head):
        raise GasCityOpsError("git_head must be a full hexadecimal commit ID")
    if not health_evidence.strip():
        raise GasCityOpsError("Taskmaster full-graph health evidence is required")
    if not SHA256_RE.fullmatch(expected_source_sha256):
        raise GasCityOpsError("expected Taskmaster source SHA-256 is invalid")
    try:
        parsed_time = dt.datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GasCityOpsError("captured_at must be an RFC3339 timestamp") from exc
    if parsed_time.tzinfo is None or parsed_time.utcoffset() != dt.timedelta(0):
        raise GasCityOpsError("captured_at must use UTC")

    source = repo / ".taskmaster" / "tasks" / "tasks.json"
    content, source_stat = _stable_read(source, label="Taskmaster source")
    if _sha256(content) != expected_source_sha256:
        raise GasCityOpsError(
            "Taskmaster source changed while cutover evidence was being collected"
        )
    parsed = _load_json_bytes(content, label="Taskmaster source")
    if not isinstance(parsed, dict):
        raise GasCityOpsError("Taskmaster source must contain one JSON object")
    normalized_dirty = sorted(set(dirty_paths))
    if any(Path(item).is_absolute() or ".." in Path(item).parts for item in normalized_dirty):
        raise GasCityOpsError("dirty paths must be safe repository-relative paths")

    manifest = {
        "schema_version": 1,
        "status": "frozen",
        "captured_at": captured_at,
        "source": {
            "repo_root": repo.as_posix(),
            "relative_path": ".taskmaster/tasks/tasks.json",
            "sha256": _sha256(content),
            "size_bytes": len(content),
            "mtime_ns": source_stat.st_mtime_ns,
        },
        "git": {"head": git_head, "dirty_paths": normalized_dirty},
        "taskmaster_health_sha256": _sha256(health_evidence.encode("utf-8")),
    }
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.parent.is_symlink():
        raise GasCityOpsError("snapshot parent directory must not be a symlink")
    try:
        destination.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise GasCityOpsError("snapshot directory already exists; evidence is append-only") from exc
    except OSError as exc:
        raise GasCityOpsError(f"cannot create snapshot directory: {destination}") from exc
    _atomic_write(destination / "tasks.json", content)
    _atomic_write(
        destination / "taskmaster-health.txt",
        health_evidence.encode("utf-8"),
    )
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(destination / "snapshot-manifest.json", manifest_bytes)
    return manifest


def load_taskmaster_snapshot(snapshot_dir: Path) -> tuple[bytes, dict[str, Any]]:
    """Load and re-hash a frozen Taskmaster cutover snapshot."""

    root = _canonical_path(snapshot_dir, must_exist=True, label="snapshot directory")
    if not root.is_dir() or root.is_symlink():
        raise GasCityOpsError("snapshot directory must be a non-symlink directory")
    manifest_value = _load_json_bytes(
        _regular_file_bytes(root / "snapshot-manifest.json", label="snapshot manifest"),
        label="snapshot manifest",
    )
    if not isinstance(manifest_value, dict):
        raise GasCityOpsError("snapshot manifest must contain one JSON object")
    if manifest_value.get("schema_version") != 1 or manifest_value.get("status") != "frozen":
        raise GasCityOpsError("snapshot manifest is not a frozen schema-version 1 snapshot")

    source = manifest_value.get("source")
    if not isinstance(source, dict):
        raise GasCityOpsError("snapshot manifest source must be an object")
    if source.get("relative_path") != ".taskmaster/tasks/tasks.json":
        raise GasCityOpsError("snapshot manifest has an unexpected Taskmaster source path")
    expected_digest = source.get("sha256")
    expected_size = source.get("size_bytes")
    if not isinstance(expected_digest, str) or not SHA256_RE.fullmatch(expected_digest):
        raise GasCityOpsError("snapshot manifest source SHA-256 is invalid")
    if not isinstance(expected_size, int) or expected_size < 1:
        raise GasCityOpsError("snapshot manifest source size is invalid")

    source_bytes = _regular_file_bytes(root / "tasks.json", label="snapshot tasks")
    if len(source_bytes) != expected_size or _sha256(source_bytes) != expected_digest:
        raise GasCityOpsError("snapshot Taskmaster bytes do not match the frozen manifest")
    parsed_source = _load_json_bytes(source_bytes, label="snapshot tasks")
    if not isinstance(parsed_source, dict):
        raise GasCityOpsError("snapshot Taskmaster source must contain one JSON object")

    health_digest = manifest_value.get("taskmaster_health_sha256")
    if not isinstance(health_digest, str) or not SHA256_RE.fullmatch(health_digest):
        raise GasCityOpsError("snapshot Taskmaster health SHA-256 is invalid")
    health_bytes = _regular_file_bytes(
        root / "taskmaster-health.txt", label="snapshot Taskmaster health"
    )
    if not health_bytes.strip() or _sha256(health_bytes) != health_digest:
        raise GasCityOpsError("snapshot Taskmaster health evidence does not match the manifest")
    return source_bytes, manifest_value


def read_private_secret_file_from_environment(environment: Mapping[str, str], variable: str) -> str:
    """Read one private single-line secret from a path supplied in the environment."""

    raw_path = environment.get(variable, "")
    if not raw_path:
        raise GasCityOpsError(f"{variable} must name a private secret file")
    configured = Path(raw_path).expanduser()
    if not configured.is_absolute() or configured.is_symlink():
        raise GasCityOpsError(f"{variable} must name an absolute non-symlink file")
    path = _canonical_path(configured, must_exist=True, label=variable)
    if path != configured:
        raise GasCityOpsError(f"{variable} path must be canonical")
    metadata = path.stat()
    if metadata.st_uid != os.getuid() or metadata.st_nlink != 1:
        raise GasCityOpsError(f"{variable} must be owned by the current user and singly linked")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise GasCityOpsError(f"{variable} must not have group/world permissions")
    content = _regular_file_bytes(path, label=variable)
    try:
        value = content.decode("utf-8").rstrip("\n")
    except UnicodeDecodeError as exc:
        raise GasCityOpsError(f"{variable} is not valid UTF-8") from exc
    if "\n" in value or "\r" in value or not 32 <= len(value) <= 128:
        raise GasCityOpsError(f"{variable} must contain one 32-128 character line")
    if any(
        character.isspace() or ord(character) < 33 or ord(character) > 126 for character in value
    ):
        raise GasCityOpsError(f"{variable} contains unsupported characters")
    return value


def write_private_json_evidence(
    path: Path,
    value: Mapping[str, Any],
    *,
    exclusive: bool = False,
) -> str:
    """Atomically write a controlled evidence object and return its SHA-256."""

    destination = _canonical_path(path, must_exist=False, label="evidence output")
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(destination, content, exclusive=exclusive)
    return _sha256(content)


def create_private_evidence_directory(path: Path) -> Path:
    """Create a new owner-only evidence directory without replacing prior runs."""

    destination = _canonical_path(path, must_exist=False, label="evidence directory")
    _make_private_parents(destination.parent)
    if destination.parent.is_symlink() or stat.S_IMODE(destination.parent.stat().st_mode) & 0o077:
        raise GasCityOpsError("evidence parent directory must be owner-only and non-symlink")
    try:
        destination.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise GasCityOpsError("evidence directory already exists; evidence is append-only") from exc
    except OSError as exc:
        raise GasCityOpsError(f"cannot create evidence directory: {destination}") from exc
    return destination


def write_private_evidence_bytes(root: Path, relative_name: str, content: bytes) -> str:
    """Write one immutable private evidence artifact beneath an evidence root."""

    evidence_root = _canonical_path(root, must_exist=True, label="evidence directory")
    if (
        not evidence_root.is_dir()
        or evidence_root.is_symlink()
        or stat.S_IMODE(evidence_root.stat().st_mode) & 0o077
    ):
        raise GasCityOpsError("evidence directory must be owner-only and non-symlink")
    relative = Path(relative_name)
    if not relative_name or relative.is_absolute() or ".." in relative.parts:
        raise GasCityOpsError("evidence artifact name must be safe and relative")
    destination = evidence_root / relative
    if not _is_within(destination, evidence_root):
        raise GasCityOpsError("evidence artifact escaped its run directory")
    return_digest = _sha256(content)
    _atomic_write(destination, content, exclusive=True)
    return return_digest


_AEGIS_BEADS_INIT_POINTER_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "repository_root",
        "git_common_dir",
        "runtime_lock_path",
        "runtime_lock_sha256",
        "run_id",
        "evidence_directory",
        "staging_directory",
        "prepared_evidence_sha256",
        "beads_tree_sha256",
        "beads_manifest_sha256",
        "metadata_sha256",
        "config_sha256",
        "project_id",
        "empty_target",
        "repository_before",
        "exclude_before_sha256",
        "exclude_after_sha256",
        "final_manifest_sha256",
    }
)
_AEGIS_BEADS_PROJECT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
_AEGIS_BEADS_INIT_EMPTY_COUNTS = {
    "issue_count": 0,
    "working_set_changes": 1,
    "expected_config_changes": 1,
    "unexpected_working_changes": 0,
    "branch_count": 1,
    "main_branch_count": 1,
}


def _private_repository_atomic_write(
    path: Path,
    content: bytes,
    *,
    mode: int,
    exclusive: bool = False,
) -> None:
    """Atomically replace one Git-internal file without chmodding its parent."""

    parent = path.parent
    try:
        parent_metadata = parent.lstat()
    except OSError as exc:
        raise GasCityOpsError(f"cannot inspect repository metadata directory: {parent}") from exc
    if parent.is_symlink() or not stat.S_ISDIR(parent_metadata.st_mode):
        raise GasCityOpsError("repository metadata parent must be one real directory")
    if parent_metadata.st_uid != os.getuid() or stat.S_IMODE(parent_metadata.st_mode) & 0o022:
        raise GasCityOpsError("repository metadata parent is not owner controlled")
    if path.is_symlink():
        raise GasCityOpsError(f"repository metadata output must not be a symlink: {path}")
    try:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
        temporary = Path(temporary_name)
        try:
            os.fchmod(fd, mode)
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            if exclusive:
                try:
                    os.link(temporary, path, follow_symlinks=False)
                except FileExistsError as exc:
                    raise GasCityOpsError(
                        f"repository metadata appeared concurrently: {path}"
                    ) from exc
                temporary.unlink()
            else:
                os.replace(temporary, path)
            directory_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise
    except OSError as exc:
        raise GasCityOpsError(f"cannot atomically update repository metadata: {path}") from exc


def _read_repository_file(path: Path, *, label: str, maximum: int = 1024 * 1024) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GasCityOpsError(f"cannot inspect {label}: {path}") from exc
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise GasCityOpsError(f"{label} must be one real regular file")
    if metadata.st_uid != os.getuid() or metadata.st_nlink != 1:
        raise GasCityOpsError(f"{label} must be singly linked and owned by the current user")
    if stat.S_IMODE(metadata.st_mode) & 0o022:
        raise GasCityOpsError(f"{label} must not be group/world writable")
    if metadata.st_size > maximum:
        raise GasCityOpsError(f"{label} is unexpectedly large")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GasCityOpsError(f"cannot read {label}: {path}") from exc


def _canonical_evidence_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _rename_directory_noreplace(source: Path, destination: Path) -> None:
    """Atomically publish a directory without ever replacing an existing path."""

    if source.parent.stat().st_dev != destination.parent.stat().st_dev:
        raise GasCityOpsError("Beads staging and target directories are not on one filesystem")
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise GasCityOpsError("atomic no-replace directory publication is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    at_fdcwd = -100
    rename_noreplace = 1
    result = renameat2(
        at_fdcwd,
        os.fsencode(source),
        at_fdcwd,
        os.fsencode(destination),
        rename_noreplace,
    )
    if result != 0:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise GasCityOpsError("Aegis .beads appeared during atomic publication")
        if error in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP}:
            raise GasCityOpsError("atomic no-replace directory publication is unavailable")
        raise GasCityOpsError(f"atomic Aegis .beads publication failed with errno {error}")
    parent_fd = os.open(destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def _secure_primary_repository(target_repo: Path) -> task_authority.RepositoryIdentity:
    configured = target_repo.expanduser()
    if not configured.is_absolute() or configured.is_symlink():
        raise GasCityOpsError("Aegis target repository must be one absolute non-symlink path")
    requested = _canonical_path(configured, must_exist=True, label="Aegis target repository")
    if requested != configured:
        raise GasCityOpsError("Aegis target repository path must be canonical")
    try:
        identity = task_authority.repository_identity(requested)
    except task_authority.TaskAuthorityError as exc:
        raise GasCityOpsError(f"cannot prove primary Aegis repository identity: {exc}") from exc
    if requested != identity.repository_root:
        raise GasCityOpsError(
            "Aegis Beads initialization must run against the primary checkout, not a linked worktree"
        )
    dot_git = requested / ".git"
    try:
        metadata = dot_git.lstat()
    except OSError as exc:
        raise GasCityOpsError("cannot inspect primary Aegis Git directory") from exc
    if dot_git.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise GasCityOpsError("primary Aegis .git must be one real directory")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise GasCityOpsError("primary Aegis .git is not owner controlled")
    return identity


def _locked_initialization_tool(
    binary: Path,
    *,
    name: str,
    lock: Mapping[str, Any],
) -> Path:
    configured = binary.expanduser()
    if not configured.is_absolute() or configured.is_symlink():
        raise GasCityOpsError(f"locked {name} binary must be an absolute non-symlink path")
    path = _canonical_path(configured, must_exist=True, label=f"locked {name} binary")
    if path != configured:
        raise GasCityOpsError(f"locked {name} binary path must be canonical")
    content = _regular_file_bytes(path, label=f"locked {name} binary")
    if stat.S_IMODE(path.stat().st_mode) & 0o111 == 0:
        raise GasCityOpsError(f"locked {name} binary is not executable")
    if _sha256(content) != lock["tools"][name]["binary_sha256"]:
        raise GasCityOpsError(f"locked {name} binary digest mismatch")
    return path


def _initialization_environment(home: Path, password: str) -> dict[str, str]:
    directories = {
        "HOME": home,
        "XDG_CONFIG_HOME": home / "xdg-config",
        "XDG_CACHE_HOME": home / "xdg-cache",
        "XDG_DATA_HOME": home / "xdg-data",
        "TMPDIR": home / "tmp",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
    return {
        **{name: path.as_posix() for name, path in directories.items()},
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CI": "true",
        "BD_NON_INTERACTIVE": "1",
        "BEADS_NO_DAEMON": "1",
        # bd 1.1.0 otherwise attempts a periodic Dolt-native backup from
        # read-only commands such as `bd export`.  The scoped Aegis account is
        # intentionally not a BACKUP_ADMIN account, so the attempt both emits
        # a warning and creates an unproven `.beads/backup` directory.  Gas
        # City owns attended backup/restore evidence; keep bd's opportunistic
        # backup path disabled for the entire initialization transaction.
        "BD_BACKUP_ENABLED": "false",
        "BEADS_ACTOR": "gas-city-initializer",
        "BEADS_DOLT_SERVER_HOST": AEGIS_BEADS_INIT_HOST,
        "BEADS_DOLT_SERVER_PORT": str(AEGIS_BEADS_INIT_PORT),
        "BEADS_DOLT_SERVER_USER": AEGIS_BEADS_INIT_USER,
        "BEADS_DOLT_SERVER_DATABASE": AEGIS_BEADS_INIT_DATABASE,
        "BEADS_DOLT_PASSWORD": password,
        "DOLT_CLI_PASSWORD": password,
    }


def _initialization_nonsecret_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        key: value
        for key, value in environment.items()
        if key not in {"BEADS_DOLT_PASSWORD", "DOLT_CLI_PASSWORD"}
    }


def _validate_initialization_versions(
    *,
    bd_binary: Path,
    dolt_binary: Path,
    cwd: Path,
    environment: Mapping[str, str],
    runner: Runner,
    password: str,
) -> dict[str, str]:
    bd_result = _checked(
        [bd_binary.as_posix(), "--version"],
        cwd=cwd,
        environment=environment,
        runner=runner,
        secrets=(password,),
    )
    dolt_result = _checked(
        [dolt_binary.as_posix(), "version"],
        cwd=cwd,
        environment=environment,
        runner=runner,
        secrets=(password,),
    )
    bd_version = bd_result.stdout.strip()
    dolt_version = dolt_result.stdout.strip()
    if bd_version != AEGIS_BEADS_INIT_BD_VERSION_OUTPUT:
        raise GasCityOpsError("Beads initialization requires exact bd 1.1.0")
    if dolt_version != AEGIS_BEADS_INIT_DOLT_VERSION_OUTPUT:
        raise GasCityOpsError("Beads initialization requires exact Dolt 2.2.0")
    return {"bd": bd_version, "dolt": dolt_version}


def _disable_initialization_metrics(
    *,
    bd_binary: Path,
    cwd: Path,
    environment: Mapping[str, str],
    runner: Runner,
) -> None:
    _checked(
        [bd_binary.as_posix(), "metrics", "off", "--quiet"],
        cwd=cwd,
        environment=environment,
        runner=runner,
    )


def _git_output(
    git_binary: Path,
    repository: Path,
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str],
    runner: Runner,
) -> str:
    return _checked(
        [git_binary.as_posix(), "-C", repository.as_posix(), *arguments],
        cwd=repository,
        environment=environment,
        runner=runner,
    ).stdout


def _untracked_content_digest(repository: Path, names: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for raw in sorted(names):
        relative = Path(raw)
        if (
            not raw
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.parts[0] in {".git", ".beads"}
        ):
            raise GasCityOpsError("Git returned an unsafe untracked path")
        path = repository / relative
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise GasCityOpsError("cannot fingerprint untracked Aegis work") from exc
        digest.update(os.fsencode(raw))
        digest.update(b"\0")
        if stat.S_ISREG(metadata.st_mode):
            digest.update(b"file\0")
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
        elif stat.S_ISLNK(metadata.st_mode):
            digest.update(b"symlink\0")
            digest.update(os.fsencode(os.readlink(path)))
        else:
            raise GasCityOpsError("untracked Aegis work contains an unsupported file type")
        digest.update(b"\0")
    return digest.hexdigest()


def _would_be_hidden_by_stealth(relative_name: str) -> bool:
    path = Path(relative_name)
    parts = path.parts
    return bool(
        relative_name == ".claude/settings.local.json"
        or ".dolt" in parts
        or path.name.endswith(".db")
        or ".beads-credential-key" in parts
        or (len(parts) >= 2 and parts[0] == ".beads" and parts[1] == "proxieddb")
    )


def _repository_work_fingerprint(
    repository: Path,
    *,
    git_binary: Path,
    environment: Mapping[str, str],
    runner: Runner,
    reject_stealth_conflicts: bool,
    ignore_beads: bool,
) -> dict[str, Any]:
    head = _git_output(
        git_binary,
        repository,
        ("rev-parse", "--verify", "HEAD"),
        environment=environment,
        runner=runner,
    ).strip()
    if GIT_OBJECT_RE.fullmatch(head) is None:
        raise GasCityOpsError("Aegis repository HEAD is not one exact Git object")
    symbolic_head = _git_output(
        git_binary,
        repository,
        ("rev-parse", "--symbolic-full-name", "HEAD"),
        environment=environment,
        runner=runner,
    ).strip()
    if not symbolic_head.startswith("refs/"):
        raise GasCityOpsError("Aegis repository must have a named primary branch")
    index = _git_output(
        git_binary,
        repository,
        ("ls-files", "--stage", "-z"),
        environment=environment,
        runner=runner,
    ).encode("utf-8", "surrogateescape")
    worktree_diff = _git_output(
        git_binary,
        repository,
        ("diff", "--binary", "--no-ext-diff"),
        environment=environment,
        runner=runner,
    ).encode("utf-8", "surrogateescape")
    index_diff = _git_output(
        git_binary,
        repository,
        ("diff", "--cached", "--binary", "--no-ext-diff"),
        environment=environment,
        runner=runner,
    ).encode("utf-8", "surrogateescape")
    raw_status = _git_output(
        git_binary,
        repository,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
        environment=environment,
        runner=runner,
    )
    untracked_output = _git_output(
        git_binary,
        repository,
        ("ls-files", "--others", "--exclude-standard", "-z"),
        environment=environment,
        runner=runner,
    )
    untracked = [name for name in untracked_output.split("\0") if name]
    if ignore_beads:
        untracked = [name for name in untracked if Path(name).parts[0] != ".beads"]
        status_records = [record for record in raw_status.split("\0") if record]
        raw_status = "\0".join(
            record
            for record in status_records
            if not (
                len(record) >= 4 and record[:2] == "??" and Path(record[3:]).parts[0] == ".beads"
            )
        )
        if raw_status:
            raw_status += "\0"
    status_bytes = raw_status.encode("utf-8", "surrogateescape")
    if reject_stealth_conflicts and any(_would_be_hidden_by_stealth(name) for name in untracked):
        raise GasCityOpsError(
            "Beads stealth exclusions would hide preexisting untracked Aegis work"
        )
    return {
        "head": head,
        "symbolic_head": symbolic_head,
        "index_sha256": _sha256(index),
        "worktree_diff_sha256": _sha256(worktree_diff),
        "index_diff_sha256": _sha256(index_diff),
        "status_sha256": _sha256(status_bytes),
        "untracked_count": len(untracked),
        "untracked_content_sha256": _untracked_content_digest(repository, untracked),
    }


def _normalize_and_manifest_beads_tree(
    beads_dir: Path,
    *,
    password: str,
    normalize: bool,
    endpoint_bound: bool,
) -> tuple[list[dict[str, Any]], str, str, str]:
    try:
        root_metadata = beads_dir.lstat()
    except OSError as exc:
        raise GasCityOpsError("initialized staging repo did not produce .beads") from exc
    if beads_dir.is_symlink() or not stat.S_ISDIR(root_metadata.st_mode):
        raise GasCityOpsError("initialized .beads must be one real directory")
    if root_metadata.st_uid != os.getuid():
        raise GasCityOpsError("initialized .beads is not owned by the current user")

    paths: list[Path] = [beads_dir]
    for root, directories, files in os.walk(beads_dir, topdown=True, followlinks=False):
        root_path = Path(root)
        for name in sorted((*directories, *files)):
            paths.append(root_path / name)
    total_bytes = 0
    for path in paths:
        metadata = path.lstat()
        if metadata.st_uid != os.getuid():
            raise GasCityOpsError("initialized .beads contains a foreign-owned entry")
        if stat.S_ISLNK(metadata.st_mode):
            raise GasCityOpsError("initialized .beads must not contain symlinks")
        if stat.S_ISDIR(metadata.st_mode):
            if normalize:
                os.chmod(path, 0o700)
            elif stat.S_IMODE(metadata.st_mode) != 0o700:
                raise GasCityOpsError("published .beads directories must be mode 0700")
        elif stat.S_ISREG(metadata.st_mode):
            if metadata.st_nlink != 1:
                raise GasCityOpsError("initialized .beads must not contain hard-linked files")
            if metadata.st_size > AEGIS_BEADS_INIT_MAX_FILE_BYTES:
                raise GasCityOpsError("initialized .beads contains an unexpectedly large file")
            total_bytes += metadata.st_size
            if total_bytes > AEGIS_BEADS_INIT_MAX_FILE_BYTES:
                raise GasCityOpsError("initialized .beads tree is unexpectedly large")
            content = path.read_bytes()
            if password.encode("utf-8") in content:
                raise GasCityOpsError("bd persisted the target Dolt credential in staging")
            if normalize:
                os.chmod(path, 0o600)
            elif stat.S_IMODE(metadata.st_mode) != 0o600:
                raise GasCityOpsError("published .beads files must be mode 0600")
        else:
            raise GasCityOpsError("initialized .beads contains an unsupported file type")

    if endpoint_bound:
        try:
            project_id = task_authority._validate_primary_beads_metadata(beads_dir)
        except task_authority.TaskAuthorityError as exc:
            raise GasCityOpsError(f"initialized Beads metadata is invalid: {exc}") from exc
    else:
        retained_environment = beads_dir / ".env"
        if retained_environment.exists() or retained_environment.is_symlink():
            raise GasCityOpsError("initialized Beads must not retain .beads/.env")
        metadata_bytes = _read_repository_file(
            beads_dir / "metadata.json",
            label="initialized Beads metadata",
            maximum=64 * 1024,
        )
        metadata = _load_json_bytes(metadata_bytes, label="initialized Beads metadata")
        project_id = metadata.get("project_id") if isinstance(metadata, dict) else None
        expected_metadata = {
            "backend": "dolt",
            "database": "dolt",
            "dolt_database": AEGIS_BEADS_INIT_DATABASE,
            "dolt_mode": "server",
            "dolt_server_host": AEGIS_BEADS_INIT_HOST,
            "dolt_server_port": AEGIS_BEADS_INIT_PORT,
            "dolt_server_user": AEGIS_BEADS_INIT_USER,
            "project_id": project_id,
        }
        if (
            metadata != expected_metadata
            or type(project_id) is not str
            or _AEGIS_BEADS_PROJECT_ID_RE.fullmatch(project_id) is None
        ):
            raise GasCityOpsError(
                "initialized Beads metadata does not match the exact bd external endpoint"
            )
    config = beads_dir / "config.yaml"
    config_bytes = _read_repository_file(
        config,
        label="initialized Beads config",
        maximum=1024 * 1024,
    )
    try:
        config_text = config_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GasCityOpsError("initialized Beads config is not UTF-8") from exc
    if endpoint_bound:
        if config_bytes != AEGIS_BEADS_CANONICAL_CONFIG:
            raise GasCityOpsError(
                "initialized Beads config is not the exact canonical Aegis endpoint binding"
            )
        expected_metadata = _canonical_evidence_bytes(
            {
                "backend": "dolt",
                "database": "dolt",
                "dolt_database": AEGIS_BEADS_INIT_DATABASE,
                "dolt_mode": "server",
                "project_id": project_id,
            }
        )
        metadata_bytes = _read_repository_file(
            beads_dir / "metadata.json",
            label="initialized Beads metadata",
            maximum=64 * 1024,
        )
        if metadata_bytes != expected_metadata:
            raise GasCityOpsError(
                "initialized Beads metadata is not the exact canonical external identity"
            )
    else:
        for line in config_text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if SECRET_KEY_RE.search(stripped):
                    raise GasCityOpsError(
                        "initialized Beads config contains an active secret setting"
                    )
                raise GasCityOpsError(
                    "initialized Beads config contains an unexpected active setting"
                )
    local_version = _read_repository_file(
        beads_dir / ".local_version",
        label="initialized Beads local version",
        maximum=128,
    )
    if local_version != b"1.1.0\n":
        raise GasCityOpsError("initialized Beads local version is not exactly 1.1.0")
    port_file = beads_dir / "dolt-server.port"
    if endpoint_bound:
        if port_file.exists() or port_file.is_symlink():
            raise GasCityOpsError(
                "canonical external Aegis binding retained a managed Dolt port mirror"
            )
    elif port_file.exists() and _read_repository_file(
        port_file,
        label="initialized Beads server port",
        maximum=32,
    ).strip() != str(AEGIS_BEADS_INIT_PORT).encode("ascii"):
        raise GasCityOpsError("initialized Beads server port file is inconsistent")

    manifest: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: item.relative_to(beads_dir).as_posix()):
        relative = path.relative_to(beads_dir).as_posix()
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            manifest.append({"path": relative, "kind": "directory", "mode": "0700"})
        else:
            content = path.read_bytes()
            manifest.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": "0600",
                    "size": len(content),
                    "sha256": _sha256(content),
                }
            )
    manifest_bytes = _canonical_evidence_bytes({"entries": manifest})
    tree_digest = hashlib.sha256(b"gas-city-aegis-beads-tree/v1\0" + manifest_bytes)
    return manifest, _sha256(manifest_bytes), tree_digest.hexdigest(), project_id


def _bind_staged_aegis_endpoint(beads_dir: Path, *, project_id: str) -> None:
    """Publish the canonical files emitted by pinned gc rig set-endpoint.

    The live empty-target attestation runs before this helper.  Keeping the
    deterministic endpoint projection inside the existing staging transaction
    avoids gc rewriting the deployed city.toml and site binding while still
    producing its exact canonical Aegis config and metadata shapes.
    """

    metadata_path = beads_dir / "metadata.json"
    metadata_bytes = _read_repository_file(
        metadata_path,
        label="staged Beads metadata before endpoint binding",
        maximum=64 * 1024,
    )
    metadata = _load_json_bytes(
        metadata_bytes,
        label="staged Beads metadata before endpoint binding",
    )
    expected = {
        "backend": "dolt",
        "database": "dolt",
        "dolt_database": AEGIS_BEADS_INIT_DATABASE,
        "dolt_mode": "server",
        "dolt_server_host": AEGIS_BEADS_INIT_HOST,
        "dolt_server_port": AEGIS_BEADS_INIT_PORT,
        "dolt_server_user": AEGIS_BEADS_INIT_USER,
        "project_id": project_id,
    }
    if metadata != expected:
        raise GasCityOpsError(
            "bd init metadata does not match the exact Aegis external endpoint"
        )
    canonical_metadata = _canonical_evidence_bytes(
        {
            "backend": "dolt",
            "database": "dolt",
            "dolt_database": AEGIS_BEADS_INIT_DATABASE,
            "dolt_mode": "server",
            "project_id": project_id,
        }
    )
    _atomic_write(
        beads_dir / "config.yaml",
        AEGIS_BEADS_CANONICAL_CONFIG,
        mode=0o600,
    )
    _atomic_write(metadata_path, canonical_metadata, mode=0o600)
    port_file = beads_dir / "dolt-server.port"
    if port_file.is_symlink():
        raise GasCityOpsError("staged Aegis port mirror must not be a symlink")
    if port_file.exists():
        content = _read_repository_file(
            port_file,
            label="staged Aegis server port",
            maximum=32,
        )
        if content.strip() != str(AEGIS_BEADS_INIT_PORT).encode("ascii"):
            raise GasCityOpsError("staged Aegis server port is inconsistent")
        port_file.unlink()
        directory_fd = os.open(beads_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def _assert_secret_absent_from_staging(staging: Path, password: str) -> None:
    encoded = password.encode("utf-8")
    for root, directories, files in os.walk(staging, topdown=True, followlinks=False):
        root_path = Path(root)
        for name in (*directories, *files):
            path = root_path / name
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise GasCityOpsError("Beads staging repo contains a symlink")
            if stat.S_ISREG(metadata.st_mode):
                if metadata.st_size > AEGIS_BEADS_INIT_MAX_FILE_BYTES:
                    raise GasCityOpsError("Beads staging repo contains an unexpectedly large file")
                if encoded in path.read_bytes():
                    raise GasCityOpsError("bd persisted the target Dolt credential in staging")


def _write_or_verify_private_evidence(
    root: Path,
    relative_name: str,
    content: bytes,
) -> str:
    path = root / relative_name
    try:
        path.lstat()
    except FileNotFoundError:
        return write_private_evidence_bytes(root, relative_name, content)
    except OSError as exc:
        raise GasCityOpsError(f"cannot inspect prior evidence artifact: {relative_name}") from exc
    observed = _read_private_initialization_evidence(path, label=f"prior evidence {relative_name}")
    if observed != content:
        raise GasCityOpsError(f"prior evidence artifact drifted: {relative_name}")
    return _sha256(observed)


def _read_private_initialization_evidence(path: Path, *, label: str) -> bytes:
    content = _read_repository_file(path, label=label, maximum=4 * 1024 * 1024)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise GasCityOpsError(f"{label} must be owner-only mode 0600")
    return content


def _validate_stealth_exclude(content: bytes, *, allow_absent: bool) -> bool:
    occurrences = content.count(AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK)
    if occurrences > 1:
        raise GasCityOpsError("Beads stealth exclude block is duplicated")
    if occurrences == 1:
        return True
    if (
        b"# Beads stealth mode (added by bd init --stealth)" in content
        or b"# Beads: Dolt files kept local via .git/info/exclude" in content
    ):
        raise GasCityOpsError("Beads stealth exclude block is partial or modified")
    if allow_absent:
        return False
    raise GasCityOpsError("bd init did not produce the exact pinned stealth exclude block")


def _exclude_after_bytes(before: bytes) -> bytes:
    if _validate_stealth_exclude(before, allow_absent=True):
        return before
    result = before
    if result and not result.endswith(b"\n"):
        result += b"\n"
    if result and not result.endswith(b"\n\n"):
        result += b"\n"
    return result + AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK


def _aegis_runtime_config_seed_argv(dolt_binary: Path) -> tuple[str, ...]:
    query = (
        "INSERT INTO config (`key`, value) VALUES "
        f"('issue_prefix', '{AEGIS_BEADS_INIT_PREFIX}'), "
        f"('types.custom', '{GAS_CITY_REQUIRED_CUSTOM_TYPES}') "
        "ON DUPLICATE KEY UPDATE value = VALUES(value);"
    )
    return (
        dolt_binary.as_posix(),
        "--host",
        AEGIS_BEADS_INIT_HOST,
        "--port",
        str(AEGIS_BEADS_INIT_PORT),
        "--user",
        AEGIS_BEADS_INIT_USER,
        "--use-db",
        AEGIS_BEADS_INIT_DATABASE,
        "--no-tls",
        "sql",
        "--result-format",
        "json",
        "--query",
        query,
    )


def _aegis_schema_migration_argv(
    bd_binary: Path, target_directory: Path
) -> tuple[str, ...]:
    return (
        bd_binary.as_posix(),
        "--json",
        "--dolt-auto-commit",
        "on",
        "-C",
        target_directory.as_posix(),
        "migrate",
        "schema",
    )


def _empty_target_attestation(
    *,
    target_directory: Path,
    bd_binary: Path,
    dolt_binary: Path,
    environment: Mapping[str, str],
    runner: Runner,
    password: str,
) -> dict[str, Any]:
    export = _checked(
        [
            bd_binary.as_posix(),
            "--readonly",
            "-C",
            target_directory.as_posix(),
            "export",
            "--all",
        ],
        cwd=target_directory,
        environment=environment,
        runner=runner,
        secrets=(password,),
    ).stdout
    if export.strip():
        try:
            for line in export.splitlines():
                if line.strip():
                    parsed = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
                    if not isinstance(parsed, dict):
                        raise ValueError
        except (ValueError, json.JSONDecodeError, RecursionError):
            raise GasCityOpsError("empty-target Beads export is invalid JSONL") from None
        raise GasCityOpsError("Aegis Beads target database is contaminated")

    connection = [
        dolt_binary.as_posix(),
        "--host",
        AEGIS_BEADS_INIT_HOST,
        "--port",
        str(AEGIS_BEADS_INIT_PORT),
        "--user",
        AEGIS_BEADS_INIT_USER,
        "--use-db",
        AEGIS_BEADS_INIT_DATABASE,
        "--no-tls",
        "sql",
        "--result-format",
        "json",
    ]
    counts_query = (
        "SELECT "
        "(SELECT COUNT(*) FROM issues) AS issue_count, "
        "(SELECT COUNT(*) FROM dolt_status) AS working_set_changes, "
        "(SELECT COUNT(*) FROM dolt_status "
        "WHERE table_name = 'config' AND status = 'modified' AND staged = 0) "
        "AS expected_config_changes, "
        "(SELECT COUNT(*) FROM dolt_status "
        "WHERE NOT (table_name = 'config' AND status = 'modified' AND staged = 0)) "
        "AS unexpected_working_changes, "
        "(SELECT COUNT(*) FROM dolt_branches) AS branch_count, "
        "(SELECT COUNT(*) FROM dolt_branches WHERE name = 'main') AS main_branch_count, "
        "(SELECT COUNT(*) FROM dolt_log) AS commit_count;"
    )
    counts_result = _checked(
        [*connection, "--query", counts_query],
        cwd=target_directory,
        environment=environment,
        runner=runner,
        secrets=(password,),
    )
    counts_value = _load_json_bytes(
        counts_result.stdout.encode("utf-8"),
        label="empty-target Dolt attestation",
    )
    rows = counts_value.get("rows") if isinstance(counts_value, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise GasCityOpsError("empty-target Dolt attestation did not return one row")
    observed: dict[str, int] = {}
    for name in (*_AEGIS_BEADS_INIT_EMPTY_COUNTS, "commit_count"):
        raw = rows[0].get(name)
        if type(raw) is int:
            value = raw
        elif type(raw) is str and re.fullmatch(r"[0-9]+", raw):
            value = int(raw)
        else:
            raise GasCityOpsError(f"empty-target Dolt attestation returned invalid {name}")
        observed[name] = value
    if (
        any(observed[name] != required for name, required in _AEGIS_BEADS_INIT_EMPTY_COUNTS.items())
        or observed["commit_count"] < 1
    ):
        raise GasCityOpsError("Aegis Dolt target is not one initialized, empty, clean main branch")

    runtime_config_result = _checked(
        [
            *connection,
            "--query",
            (
                "SELECT `key`, value FROM config WHERE `key` IN "
                "('issue_prefix', 'types.custom') ORDER BY `key`;"
            ),
        ],
        cwd=target_directory,
        environment=environment,
        runner=runner,
        secrets=(password,),
    )
    runtime_config_value = _load_json_bytes(
        runtime_config_result.stdout.encode("utf-8"),
        label="empty-target Gas City runtime config",
    )
    runtime_config_rows = (
        runtime_config_value.get("rows")
        if isinstance(runtime_config_value, dict)
        else None
    )
    expected_runtime_config = [
        {"key": "issue_prefix", "value": AEGIS_BEADS_INIT_PREFIX},
        {"key": "types.custom", "value": GAS_CITY_REQUIRED_CUSTOM_TYPES},
    ]
    if runtime_config_rows != expected_runtime_config:
        raise GasCityOpsError(
            "Aegis Dolt target lacks exact Gas City runtime configuration"
        )

    head_result = _checked(
        [*connection, "--query", "SELECT HASHOF('main') AS head;"],
        cwd=target_directory,
        environment=environment,
        runner=runner,
        secrets=(password,),
    )
    head_value = _load_json_bytes(
        head_result.stdout.encode("utf-8"),
        label="empty-target Dolt main head",
    )
    head_rows = head_value.get("rows") if isinstance(head_value, dict) else None
    head = (
        head_rows[0].get("head")
        if isinstance(head_rows, list) and len(head_rows) == 1 and isinstance(head_rows[0], dict)
        else None
    )
    if type(head) is not str or re.fullmatch(r"[a-z0-9]{20,128}", head) is None:
        raise GasCityOpsError("empty-target Dolt main head is invalid")
    return {
        **observed,
        "issue_prefix": AEGIS_BEADS_INIT_PREFIX,
        "types_custom": GAS_CITY_REQUIRED_CUSTOM_TYPES,
        "main_head": head,
        "export_record_count": 0,
        "export_sha256": _sha256(export.encode("utf-8")),
    }


def _validate_repository_fingerprint(value: Any, *, label: str) -> None:
    fields = {
        "head",
        "symbolic_head",
        "index_sha256",
        "worktree_diff_sha256",
        "index_diff_sha256",
        "status_sha256",
        "untracked_count",
        "untracked_content_sha256",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise GasCityOpsError(f"{label} fields are not exact")
    if type(value.get("head")) is not str or GIT_OBJECT_RE.fullmatch(value["head"]) is None:
        raise GasCityOpsError(f"{label} Git head is invalid")
    symbolic = value.get("symbolic_head")
    if (
        type(symbolic) is not str
        or not symbolic.startswith("refs/")
        or not GIT_REF_RE.fullmatch(symbolic.removeprefix("refs/"))
    ):
        raise GasCityOpsError(f"{label} symbolic head is invalid")
    for field in fields - {"head", "symbolic_head", "untracked_count"}:
        if type(value.get(field)) is not str or SHA256_RE.fullmatch(value[field]) is None:
            raise GasCityOpsError(f"{label} {field} is invalid")
    if type(value.get("untracked_count")) is not int or value["untracked_count"] < 0:
        raise GasCityOpsError(f"{label} untracked count is invalid")


def _validate_empty_target_value(value: Any) -> None:
    expected_fields = {
        *_AEGIS_BEADS_INIT_EMPTY_COUNTS,
        "commit_count",
        "issue_prefix",
        "types_custom",
        "main_head",
        "export_record_count",
        "export_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise GasCityOpsError("Aegis empty-target evidence fields are not exact")
    if any(
        value.get(name) != required for name, required in _AEGIS_BEADS_INIT_EMPTY_COUNTS.items()
    ):
        raise GasCityOpsError("Aegis empty-target evidence counts are invalid")
    if type(value.get("commit_count")) is not int or value["commit_count"] < 1:
        raise GasCityOpsError("Aegis empty-target commit count is invalid")
    if value.get("issue_prefix") != AEGIS_BEADS_INIT_PREFIX:
        raise GasCityOpsError("Aegis empty-target issue prefix is invalid")
    if value.get("types_custom") != GAS_CITY_REQUIRED_CUSTOM_TYPES:
        raise GasCityOpsError("Aegis empty-target custom types are invalid")
    if (
        type(value.get("main_head")) is not str
        or re.fullmatch(r"[a-z0-9]{20,128}", value["main_head"]) is None
    ):
        raise GasCityOpsError("Aegis empty-target main head is invalid")
    if value.get("export_record_count") != 0:
        raise GasCityOpsError("Aegis empty-target export count is invalid")
    if (
        type(value.get("export_sha256")) is not str
        or SHA256_RE.fullmatch(value["export_sha256"]) is None
    ):
        raise GasCityOpsError("Aegis empty-target export digest is invalid")


def _read_initialization_pointer(path: Path) -> dict[str, Any]:
    content = _read_repository_file(
        path,
        label="Aegis Beads initialization pointer",
        maximum=256 * 1024,
    )
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise GasCityOpsError("Aegis Beads initialization pointer must be mode 0600")
    value = _load_json_bytes(content, label="Aegis Beads initialization pointer")
    if not isinstance(value, dict) or set(value) != _AEGIS_BEADS_INIT_POINTER_FIELDS:
        raise GasCityOpsError("Aegis Beads initialization pointer fields are not exact")
    if content != _canonical_evidence_bytes(value):
        raise GasCityOpsError("Aegis Beads initialization pointer is not canonical JSON")
    if value.get("schema_version") != AEGIS_BEADS_INIT_POINTER_SCHEMA:
        raise GasCityOpsError("Aegis Beads initialization pointer schema is invalid")
    if value.get("status") not in {"prepared", "complete"}:
        raise GasCityOpsError("Aegis Beads initialization pointer status is invalid")
    for field in (
        "runtime_lock_sha256",
        "prepared_evidence_sha256",
        "beads_tree_sha256",
        "beads_manifest_sha256",
        "metadata_sha256",
        "config_sha256",
        "exclude_before_sha256",
        "exclude_after_sha256",
    ):
        if type(value.get(field)) is not str or SHA256_RE.fullmatch(value[field]) is None:
            raise GasCityOpsError(f"Aegis Beads initialization pointer {field} is invalid")
    final_digest = value.get("final_manifest_sha256")
    if value["status"] == "prepared" and final_digest is not None:
        raise GasCityOpsError("prepared Aegis initialization unexpectedly names final evidence")
    if value["status"] == "complete" and (
        type(final_digest) is not str or SHA256_RE.fullmatch(final_digest) is None
    ):
        raise GasCityOpsError("complete Aegis initialization lacks final evidence")
    project_id = value.get("project_id")
    if type(project_id) is not str or _AEGIS_BEADS_PROJECT_ID_RE.fullmatch(project_id) is None:
        raise GasCityOpsError("Aegis Beads initialization project_id is invalid")
    _validate_empty_target_value(value.get("empty_target"))
    _validate_repository_fingerprint(
        value.get("repository_before"),
        label="Aegis Beads initialization repository fingerprint",
    )
    return value


def _initialization_state_root(git_common_dir: Path) -> Path:
    root = git_common_dir / AEGIS_BEADS_INIT_STATE_DIRECTORY
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise GasCityOpsError("cannot create Aegis Beads initialization state directory") from exc
    try:
        metadata = root.lstat()
    except OSError as exc:
        raise GasCityOpsError("cannot inspect Aegis Beads initialization state directory") from exc
    if root.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise GasCityOpsError("Aegis Beads initialization state must be one real directory")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise GasCityOpsError("Aegis Beads initialization state must be owner-only mode 0700")
    return root


def _acquire_initialization_lock(state_root: Path) -> int:
    path = state_root / "operation.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd: int | None = None
    try:
        fd = os.open(path, flags, 0o600)
        metadata = os.fstat(fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
        ):
            raise GasCityOpsError("Aegis Beads initialization lock is unsafe")
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd
    except GasCityOpsError:
        if fd is not None:
            os.close(fd)
        raise
    except OSError as exc:
        if fd is not None:
            os.close(fd)
        raise GasCityOpsError("cannot acquire Aegis Beads initialization lock") from exc


def _validate_pointer_binding(
    pointer: Mapping[str, Any],
    *,
    identity: task_authority.RepositoryIdentity,
    lock_path: Path,
    lock_sha256: str,
    lock_value: Mapping[str, Any],
    bd_binary: Path,
    dolt_binary: Path,
    state_root: Path,
) -> tuple[Path, Path]:
    expected = {
        "repository_root": identity.repository_root.as_posix(),
        "git_common_dir": identity.git_common_dir.as_posix(),
        "runtime_lock_path": lock_path.as_posix(),
        "runtime_lock_sha256": lock_sha256,
    }
    if any(pointer.get(field) != value for field, value in expected.items()):
        raise GasCityOpsError("Aegis Beads initialization pointer is bound to another target")
    run_id = pointer.get("run_id")
    if type(run_id) is not str or re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{16}", run_id) is None:
        raise GasCityOpsError("Aegis Beads initialization run ID is invalid")
    expected_evidence = lock_path.parent / "runtime" / "evidence" / "beads-initialization" / run_id
    expected_staging = state_root / f"staging-{run_id}"
    if pointer.get("evidence_directory") != expected_evidence.as_posix():
        raise GasCityOpsError("Aegis Beads initialization evidence path is invalid")
    if pointer.get("staging_directory") != expected_staging.as_posix():
        raise GasCityOpsError("Aegis Beads initialization staging path is invalid")
    try:
        evidence_metadata = expected_evidence.lstat()
    except OSError as exc:
        raise GasCityOpsError("Aegis Beads initialization evidence directory is missing") from exc
    if expected_evidence.is_symlink() or not stat.S_ISDIR(evidence_metadata.st_mode):
        raise GasCityOpsError("Aegis Beads initialization evidence is not one real directory")
    if evidence_metadata.st_uid != os.getuid() or stat.S_IMODE(evidence_metadata.st_mode) != 0o700:
        raise GasCityOpsError("Aegis Beads initialization evidence is not owner-only")
    prepared = _read_private_initialization_evidence(
        expected_evidence / "prepared.json",
        label="Aegis Beads prepared evidence",
    )
    if _sha256(prepared) != pointer["prepared_evidence_sha256"]:
        raise GasCityOpsError("Aegis Beads prepared evidence drifted")
    prepared_value = _load_json_bytes(prepared, label="Aegis Beads prepared evidence")
    if (
        not isinstance(prepared_value, dict)
        or set(prepared_value)
        != {
            "schema_version",
            "status",
            "run_id",
            "runtime_lock_sha256",
            "intent_sha256",
            "beads_tree_sha256",
            "beads_manifest_sha256",
            "metadata_sha256",
            "config_sha256",
            "project_id",
            "empty_target",
            "repository_before",
            "exclude_before_sha256",
            "exclude_after_sha256",
        }
        or prepared_value.get("schema_version") != AEGIS_BEADS_INIT_SCHEMA
        or prepared_value.get("status") != "prepared"
        or prepared_value.get("run_id") != run_id
        or prepared_value.get("runtime_lock_sha256") != lock_sha256
        or prepared_value.get("beads_tree_sha256") != pointer["beads_tree_sha256"]
        or prepared_value.get("beads_manifest_sha256") != pointer["beads_manifest_sha256"]
        or prepared_value.get("metadata_sha256") != pointer["metadata_sha256"]
        or prepared_value.get("config_sha256") != pointer["config_sha256"]
        or prepared_value.get("project_id") != pointer["project_id"]
        or prepared_value.get("empty_target") != pointer["empty_target"]
        or prepared_value.get("exclude_before_sha256") != pointer["exclude_before_sha256"]
        or prepared_value.get("exclude_after_sha256") != pointer["exclude_after_sha256"]
    ):
        raise GasCityOpsError("Aegis Beads prepared evidence does not match its pointer")
    intent = _read_private_initialization_evidence(
        expected_evidence / "intent.json",
        label="Aegis Beads initialization intent",
    )
    if _sha256(intent) != prepared_value.get("intent_sha256"):
        raise GasCityOpsError("Aegis Beads initialization intent drifted")
    intent_value = _load_json_bytes(intent, label="Aegis Beads initialization intent")
    expected_tools = {
        "bd": {
            "path": bd_binary.as_posix(),
            "version": AEGIS_BEADS_INIT_BD_VERSION_OUTPUT,
            "sha256": lock_value["tools"]["bd"]["binary_sha256"],
        },
        "dolt": {
            "path": dolt_binary.as_posix(),
            "version": AEGIS_BEADS_INIT_DOLT_VERSION_OUTPUT,
            "sha256": lock_value["tools"]["dolt"]["binary_sha256"],
        },
    }
    expected_target = {
        "prefix": AEGIS_BEADS_INIT_PREFIX,
        "host": AEGIS_BEADS_INIT_HOST,
        "port": AEGIS_BEADS_INIT_PORT,
        "user": AEGIS_BEADS_INIT_USER,
        "database": AEGIS_BEADS_INIT_DATABASE,
    }
    if (
        not isinstance(intent_value, dict)
        or set(intent_value)
        != {
            "schema_version",
            "status",
            "run_id",
            "created_at",
            "repository_root",
            "git_common_dir",
            "staging_directory",
            "runtime_lock_path",
            "runtime_lock_sha256",
            "tools",
            "target",
            "repository_before",
            "exclude_block_sha256",
            "exclude_before_sha256",
            "exclude_after_sha256",
        }
        or intent_value.get("schema_version") != AEGIS_BEADS_INIT_SCHEMA
        or intent_value.get("status") != "intent"
        or intent_value.get("run_id") != run_id
        or intent_value.get("runtime_lock_path") != lock_path.as_posix()
        or intent_value.get("runtime_lock_sha256") != lock_sha256
        or intent_value.get("repository_root") != identity.repository_root.as_posix()
        or intent_value.get("git_common_dir") != identity.git_common_dir.as_posix()
        or intent_value.get("staging_directory") != expected_staging.as_posix()
        or intent_value.get("tools") != expected_tools
        or intent_value.get("target") != expected_target
        or intent_value.get("exclude_block_sha256") != _sha256(AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK)
        or intent_value.get("exclude_before_sha256") != pointer["exclude_before_sha256"]
        or intent_value.get("exclude_after_sha256") != pointer["exclude_after_sha256"]
        or intent_value.get("repository_before") != pointer["repository_before"]
    ):
        raise GasCityOpsError("Aegis Beads initialization intent is not exact")
    _utc_timestamp(intent_value.get("created_at"), label="Aegis initialization created_at")
    tree_evidence = _read_private_initialization_evidence(
        expected_evidence / "beads-tree.json",
        label="Aegis Beads tree evidence",
    )
    if _sha256(tree_evidence) != pointer["beads_manifest_sha256"]:
        raise GasCityOpsError("Aegis Beads tree evidence drifted")
    return expected_evidence, expected_staging


def _validate_complete_initialization(
    pointer: Mapping[str, Any],
    *,
    evidence_root: Path,
    lock_value: Mapping[str, Any],
) -> None:
    final_bytes = _read_private_initialization_evidence(
        evidence_root / "manifest.json",
        label="Aegis Beads initialization manifest",
    )
    if _sha256(final_bytes) != pointer["final_manifest_sha256"]:
        raise GasCityOpsError("Aegis Beads initialization manifest drifted")
    value = _load_json_bytes(final_bytes, label="Aegis Beads initialization manifest")
    artifacts = value.get("artifacts") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema_version",
            "status",
            "run_id",
            "repository_root",
            "runtime_lock_path",
            "runtime_lock_sha256",
            "tools",
            "project_id",
            "beads_tree_sha256",
            "beads_manifest_sha256",
            "metadata_sha256",
            "config_sha256",
            "empty_target",
            "exclude_block_sha256",
            "exclude_before_sha256",
            "exclude_after_sha256",
            "artifacts",
            "credential_transport",
        }
        or value.get("schema_version") != AEGIS_BEADS_INIT_SCHEMA
        or value.get("status") != "pass"
        or value.get("run_id") != pointer["run_id"]
        or value.get("runtime_lock_sha256") != pointer["runtime_lock_sha256"]
        or value.get("repository_root") != pointer["repository_root"]
        or value.get("runtime_lock_path") != pointer["runtime_lock_path"]
        or value.get("project_id") != pointer["project_id"]
        or value.get("beads_tree_sha256") != pointer["beads_tree_sha256"]
        or value.get("empty_target") != pointer["empty_target"]
        or value.get("exclude_before_sha256") != pointer["exclude_before_sha256"]
        or value.get("exclude_after_sha256") != pointer["exclude_after_sha256"]
        or value.get("beads_manifest_sha256") != pointer["beads_manifest_sha256"]
        or value.get("metadata_sha256") != pointer["metadata_sha256"]
        or value.get("config_sha256") != pointer["config_sha256"]
        or value.get("tools")
        != {
            "bd_sha256": lock_value["tools"]["bd"]["binary_sha256"],
            "dolt_sha256": lock_value["tools"]["dolt"]["binary_sha256"],
        }
        or value.get("exclude_block_sha256") != _sha256(AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK)
        or value.get("credential_transport") != "owner-only-environment-file"
        or not isinstance(artifacts, dict)
        or set(artifacts)
        != {
            "intent.json",
            "beads-tree.json",
            "prepared.json",
            "publish.json",
        }
    ):
        raise GasCityOpsError("Aegis Beads initialization manifest is not exact")
    for name, expected_digest in artifacts.items():
        if type(expected_digest) is not str or SHA256_RE.fullmatch(expected_digest) is None:
            raise GasCityOpsError("Aegis Beads initialization artifact digest is invalid")
        artifact = _read_private_initialization_evidence(
            evidence_root / name,
            label=f"Aegis Beads initialization {name}",
        )
        if _sha256(artifact) != expected_digest:
            raise GasCityOpsError(f"Aegis Beads initialization artifact drifted: {name}")
    publish_bytes = _read_private_initialization_evidence(
        evidence_root / "publish.json",
        label="Aegis Beads publish evidence",
    )
    publish = _load_json_bytes(publish_bytes, label="Aegis Beads publish evidence")
    publish_fields = {
        "schema_version",
        "status",
        "run_id",
        "action",
        "published_directory",
        "repository_original_before",
        "repository_resume_before",
        "repository_after",
        "beads_tree_sha256",
        "metadata_sha256",
        "config_sha256",
        "project_id",
        "empty_target",
        "exclude_before_sha256",
        "exclude_after_sha256",
    }
    if (
        not isinstance(publish, dict)
        or set(publish) != publish_fields
        or publish.get("schema_version") != AEGIS_BEADS_INIT_SCHEMA
        or publish.get("status") != "pass"
        or publish.get("run_id") != pointer["run_id"]
        or publish.get("action") != "initialized"
        or publish.get("published_directory")
        != (Path(pointer["repository_root"]) / ".beads").as_posix()
        or publish.get("repository_original_before") != pointer["repository_before"]
        or publish.get("repository_resume_before") != publish.get("repository_after")
        or publish.get("beads_tree_sha256") != pointer["beads_tree_sha256"]
        or publish.get("metadata_sha256") != pointer["metadata_sha256"]
        or publish.get("config_sha256") != pointer["config_sha256"]
        or publish.get("project_id") != pointer["project_id"]
        or publish.get("empty_target") != pointer["empty_target"]
        or publish.get("exclude_before_sha256") != pointer["exclude_before_sha256"]
        or publish.get("exclude_after_sha256") != pointer["exclude_after_sha256"]
    ):
        raise GasCityOpsError("Aegis Beads publish evidence is not exact")
    _validate_repository_fingerprint(
        publish["repository_resume_before"],
        label="Aegis Beads publish repository fingerprint",
    )


def _verify_published_beads(
    beads_dir: Path,
    *,
    pointer: Mapping[str, Any],
    password: str,
) -> None:
    _, manifest_sha256, tree_sha256, project_id = _normalize_and_manifest_beads_tree(
        beads_dir,
        password=password,
        normalize=False,
        endpoint_bound=True,
    )
    metadata_sha256 = _sha256(
        _read_repository_file(
            beads_dir / "metadata.json",
            label="published Beads metadata",
            maximum=64 * 1024,
        )
    )
    config_sha256 = _sha256(
        _read_repository_file(
            beads_dir / "config.yaml",
            label="published Beads config",
            maximum=1024 * 1024,
        )
    )
    if (
        manifest_sha256 != pointer["beads_manifest_sha256"]
        or project_id != pointer["project_id"]
        or tree_sha256 != pointer["beads_tree_sha256"]
        or metadata_sha256 != pointer["metadata_sha256"]
        or config_sha256 != pointer["config_sha256"]
    ):
        raise GasCityOpsError("published Aegis .beads drifted from prepared evidence")


def initialize_aegis_beads(
    target_repo: Path,
    lock_path: Path,
    *,
    bd_binary: Path,
    dolt_binary: Path,
    password: str,
    git_binary: Path = Path("/usr/bin/git"),
    runner: Runner = _default_runner,
    phase_hook: Callable[[str], None] | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Initialize Aegis Beads without changing repository work or authority.

    The operation stages ``bd init`` in an independent Git repository beneath
    the primary checkout's real ``.git`` directory, proves the external Dolt
    schema is initialized and empty, then atomically publishes only ``.beads``
    and the exact pinned stealth exclusion. A private transaction pointer makes
    publication crash-repairable and rejects unrelated preexisting stores.
    """

    if type(password) is not str or not password:
        raise GasCityOpsError("target Dolt password must be a non-empty string")
    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_value = load_runtime_lock(lock)
    lock_bytes = _regular_file_bytes(lock, label="runtime lock")
    lock_sha256 = _sha256(lock_bytes)
    if lock_value["tools"]["bd"]["version"] != "1.1.0":
        raise GasCityOpsError("runtime lock does not pin bd 1.1.0")
    if lock_value["tools"]["dolt"]["version"] != "2.2.0":
        raise GasCityOpsError("runtime lock does not pin Dolt 2.2.0")
    identity = _secure_primary_repository(target_repo)
    bd = _locked_initialization_tool(bd_binary, name="bd", lock=lock_value)
    dolt = _locked_initialization_tool(dolt_binary, name="dolt", lock=lock_value)
    configured_git = git_binary.expanduser()
    if not configured_git.is_absolute() or configured_git.is_symlink():
        raise GasCityOpsError("Git binary must be an absolute non-symlink path")
    git = _canonical_path(configured_git, must_exist=True, label="Git binary")
    if git != configured_git or not git.is_file() or stat.S_IMODE(git.stat().st_mode) & 0o111 == 0:
        raise GasCityOpsError("Git binary must be one real executable file")

    state_root = _initialization_state_root(identity.git_common_dir)
    lock_fd = _acquire_initialization_lock(state_root)
    pointer_path = identity.git_common_dir / AEGIS_BEADS_INIT_POINTER_NAME
    beads_dir = identity.repository_root / ".beads"
    info_exclude = identity.git_common_dir / "info" / "exclude"
    transient_home: Path | None = None
    try:
        pointer_exists = False
        try:
            pointer_path.lstat()
            pointer_exists = True
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise GasCityOpsError("cannot inspect Aegis Beads initialization pointer") from exc
        beads_exists = False
        try:
            beads_dir.lstat()
            beads_exists = True
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise GasCityOpsError("cannot inspect primary Aegis .beads") from exc
        if beads_exists and not pointer_exists:
            raise GasCityOpsError("preexisting Aegis .beads has no guarded initialization proof")

        if pointer_exists:
            pointer = _read_initialization_pointer(pointer_path)
            evidence_root, staging = _validate_pointer_binding(
                pointer,
                identity=identity,
                lock_path=lock,
                lock_sha256=lock_sha256,
                lock_value=lock_value,
                bd_binary=bd,
                dolt_binary=dolt,
                state_root=state_root,
            )
            run_id = str(pointer["run_id"])
        else:
            pointer = None
            evidence_root = None
            staging = None
            instant = now or _utc_now()
            run_id = instant.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(8)

        transient_home = state_root / (
            f"resume-home-{run_id}" if pointer is not None else f"preflight-home-{run_id}"
        )
        environment = _initialization_environment(transient_home, password)
        nonsecret_environment = _initialization_nonsecret_environment(environment)
        _disable_initialization_metrics(
            bd_binary=bd,
            cwd=identity.repository_root,
            environment=nonsecret_environment,
            runner=runner,
        )
        versions = _validate_initialization_versions(
            bd_binary=bd,
            dolt_binary=dolt,
            cwd=identity.repository_root,
            environment=nonsecret_environment,
            runner=runner,
            password=password,
        )
        repository_resume_before = _repository_work_fingerprint(
            identity.repository_root,
            git_binary=git,
            environment=nonsecret_environment,
            runner=runner,
            reject_stealth_conflicts=pointer is None,
            ignore_beads=pointer is not None,
        )

        if pointer is not None and pointer["status"] == "complete":
            if not beads_exists:
                raise GasCityOpsError("completed Aegis initialization lost its .beads directory")
            assert evidence_root is not None
            _validate_complete_initialization(
                pointer,
                evidence_root=evidence_root,
                lock_value=lock_value,
            )
            _verify_published_beads(beads_dir, pointer=pointer, password=password)
            exclude_bytes = _read_repository_file(
                info_exclude,
                label="primary Git info/exclude",
            )
            if not _validate_stealth_exclude(exclude_bytes, allow_absent=False):
                raise GasCityOpsError("completed Aegis initialization lost its stealth block")
            attestation = _empty_target_attestation(
                target_directory=identity.repository_root,
                bd_binary=bd,
                dolt_binary=dolt,
                environment=environment,
                runner=runner,
                password=password,
            )
            if attestation != pointer["empty_target"]:
                raise GasCityOpsError(
                    "initialized Aegis target is no longer in the pre-migration empty state"
                )
            _verify_published_beads(beads_dir, pointer=pointer, password=password)
            repository_after = _repository_work_fingerprint(
                identity.repository_root,
                git_binary=git,
                environment=nonsecret_environment,
                runner=runner,
                reject_stealth_conflicts=False,
                ignore_beads=True,
            )
            if repository_after != repository_resume_before:
                raise GasCityOpsError("Aegis repository changed during idempotency verification")
            return {
                "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                "status": "pass",
                "action": "already-initialized",
                "repository": identity.repository_root.as_posix(),
                "project_id": pointer["project_id"],
                "database": AEGIS_BEADS_INIT_DATABASE,
                "main_head": attestation["main_head"],
                "evidence_directory": evidence_root.as_posix(),
                "evidence_manifest_sha256": pointer["final_manifest_sha256"],
            }

        created_evidence = False
        prepared_committed = pointer is not None
        try:
            if pointer is None:
                evidence_root = create_private_evidence_directory(
                    lock.parent / "runtime" / "evidence" / "beads-initialization" / run_id
                )
                created_evidence = True
                staging = state_root / f"staging-{run_id}"
                try:
                    staging.mkdir(mode=0o700)
                except OSError as exc:
                    raise GasCityOpsError(
                        "cannot create same-filesystem Beads staging repo"
                    ) from exc
                if staging.stat().st_dev != identity.repository_root.stat().st_dev:
                    raise GasCityOpsError("Beads staging repo is not on the target filesystem")
                repository_before = repository_resume_before
                exclude_before = _read_repository_file(
                    info_exclude,
                    label="primary Git info/exclude",
                )
                exclude_after = _exclude_after_bytes(exclude_before)
                intent = {
                    "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                    "status": "intent",
                    "run_id": run_id,
                    "created_at": _format_utc(now or _utc_now()),
                    "repository_root": identity.repository_root.as_posix(),
                    "git_common_dir": identity.git_common_dir.as_posix(),
                    "staging_directory": staging.as_posix(),
                    "runtime_lock_path": lock.as_posix(),
                    "runtime_lock_sha256": lock_sha256,
                    "tools": {
                        "bd": {
                            "path": bd.as_posix(),
                            "version": versions["bd"],
                            "sha256": lock_value["tools"]["bd"]["binary_sha256"],
                        },
                        "dolt": {
                            "path": dolt.as_posix(),
                            "version": versions["dolt"],
                            "sha256": lock_value["tools"]["dolt"]["binary_sha256"],
                        },
                    },
                    "target": {
                        "prefix": AEGIS_BEADS_INIT_PREFIX,
                        "host": AEGIS_BEADS_INIT_HOST,
                        "port": AEGIS_BEADS_INIT_PORT,
                        "user": AEGIS_BEADS_INIT_USER,
                        "database": AEGIS_BEADS_INIT_DATABASE,
                    },
                    "repository_before": repository_before,
                    "exclude_block_sha256": _sha256(AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK),
                    "exclude_before_sha256": _sha256(exclude_before),
                    "exclude_after_sha256": _sha256(exclude_after),
                }
                intent_digest = write_private_evidence_bytes(
                    evidence_root, "intent.json", _canonical_evidence_bytes(intent)
                )
                _checked(
                    [
                        git.as_posix(),
                        "init",
                        "--quiet",
                        "--initial-branch=main",
                        staging.as_posix(),
                    ],
                    cwd=identity.repository_root,
                    environment=nonsecret_environment,
                    runner=runner,
                )
                init_result = _checked(
                    [
                        bd.as_posix(),
                        "init",
                        "--server",
                        "--external",
                        "--server-host",
                        AEGIS_BEADS_INIT_HOST,
                        "--server-port",
                        str(AEGIS_BEADS_INIT_PORT),
                        "--server-user",
                        AEGIS_BEADS_INIT_USER,
                        "--database",
                        AEGIS_BEADS_INIT_DATABASE,
                        "--prefix",
                        AEGIS_BEADS_INIT_PREFIX,
                        "--non-interactive",
                        "--skip-agents",
                        "--skip-hooks",
                        "--stealth",
                        "--init-if-missing",
                        "--quiet",
                    ],
                    cwd=staging,
                    environment=environment,
                    runner=runner,
                    secrets=(password,),
                )
                if password in init_result.stdout or password in init_result.stderr:
                    raise GasCityOpsError("bd init echoed the target Dolt credential")
                _assert_secret_absent_from_staging(staging, password)
                staging_exclude = _read_repository_file(
                    staging / ".git" / "info" / "exclude",
                    label="staging Git info/exclude",
                )
                _validate_stealth_exclude(staging_exclude, allow_absent=False)
                _, _, _, project_id = _normalize_and_manifest_beads_tree(
                    staging / ".beads",
                    password=password,
                    normalize=True,
                    endpoint_bound=False,
                )
                _checked(
                    _aegis_runtime_config_seed_argv(dolt),
                    cwd=staging,
                    environment=environment,
                    runner=runner,
                    secrets=(password,),
                )
                if phase_hook is not None:
                    phase_hook("after-runtime-config")
                _checked(
                    _aegis_schema_migration_argv(bd, staging),
                    cwd=staging,
                    environment=environment,
                    runner=runner,
                    secrets=(password,),
                )
                if phase_hook is not None:
                    phase_hook("after-schema-migration")
                empty_target = _empty_target_attestation(
                    target_directory=staging,
                    bd_binary=bd,
                    dolt_binary=dolt,
                    environment=environment,
                    runner=runner,
                    password=password,
                )
                _bind_staged_aegis_endpoint(
                    staging / ".beads",
                    project_id=project_id,
                )
                # Capture the publishable tree only after every bd operation.
                # Even read-only commands are treated as potentially creating
                # local runtime files until a final secret/mode/tree audit proves
                # otherwise.
                _assert_secret_absent_from_staging(staging, password)
                (
                    tree_manifest,
                    manifest_sha256,
                    tree_sha256,
                    finalized_project_id,
                ) = _normalize_and_manifest_beads_tree(
                    staging / ".beads",
                    password=password,
                    normalize=True,
                    endpoint_bound=True,
                )
                if finalized_project_id != project_id:
                    raise GasCityOpsError(
                        "canonical Aegis endpoint binding changed the Beads project identity"
                    )
                tree_bytes = _canonical_evidence_bytes({"entries": tree_manifest})
                if _sha256(tree_bytes) != manifest_sha256:
                    raise GasCityOpsError("internal Beads tree evidence digest mismatch")
                tree_evidence_digest = write_private_evidence_bytes(
                    evidence_root, "beads-tree.json", tree_bytes
                )
                metadata_bytes = _read_repository_file(
                    staging / ".beads" / "metadata.json",
                    label="staged Beads metadata",
                    maximum=64 * 1024,
                )
                config_bytes = _read_repository_file(
                    staging / ".beads" / "config.yaml",
                    label="staged Beads config",
                    maximum=1024 * 1024,
                )
                prepared = {
                    "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                    "status": "prepared",
                    "run_id": run_id,
                    "runtime_lock_sha256": lock_sha256,
                    "intent_sha256": intent_digest,
                    "beads_tree_sha256": tree_sha256,
                    "beads_manifest_sha256": tree_evidence_digest,
                    "metadata_sha256": _sha256(metadata_bytes),
                    "config_sha256": _sha256(config_bytes),
                    "project_id": project_id,
                    "empty_target": empty_target,
                    "repository_before": repository_before,
                    "exclude_before_sha256": _sha256(exclude_before),
                    "exclude_after_sha256": _sha256(exclude_after),
                }
                prepared_digest = write_private_evidence_bytes(
                    evidence_root, "prepared.json", _canonical_evidence_bytes(prepared)
                )
                pointer = {
                    "schema_version": AEGIS_BEADS_INIT_POINTER_SCHEMA,
                    "status": "prepared",
                    "repository_root": identity.repository_root.as_posix(),
                    "git_common_dir": identity.git_common_dir.as_posix(),
                    "runtime_lock_path": lock.as_posix(),
                    "runtime_lock_sha256": lock_sha256,
                    "run_id": run_id,
                    "evidence_directory": evidence_root.as_posix(),
                    "staging_directory": staging.as_posix(),
                    "prepared_evidence_sha256": prepared_digest,
                    "beads_tree_sha256": tree_sha256,
                    "beads_manifest_sha256": tree_evidence_digest,
                    "metadata_sha256": _sha256(metadata_bytes),
                    "config_sha256": _sha256(config_bytes),
                    "project_id": project_id,
                    "empty_target": empty_target,
                    "repository_before": repository_before,
                    "exclude_before_sha256": _sha256(exclude_before),
                    "exclude_after_sha256": _sha256(exclude_after),
                    "final_manifest_sha256": None,
                }
                _private_repository_atomic_write(
                    pointer_path,
                    _canonical_evidence_bytes(pointer),
                    mode=0o600,
                    exclusive=True,
                )
                prepared_committed = True
                if phase_hook is not None:
                    phase_hook("prepared")
            else:
                assert evidence_root is not None and staging is not None
                repository_before = pointer["repository_before"]
                exclude_before = _read_repository_file(
                    info_exclude,
                    label="primary Git info/exclude",
                )
                expected_before = pointer["exclude_before_sha256"]
                expected_after = pointer["exclude_after_sha256"]
                if _sha256(exclude_before) not in {expected_before, expected_after}:
                    raise GasCityOpsError(
                        "Git info/exclude changed after prepared Beads publication"
                    )

            assert pointer is not None and evidence_root is not None and staging is not None
            staged_beads = staging / ".beads"
            staged_exists = staged_beads.exists()
            target_exists = beads_dir.exists()
            if staged_exists and target_exists:
                raise GasCityOpsError("both staged and published Aegis .beads exist")
            if not staged_exists and not target_exists:
                raise GasCityOpsError("prepared Aegis .beads disappeared before publication")
            if staged_exists:
                _verify_published_beads(staged_beads, pointer=pointer, password=password)
                attestation_directory = staging
            else:
                _verify_published_beads(beads_dir, pointer=pointer, password=password)
                attestation_directory = identity.repository_root
            empty_target = _empty_target_attestation(
                target_directory=attestation_directory,
                bd_binary=bd,
                dolt_binary=dolt,
                environment=environment,
                runner=runner,
                password=password,
            )
            if empty_target != pointer["empty_target"]:
                raise GasCityOpsError("Aegis empty-target evidence changed before publication")
            _verify_published_beads(
                attestation_directory / ".beads",
                pointer=pointer,
                password=password,
            )
            if staged_exists:
                _rename_directory_noreplace(staged_beads, beads_dir)
                if phase_hook is not None:
                    phase_hook("published")

            current_exclude = _read_repository_file(
                info_exclude,
                label="primary Git info/exclude",
            )
            current_exclude_digest = _sha256(current_exclude)
            if current_exclude_digest == pointer["exclude_before_sha256"]:
                updated_exclude = _exclude_after_bytes(current_exclude)
                if _sha256(updated_exclude) != pointer["exclude_after_sha256"]:
                    raise GasCityOpsError("prepared stealth exclude digest is inconsistent")
                exclude_mode = stat.S_IMODE(info_exclude.stat().st_mode)
                _private_repository_atomic_write(
                    info_exclude,
                    updated_exclude,
                    mode=exclude_mode,
                )
            elif current_exclude_digest == pointer["exclude_after_sha256"]:
                _validate_stealth_exclude(current_exclude, allow_absent=False)
            else:
                raise GasCityOpsError("Git info/exclude drifted during Beads publication")
            if phase_hook is not None:
                phase_hook("excluded")

            repository_after = _repository_work_fingerprint(
                identity.repository_root,
                git_binary=git,
                environment=nonsecret_environment,
                runner=runner,
                reject_stealth_conflicts=False,
                ignore_beads=True,
            )
            if repository_after != repository_resume_before:
                raise GasCityOpsError(
                    "Aegis HEAD, index, tracked changes, or untracked work changed during initialization"
                )
            publish = {
                "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                "status": "pass",
                "run_id": run_id,
                # Immutable finalization evidence must be byte-identical when a
                # prepared transaction resumes after any later crash boundary.
                "action": "initialized",
                "published_directory": beads_dir.as_posix(),
                "repository_original_before": repository_before,
                "repository_resume_before": repository_resume_before,
                "repository_after": repository_after,
                "beads_tree_sha256": pointer["beads_tree_sha256"],
                "metadata_sha256": pointer["metadata_sha256"],
                "config_sha256": pointer["config_sha256"],
                "project_id": pointer["project_id"],
                "empty_target": pointer["empty_target"],
                "exclude_before_sha256": pointer["exclude_before_sha256"],
                "exclude_after_sha256": pointer["exclude_after_sha256"],
            }
            publish_digest = _write_or_verify_private_evidence(
                evidence_root, "publish.json", _canonical_evidence_bytes(publish)
            )
            if phase_hook is not None:
                phase_hook("publish-evidence")
            artifacts = {
                name: _sha256(
                    _read_private_initialization_evidence(
                        evidence_root / name,
                        label=f"Aegis initialization {name}",
                    )
                )
                for name in ("intent.json", "beads-tree.json", "prepared.json", "publish.json")
            }
            if artifacts["publish.json"] != publish_digest:
                raise GasCityOpsError("Aegis initialization publish evidence digest mismatch")
            manifest = {
                "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                "status": "pass",
                "run_id": run_id,
                "repository_root": identity.repository_root.as_posix(),
                "runtime_lock_path": lock.as_posix(),
                "runtime_lock_sha256": lock_sha256,
                "tools": {
                    "bd_sha256": lock_value["tools"]["bd"]["binary_sha256"],
                    "dolt_sha256": lock_value["tools"]["dolt"]["binary_sha256"],
                },
                "project_id": pointer["project_id"],
                "beads_tree_sha256": pointer["beads_tree_sha256"],
                "beads_manifest_sha256": pointer["beads_manifest_sha256"],
                "metadata_sha256": pointer["metadata_sha256"],
                "config_sha256": pointer["config_sha256"],
                "empty_target": pointer["empty_target"],
                "exclude_block_sha256": _sha256(AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK),
                "exclude_before_sha256": pointer["exclude_before_sha256"],
                "exclude_after_sha256": pointer["exclude_after_sha256"],
                "artifacts": artifacts,
                "credential_transport": "owner-only-environment-file",
            }
            manifest_digest = _write_or_verify_private_evidence(
                evidence_root, "manifest.json", _canonical_evidence_bytes(manifest)
            )
            if phase_hook is not None:
                phase_hook("manifest")
            complete_pointer = dict(pointer)
            complete_pointer["status"] = "complete"
            complete_pointer["final_manifest_sha256"] = manifest_digest
            _private_repository_atomic_write(
                pointer_path,
                _canonical_evidence_bytes(complete_pointer),
                mode=0o600,
            )
            try:
                if staging.exists():
                    shutil.rmtree(staging)
            except OSError:
                # The complete pointer and evidence remain authoritative; stale
                # staging contains no .beads or credential and is harmless.
                pass
            preflight_home = state_root / f"preflight-home-{run_id}"
            if preflight_home.exists():
                try:
                    shutil.rmtree(preflight_home)
                except OSError:
                    pass
            return {
                "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                "status": "pass",
                "action": "initialized" if created_evidence else "crash-repaired",
                "repository": identity.repository_root.as_posix(),
                "project_id": pointer["project_id"],
                "database": AEGIS_BEADS_INIT_DATABASE,
                "main_head": pointer["empty_target"]["main_head"],
                "evidence_directory": evidence_root.as_posix(),
                "evidence_manifest_sha256": manifest_digest,
            }
        except Exception as exc:
            if not prepared_committed and pointer_path.exists():
                try:
                    committed_pointer = _read_initialization_pointer(pointer_path)
                except GasCityOpsError:
                    pass
                else:
                    prepared_committed = committed_pointer.get("status") == "prepared"
            if evidence_root is not None and created_evidence:
                message = _redact(str(exc), (password,))
                failure = {
                    "schema_version": AEGIS_BEADS_INIT_SCHEMA,
                    "status": "failed",
                    "run_id": run_id,
                    "error_type": type(exc).__name__,
                    "error": message,
                    "prepared": prepared_committed,
                    "published": beads_dir.exists(),
                }
                try:
                    write_private_evidence_bytes(
                        evidence_root,
                        "failure.json",
                        _canonical_evidence_bytes(failure),
                    )
                except GasCityOpsError:
                    pass
            if not prepared_committed and staging is not None and staging.exists():
                try:
                    shutil.rmtree(staging)
                except OSError:
                    pass
            if isinstance(exc, GasCityOpsError):
                raise
            raise GasCityOpsError("Aegis Beads initialization failed safely") from exc
    finally:
        if (
            transient_home is not None
            and transient_home.name.startswith(("preflight-home-", "resume-home-"))
            and transient_home.exists()
        ):
            try:
                shutil.rmtree(transient_home)
            except OSError:
                pass
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _relative_evidence_path(path: Path, lock_root: Path, *, label: str) -> str:
    resolved = _canonical_path(path, must_exist=True, label=label)
    try:
        relative = resolved.relative_to(lock_root)
    except ValueError as exc:
        raise GasCityOpsError(f"{label} must live beneath the runtime-lock directory") from exc
    if not relative.parts or ".." in relative.parts:
        raise GasCityOpsError(f"{label} has an unsafe relative path")
    return relative.as_posix()


def _load_evidence_record(
    lock_root: Path,
    record: Mapping[str, Any],
    *,
    label: str,
) -> tuple[Path, bytes, dict[str, Any]]:
    if set(record) != {"path", "sha256"}:
        raise GasCityOpsError(f"{label} must contain exactly path and sha256")
    raw_path = record.get("path")
    digest = record.get("sha256")
    if (
        not isinstance(raw_path, str)
        or not raw_path
        or Path(raw_path).is_absolute()
        or ".." in Path(raw_path).parts
        or not isinstance(digest, str)
        or SHA256_RE.fullmatch(digest) is None
    ):
        raise GasCityOpsError(f"{label} path or digest is invalid")
    path = _canonical_path(lock_root / raw_path, must_exist=True, label=label)
    if not _is_within(path, lock_root):
        raise GasCityOpsError(f"{label} escaped the runtime-lock directory")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GasCityOpsError(f"{label} must be owner-only")
    parent = path.parent
    while _is_within(parent, lock_root):
        if parent.is_symlink() or stat.S_IMODE(parent.stat().st_mode) & 0o077:
            raise GasCityOpsError(f"{label} parent directories must be owner-only")
        if parent == lock_root:
            break
        parent = parent.parent
    content = _regular_file_bytes(path, label=label)
    if _sha256(content) != digest:
        raise GasCityOpsError(f"{label} content digest mismatch")
    value = _load_json_bytes(content, label=label)
    if not isinstance(value, dict):
        raise GasCityOpsError(f"{label} must contain one JSON object")
    return path, content, value


def _write_append_only_json(path: Path, value: Mapping[str, Any]) -> tuple[bytes, str]:
    destination = _canonical_path(path, must_exist=False, label="evidence output")
    content = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if destination.exists() or destination.is_symlink():
        existing = _regular_file_bytes(destination, label="existing evidence output")
        if existing != content:
            raise GasCityOpsError(
                f"evidence output already exists with different bytes: {destination}"
            )
        return content, _sha256(content)
    _atomic_write(destination, content, exclusive=True)
    return content, _sha256(content)


def _candidate_lock_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_candidate_lock(lock_path: Path, content: bytes) -> None:
    parent = lock_path.parent
    fd, raw_temporary = tempfile.mkstemp(prefix=".runtime-lock.validate.", dir=parent)
    temporary = Path(raw_temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        load_runtime_lock(temporary)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _replace_runtime_lock(
    lock_path: Path,
    *,
    expected_sha256: str,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare, validate, and atomically replace a runtime lock under a file lock."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    candidate_bytes = _candidate_lock_bytes(candidate)
    _validate_candidate_lock(path, candidate_bytes)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise GasCityOpsError(f"cannot lock runtime lock: {path}") from exc
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        current = _regular_file_bytes(path, label="runtime lock")
        if _sha256(current) != expected_sha256:
            raise GasCityOpsError("runtime lock changed during promotion")
        _atomic_write(path, candidate_bytes, mode=0o600)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
    return load_runtime_lock(path)


def _build_context_fingerprint(context: Path) -> dict[str, Any]:
    """Hash the exact non-runtime Docker context without following any symlink."""

    required_ignores = {
        "**",
        "!.dockerignore",
        "!docker",
        "!docker/**",
        "!artifacts",
        "!artifacts/**",
        "!formulas",
        "!formulas/aegis",
        "!formulas/aegis/mol-polecat-work.toml",
        "!config",
        "!config/city.worker.toml",
        "!config/codex-preflight-models.json",
        "docker/**/__pycache__",
        "docker/**/*.pyc",
    }
    ignore_path = context / ".dockerignore"
    ignore_bytes = _regular_file_bytes(ignore_path, label="Docker ignore file")
    try:
        ignore_lines = {
            line.strip()
            for line in ignore_bytes.decode("utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    except UnicodeDecodeError as exc:
        raise GasCityOpsError("Docker ignore file is not valid UTF-8") from exc
    if not required_ignores.issubset(ignore_lines):
        raise GasCityOpsError(
            "Docker ignore file does not exclude all runtime, VCS, and secret paths"
        )

    records: list[dict[str, Any]] = []
    discovered: set[str] = set()
    candidates = [
        ignore_path,
        *(context / "docker").rglob("*"),
        *(context / "artifacts").rglob("*"),
        context / AEGIS_POLECAT_STARTUP_FIXED_PATHS["formula_path"],
        context / "config" / "city.worker.toml",
        context / "config" / "codex-preflight-models.json",
    ]
    for path in sorted(candidates):
        relative = path.relative_to(context)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise GasCityOpsError(f"Docker build context contains a symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise GasCityOpsError(f"Docker build context contains a special file: {relative}")
        discovered.add(relative.as_posix())
        content, observed = _stable_read(path, label=f"Docker context file {relative}")
        records.append(
            {
                "path": relative.as_posix(),
                "size_bytes": observed.st_size,
                "sha256": _sha256(content),
            }
        )
    if discovered != BUILD_CONTEXT_FILES:
        raise GasCityOpsError(
            "Docker build context inventory is not exact; "
            f"missing={sorted(BUILD_CONTEXT_FILES - discovered)}, "
            f"unexpected={sorted(discovered - BUILD_CONTEXT_FILES)}"
        )
    manifest_bytes = (json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    dockerfile = context / "docker" / "Dockerfile"
    dockerfile_bytes = _regular_file_bytes(dockerfile, label="Dockerfile")
    return {
        "manifest_sha256": _sha256(manifest_bytes),
        "file_count": len(records),
        "dockerfile_sha256": _sha256(dockerfile_bytes),
        "dockerignore_sha256": _sha256(ignore_bytes),
    }


def _docker_image_id(text: str, *, label: str) -> str:
    value = text.strip()
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise GasCityOpsError(f"{label} did not return one immutable Docker image ID")
    return value


def build_locked_images(
    lock_path: Path,
    context_dir: Path,
    *,
    docker_binary: Path,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Build all locked targets without tags and write an immutable build receipt.

    The clock hook exists for deterministic unit tests.  The operator CLI never
    exposes a timestamp override.
    """

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_bytes = _regular_file_bytes(path, label="runtime lock")
    lock = load_runtime_lock(path)
    if lock["status"] != "staged_pending_provisioning":
        raise GasCityOpsError("images may be built only from a staged runtime lock")
    if any(record["image_id"] is not None for record in lock["images"].values()):
        raise GasCityOpsError("staged runtime lock already contains an image ID")
    if lock["image_receipt"]["sha256"] is not None:
        raise GasCityOpsError("staged runtime lock already contains an image receipt digest")

    context = _canonical_path(context_dir, must_exist=True, label="Docker build context")
    if not context.is_dir() or context.is_symlink():
        raise GasCityOpsError("Docker build context must be a non-symlink directory")
    docker = _canonical_path(docker_binary, must_exist=True, label="Docker binary")
    docker_bytes = _regular_file_bytes(docker, label="Docker binary")
    env = dict(os.environ if environment is None else environment)
    fingerprint_before = _build_context_fingerprint(context)
    source_artifacts = _locked_build_source_artifacts(lock)
    for relative_path, expected_digest in source_artifacts.items():
        source_bytes = _regular_file_bytes(
            context / relative_path,
            label=f"immutable build source artifact {relative_path}",
        )
        if _sha256(source_bytes) != expected_digest:
            raise GasCityOpsError(
                f"immutable build source artifact does not match the runtime lock: "
                f"{relative_path}"
            )
    version_result = _checked(
        (docker.as_posix(), "version", "--format", "{{.Client.Version}}"),
        cwd=context,
        environment=env,
        runner=runner,
    )
    docker_version = version_result.stdout.strip()
    if not docker_version or len(docker_version) > 128 or "\n" in docker_version:
        raise GasCityOpsError("Docker client version output is invalid")

    image_ids: dict[str, str] = {}
    dockerfile = context / "docker" / "Dockerfile"
    for name, target in LOCK_IMAGE_TARGETS.items():
        result = _checked(
            (
                docker.as_posix(),
                "build",
                "--pull=false",
                "--no-cache",
                "--quiet",
                "--file",
                dockerfile.as_posix(),
                "--target",
                target,
                context.as_posix(),
            ),
            cwd=context,
            environment=env,
            runner=runner,
        )
        image_id = _docker_image_id(result.stdout, label=f"Docker build for {name}")
        inspected = _checked(
            (docker.as_posix(), "image", "inspect", "--format", "{{.Id}}", image_id),
            cwd=context,
            environment=env,
            runner=runner,
        )
        if _docker_image_id(inspected.stdout, label=f"Docker inspect for {name}") != image_id:
            raise GasCityOpsError(f"Docker inspect returned a different image ID for {name}")
        image_ids[name] = image_id
    fingerprint_after = _build_context_fingerprint(context)
    if fingerprint_before != fingerprint_after:
        raise GasCityOpsError("Docker build context changed while images were being built")

    receipt = {
        "schema_version": 1,
        "kind": "immutable-image-build",
        "status": "pass",
        "built_at": _format_utc(clock()),
        "source_lock_sha256": _sha256(lock_bytes),
        "lock_schema_version": LOCK_SCHEMA_VERSION,
        "source_artifacts": source_artifacts,
        "build_context": fingerprint_after,
        "docker": {
            "binary": docker.as_posix(),
            "binary_sha256": _sha256(docker_bytes),
            "client_version": docker_version,
            "tagged": False,
            "pull": False,
            "no_cache": True,
        },
        "targets": dict(LOCK_IMAGE_TARGETS),
        "images": image_ids,
    }
    receipt_path = path.parent / lock["image_receipt"]["path"]
    _, receipt_digest = _write_append_only_json(receipt_path, receipt)
    return {
        "status": "built_pending_promotion",
        "receipt_path": receipt_path.as_posix(),
        "receipt_sha256": receipt_digest,
        "images": image_ids,
        "source_lock_sha256": receipt["source_lock_sha256"],
    }


def _verified_image_build_receipt(
    lock_path: Path,
    lock: Mapping[str, Any],
    *,
    expected_source_lock_sha256: str,
) -> tuple[bytes, dict[str, str]]:
    receipt_path = lock_path.parent / str(lock["image_receipt"]["path"])
    content = _regular_file_bytes(receipt_path, label="image build receipt")
    if stat.S_IMODE(receipt_path.stat().st_mode) & 0o077:
        raise GasCityOpsError("image build receipt must be owner-only")
    value = _load_json_bytes(content, label="image build receipt")
    if not isinstance(value, dict):
        raise GasCityOpsError("image build receipt must contain one object")
    images = value.get("images")
    if not isinstance(images, dict):
        raise GasCityOpsError("image build receipt lacks an exact image set")
    _validate_image_build_receipt_shape(
        value,
        expected_images=images,
        expected_source_artifacts=_locked_build_source_artifacts(lock),
    )
    if value.get("source_lock_sha256") != expected_source_lock_sha256 or set(images) != set(
        LOCK_IMAGE_TARGETS
    ):
        raise GasCityOpsError("image build receipt does not match the staged runtime lock")
    return content, {str(name): str(image_id) for name, image_id in images.items()}


def promote_locked_images(
    lock_path: Path,
    *,
    docker_binary: Path,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Promote only locally present, receipt-bound image IDs into the runtime lock."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_bytes = _regular_file_bytes(path, label="runtime lock")
    lock = load_runtime_lock(path)
    if lock["status"] == "provisioned_pending_canary":
        return {"status": "already_provisioned", "runtime_lock": lock}
    if lock["status"] != "staged_pending_provisioning":
        raise GasCityOpsError("image promotion requires a staged runtime lock")
    source_digest = _sha256(lock_bytes)
    receipt_bytes, image_ids = _verified_image_build_receipt(
        path,
        lock,
        expected_source_lock_sha256=source_digest,
    )
    docker = _canonical_path(docker_binary, must_exist=True, label="Docker binary")
    _regular_file_bytes(docker, label="Docker binary")
    env = dict(os.environ if environment is None else environment)
    for name, image_id in image_ids.items():
        result = _checked(
            (docker.as_posix(), "image", "inspect", "--format", "{{.Id}}", image_id),
            cwd=path.parent,
            environment=env,
            runner=runner,
        )
        if _docker_image_id(result.stdout, label=f"Docker inspect for {name}") != image_id:
            raise GasCityOpsError(f"locked image is not locally present for {name}")

    candidate = copy.deepcopy(lock)
    for name, image_id in image_ids.items():
        candidate["images"][name]["image_id"] = image_id
    candidate["image_receipt"]["sha256"] = _sha256(receipt_bytes)
    candidate["status"] = "provisioned_pending_canary"
    promoted = _replace_runtime_lock(
        path,
        expected_sha256=source_digest,
        candidate=candidate,
    )
    return {
        "status": "provisioned_pending_canary",
        "runtime_lock_sha256": _sha256(_regular_file_bytes(path, label="runtime lock")),
        "image_receipt_sha256": promoted["image_receipt"]["sha256"],
        "images": {name: record["image_id"] for name, record in promoted["images"].items()},
    }


def _file_tree_manifest(root: Path, *, label: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise GasCityOpsError(f"{label} contains a symlink: {relative}")
        observed = path.stat()
        if path.is_dir():
            entries.append(
                {
                    "path": relative.as_posix(),
                    "type": "directory",
                    "source_mode": stat.S_IMODE(observed.st_mode),
                    "source_mtime_ns": observed.st_mtime_ns,
                }
            )
            continue
        if not path.is_file():
            raise GasCityOpsError(f"{label} contains a special file: {relative}")
        content, stable = _stable_read(path, label=f"{label} file {relative}")
        entries.append(
            {
                "path": relative.as_posix(),
                "type": "file",
                "size_bytes": len(content),
                "source_mode": stat.S_IMODE(stable.st_mode),
                "source_mtime_ns": stable.st_mtime_ns,
                "sha256": _sha256(content),
            }
        )
    if not entries:
        raise GasCityOpsError(f"{label} contains no files")
    return entries


def _file_manifest_bytes(entries: Sequence[Mapping[str, Any]]) -> bytes:
    value = {
        "schema_version": 1,
        "kind": "dolt-cold-backup-file-manifest",
        "entries": list(entries),
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _tree_content_identity(entries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Compare inventory, bytes, and modes while ignoring read-induced mtimes."""

    return [
        {key: child for key, child in record.items() if key != "source_mtime_ns"}
        for record in entries
    ]


def _restore_payload_metadata(
    payload: Path,
    entries: Sequence[Mapping[str, Any]],
    *,
    root_mode: int,
    root_mtime_ns: int,
) -> None:
    for record in (item for item in entries if item["type"] == "file"):
        target = payload / str(record["path"])
        target.chmod(int(record["source_mode"]))
        os.utime(
            target,
            ns=(int(record["source_mtime_ns"]), int(record["source_mtime_ns"])),
            follow_symlinks=False,
        )
    for record in sorted(
        (item for item in entries if item["type"] == "directory"),
        key=lambda item: len(Path(str(item["path"])).parts),
        reverse=True,
    ):
        target = payload / str(record["path"])
        target.chmod(int(record["source_mode"]))
        os.utime(
            target,
            ns=(int(record["source_mtime_ns"]), int(record["source_mtime_ns"])),
            follow_symlinks=False,
        )
    payload.chmod(root_mode)
    os.utime(
        payload,
        ns=(root_mtime_ns, root_mtime_ns),
        follow_symlinks=False,
    )


def _validate_file_manifest(
    value: Any,
    *,
    expected_kind: str = "dolt-cold-backup-file-manifest",
    label: str = "cold backup",
) -> list[dict[str, Any]]:
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("kind") != expected_kind
        or not isinstance(value.get("entries"), list)
        or not value["entries"]
    ):
        raise GasCityOpsError(f"{label} file manifest is invalid")
    normalized: list[dict[str, Any]] = []
    prior = ""
    for record in value["entries"]:
        if not isinstance(record, dict) or record.get("type") not in {"file", "directory"}:
            raise GasCityOpsError(f"{label} file-manifest entry is invalid")
        expected_fields = (
            {"path", "type", "source_mode", "source_mtime_ns", "size_bytes", "sha256"}
            if record["type"] == "file"
            else {"path", "type", "source_mode", "source_mtime_ns"}
        )
        if set(record) != expected_fields:
            raise GasCityOpsError(f"{label} file-manifest entry fields are invalid")
        raw_path = record.get("path")
        relative = Path(str(raw_path))
        if (
            not isinstance(raw_path, str)
            or not raw_path
            or relative.is_absolute()
            or ".." in relative.parts
            or raw_path <= prior
            or not isinstance(record.get("source_mode"), int)
            or not 0 <= record["source_mode"] <= 0o7777
            or not isinstance(record.get("source_mtime_ns"), int)
            or record["source_mtime_ns"] < 0
        ):
            raise GasCityOpsError(f"{label} file-manifest entry is unsafe")
        if record["type"] == "file" and (
            not isinstance(record.get("size_bytes"), int)
            or record["size_bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or SHA256_RE.fullmatch(record["sha256"]) is None
        ):
            raise GasCityOpsError(f"{label} file-manifest file entry is invalid")
        prior = raw_path
        normalized.append(dict(record))
    return normalized


def _verify_backup_payload(payload: Path, entries: Sequence[Mapping[str, Any]]) -> None:
    expected = [(str(record["path"]), str(record["type"])) for record in entries]
    actual: list[tuple[str, str]] = []
    if not payload.is_dir() or payload.is_symlink():
        raise GasCityOpsError("cold backup payload is missing or is a symlink")
    for path in sorted(payload.rglob("*")):
        relative = path.relative_to(payload).as_posix()
        if path.is_symlink():
            raise GasCityOpsError(f"cold backup payload contains a symlink: {relative}")
        if path.is_dir():
            actual.append((relative, "directory"))
            continue
        if not path.is_file():
            raise GasCityOpsError(f"cold backup payload contains a special file: {relative}")
        actual.append((relative, "file"))
    if actual != expected:
        raise GasCityOpsError("cold backup payload inventory does not match its manifest")
    for record in entries:
        if record["type"] == "directory":
            observed = (payload / str(record["path"])).stat()
            if (
                stat.S_IMODE(observed.st_mode) != record["source_mode"]
                or observed.st_mtime_ns != record["source_mtime_ns"]
            ):
                raise GasCityOpsError(f"cold backup directory metadata mismatch: {record['path']}")
            continue
        observed = (payload / str(record["path"])).stat()
        content, _ = _stable_read(
            payload / str(record["path"]),
            label=f"cold backup payload {record['path']}",
        )
        if (
            stat.S_IMODE(observed.st_mode) != record["source_mode"]
            or observed.st_mtime_ns != record["source_mtime_ns"]
            or len(content) != record["size_bytes"]
            or _sha256(content) != record["sha256"]
        ):
            raise GasCityOpsError(f"cold backup payload digest mismatch: {record['path']}")


PortProbe = Callable[[str, int, float], bool]


def _default_port_probe(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _source_process_holders(source: Path, proc_root: Path) -> list[str]:
    def held_path(raw: str) -> bool:
        candidate = raw.removesuffix(" (deleted)")
        if not candidate.startswith("/"):
            return False
        normalized = Path(os.path.normpath(candidate))
        return _is_within(normalized, source)

    holders: set[str] = set()
    if not proc_root.is_dir():
        raise GasCityOpsError("process filesystem is unavailable for stopped-server proof")
    for process in sorted(proc_root.iterdir(), key=lambda item: item.name):
        if not process.name.isdigit() or int(process.name) == os.getpid():
            continue
        try:
            cmdline = (
                (process / "cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode("utf-8", errors="replace")
            )
        except OSError:
            cmdline = ""
        try:
            cwd = (process / "cwd").resolve(strict=True)
        except OSError:
            cwd = None
        if "dolt" in cmdline.lower() and (
            source.as_posix() in cmdline or (cwd is not None and _is_within(cwd, source))
        ):
            holders.add(process.name)
        descriptor_root = process / "fd"
        try:
            descriptors = list(descriptor_root.iterdir())
        except OSError:
            descriptors = []
        for descriptor in descriptors:
            try:
                raw_target = os.readlink(descriptor)
            except OSError:
                continue
            if held_path(raw_target):
                holders.add(process.name)
                break
        try:
            maps_lines = (process / "maps").read_text()
        except OSError:
            maps_lines = ""
        for line in maps_lines.splitlines():
            fields = line.split(maxsplit=5)
            if len(fields) == 6 and held_path(fields[5]):
                holders.add(process.name)
                break
    return sorted(holders, key=int)


def _dolt_stopped_attestation(
    source: Path,
    *,
    docker_binary: Path,
    host: str,
    port: int,
    container_name: str,
    runner: Runner,
    environment: Mapping[str, str],
    port_probe: PortProbe,
    proc_root: Path,
    observed_at: dt.datetime,
) -> dict[str, Any]:
    if (
        host != HQ_DOLT_ENDPOINT_HOST
        or port != HQ_DOLT_ENDPOINT_PORT
        or container_name != HQ_DOLT_CONTAINER_NAME
    ):
        raise GasCityOpsError("cold backup requires the exact locked HQ Dolt identity")
    docker = _canonical_path(docker_binary, must_exist=True, label="Docker binary")
    docker_bytes = _regular_file_bytes(docker, label="Docker binary")
    version = _checked(
        (docker.as_posix(), "version", "--format", "{{.Client.Version}}"),
        cwd=source,
        environment=environment,
        runner=runner,
    ).stdout.strip()
    if not version or "\n" in version or len(version) > 128:
        raise GasCityOpsError("Docker client version output is invalid")
    inspect = runner(
        (docker.as_posix(), "inspect", "--format", "{{.State.Running}}", container_name),
        source,
        environment,
    )
    if inspect.returncode == 0:
        running = inspect.stdout.strip().lower()
        if running not in {"true", "false"}:
            raise GasCityOpsError("Docker returned an invalid HQ container state")
        if running == "true":
            raise GasCityOpsError("HQ Dolt container is still running")
        container_state = "stopped"
    else:
        diagnostic = (inspect.stderr or inspect.stdout).strip()
        if "No such object" not in diagnostic and "No such container" not in diagnostic:
            raise GasCityOpsError(f"cannot prove HQ container state: {diagnostic[-512:]}")
        container_state = "absent"
    if port_probe(host, port, 0.5):
        raise GasCityOpsError("HQ Dolt loopback listener is still accepting connections")
    holders = _source_process_holders(source, proc_root)
    if holders:
        raise GasCityOpsError(
            "Dolt data directory is still held by process IDs: " + ", ".join(holders)
        )
    return {
        "schema_version": 1,
        "kind": "dolt-stopped-attestation",
        "status": "pass",
        "observed_at": _format_utc(observed_at),
        "source_data_dir": source.as_posix(),
        "endpoint": {"host": host, "port": port},
        "container": {"name": container_name, "state": container_state},
        "docker": {
            "binary_sha256": _sha256(docker_bytes),
            "client_version": version,
            "daemon_reachable": True,
        },
        "checks": {
            "container_not_running": True,
            "listener_absent": True,
            "source_process_holders": 0,
        },
    }


def _derive_hq_state(
    source: Path,
    *,
    database_relative_path: str,
    dolt_binary: Path,
    expected_dolt_sha256: str,
    runner: Runner,
    environment: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    relative = Path(database_relative_path)
    if (
        not database_relative_path
        or relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) != 1
    ):
        raise GasCityOpsError("HQ database path must be one safe relative directory name")
    database = _canonical_path(source / relative, must_exist=True, label="HQ database")
    if not database.is_dir() or database.is_symlink() or not _is_within(database, source):
        raise GasCityOpsError("HQ database must be a non-symlink directory under Dolt data")
    dolt = _canonical_path(dolt_binary, must_exist=True, label="Dolt binary")
    dolt_bytes = _regular_file_bytes(dolt, label="Dolt binary")
    if _sha256(dolt_bytes) != expected_dolt_sha256:
        raise GasCityOpsError("HQ-state Dolt binary does not match the runtime lock")
    version = _checked(
        (dolt.as_posix(), "version"),
        cwd=database,
        environment=environment,
        runner=runner,
    ).stdout.strip()
    if re.search(r"(?<![0-9A-Za-z])2\.2\.0(?![0-9A-Za-z])", version) is None:
        raise GasCityOpsError("HQ-state capture requires exact Dolt 2.2.0")
    commands = {
        "status": (dolt.as_posix(), "status"),
        "branch": (dolt.as_posix(), "branch", "--show-current"),
        "head": (
            dolt.as_posix(),
            "sql",
            "-r",
            "json",
            "-q",
            "SELECT DOLT_HASHOF('main') AS head",
        ),
        "working_diff": (dolt.as_posix(), "diff", "-r", "json"),
        "staged_diff": (dolt.as_posix(), "diff", "--staged", "-r", "json"),
    }
    outputs: dict[str, bytes] = {}
    for name, command in commands.items():
        result = _checked(
            command,
            cwd=database,
            environment=environment,
            runner=runner,
        )
        outputs[name] = result.stdout.encode("utf-8")
        if len(outputs[name]) > 16 * 1024 * 1024:
            raise GasCityOpsError(f"HQ-state {name} output exceeds the evidence ceiling")
    try:
        branch = outputs["branch"].decode("utf-8").strip()
        status_text = outputs["status"].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GasCityOpsError("HQ branch/status output is not valid UTF-8") from exc
    if branch != "main" or not status_text.startswith("On branch main\n"):
        raise GasCityOpsError("HQ database is not on the required main branch")
    head = _head_from_json(outputs["head"].decode("utf-8"), label="HQ Dolt head")
    diff_values: dict[str, dict[str, Any]] = {}
    empty_diff_outputs: list[str] = []
    for name in ("working_diff", "staged_diff"):
        if not outputs[name].strip():
            parsed = {"tables": []}
            outputs[name] = b'{"tables":[]}\n'
            empty_diff_outputs.append(name)
        else:
            parsed = _load_json_bytes(outputs[name], label=f"HQ {name}")
        if not isinstance(parsed, dict) or not isinstance(parsed.get("tables"), list):
            raise GasCityOpsError(f"HQ {name} is not a structured Dolt JSON diff")
        diff_values[name] = parsed
    clean_text = "nothing to commit, working tree clean" in status_text.lower()
    dirty = bool(diff_values["working_diff"]["tables"] or diff_values["staged_diff"]["tables"])
    if clean_text == dirty:
        raise GasCityOpsError("HQ status and structured working-set diffs disagree")
    raw = {
        "hq-status.txt": outputs["status"],
        "hq-working-diff.json": outputs["working_diff"],
        "hq-staged-diff.json": outputs["staged_diff"],
        "hq-head.json": outputs["head"],
    }
    receipt = {
        "schema_version": 1,
        "kind": "hq-dolt-state",
        "status": "pass",
        "database_relative_path": database_relative_path,
        "branch": branch,
        "head": head,
        "working_set_dirty": dirty,
        "dolt": {
            "version": "2.2.0",
            "binary_sha256": _sha256(dolt_bytes),
        },
        "artifacts": {name: _sha256(content) for name, content in sorted(raw.items())},
        "working_diff_table_count": len(diff_values["working_diff"]["tables"]),
        "staged_diff_table_count": len(diff_values["staged_diff"]["tables"]),
        "empty_diff_outputs_normalized": empty_diff_outputs,
    }
    return receipt, raw


def capture_cold_dolt_backup(
    source_data_dir: Path,
    output_dir: Path,
    *,
    lock_path: Path,
    dolt_binary: Path,
    docker_binary: Path,
    database_relative_path: str = HQ_DOLT_DATABASE_RELATIVE_PATH,
    endpoint_host: str = HQ_DOLT_ENDPOINT_HOST,
    endpoint_port: int = HQ_DOLT_ENDPOINT_PORT,
    container_name: str = HQ_DOLT_CONTAINER_NAME,
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    port_probe: PortProbe = _default_port_probe,
    proc_root: Path = Path("/proc"),
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Guard, derive state, and capture an exact private HQ Dolt cold backup.

    The function itself proves the container, listener, process, and open-file
    boundaries and derives HQ state with the lock-pinned Dolt binary.  No
    caller-authored stop/status assertion is accepted.  Every read command is
    enclosed by byte-and-metadata scans, so a read that mutates source state
    fails the capture.  ``clock`` and probe hooks exist only for deterministic
    tests; the CLI exposes neither override.
    """

    source = _canonical_path(source_data_dir, must_exist=True, label="Dolt data directory")
    if (
        database_relative_path != HQ_DOLT_DATABASE_RELATIVE_PATH
        or endpoint_host != HQ_DOLT_ENDPOINT_HOST
        or endpoint_port != HQ_DOLT_ENDPOINT_PORT
        or container_name != HQ_DOLT_CONTAINER_NAME
    ):
        raise GasCityOpsError("cold backup requires the exact locked HQ Dolt identity")
    if not source.is_dir() or source.is_symlink():
        raise GasCityOpsError("Dolt data directory must be a non-symlink directory")
    if stat.S_IMODE(source.stat().st_mode) & 0o077:
        raise GasCityOpsError("Dolt data directory must be owner-only before cold backup")
    source_root_stat = source.stat()
    destination = _canonical_path(output_dir, must_exist=False, label="cold backup directory")
    if _is_within(destination, source) or _is_within(source, destination):
        raise GasCityOpsError("cold backup source and destination must be disjoint")
    canonical_lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(canonical_lock)
    env = dict(os.environ if environment is None else environment)
    observed_before = clock().replace(microsecond=0)
    stopped_before = _dolt_stopped_attestation(
        source,
        docker_binary=docker_binary,
        host=endpoint_host,
        port=endpoint_port,
        container_name=container_name,
        runner=runner,
        environment=env,
        port_probe=port_probe,
        proc_root=proc_root,
        observed_at=observed_before,
    )
    before = _file_tree_manifest(source, label="Dolt data directory")
    file_manifest = _file_manifest_bytes(before)
    root = create_private_evidence_directory(destination)
    payload = root / "data"
    payload.mkdir(mode=0o700)
    try:
        for record in before:
            relative = Path(str(record["path"]))
            target = payload / relative
            if record["type"] == "directory":
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
                target.chmod(0o700)
                continue
            content, _ = _stable_read(
                source / relative,
                label=f"Dolt data source {relative}",
            )
            write_private_evidence_bytes(payload, relative.as_posix(), content)
        _restore_payload_metadata(
            payload,
            before,
            root_mode=stat.S_IMODE(source_root_stat.st_mode),
            root_mtime_ns=source_root_stat.st_mtime_ns,
        )
        after = _file_tree_manifest(source, label="Dolt data directory")
        if before != after:
            failure = {
                "schema_version": 1,
                "kind": "dolt-cold-backup-failure",
                "status": "failed",
                "reason": "source_changed_during_capture",
                "before_manifest_sha256": _sha256(file_manifest),
                "after_manifest_sha256": _sha256(_file_manifest_bytes(after)),
            }
            write_private_json_evidence(root / "cold-backup-failure.json", failure, exclusive=True)
            raise GasCityOpsError("Dolt data directory changed during cold backup")
        _verify_backup_payload(payload, before)
        payload_before_state = _file_tree_manifest(
            payload,
            label="byte-identical cold-backup payload",
        )
        state, state_artifacts = _derive_hq_state(
            payload,
            database_relative_path=database_relative_path,
            dolt_binary=dolt_binary,
            expected_dolt_sha256=lock["tools"]["dolt"]["binary_sha256"],
            runner=runner,
            environment=env,
        )
        payload_after_state = _file_tree_manifest(
            payload,
            label="byte-identical cold-backup payload",
        )
        if _tree_content_identity(payload_before_state) != _tree_content_identity(
            payload_after_state
        ):
            raise GasCityOpsError(
                "pinned Dolt state inspection changed backup payload inventory, bytes, or modes"
            )
        _restore_payload_metadata(
            payload,
            before,
            root_mode=stat.S_IMODE(source_root_stat.st_mode),
            root_mtime_ns=source_root_stat.st_mtime_ns,
        )
        _verify_backup_payload(payload, before)
        stop_before_bytes = _candidate_lock_bytes(stopped_before)
        state_bytes = _candidate_lock_bytes(state)
        write_private_evidence_bytes(root, "server-stopped-before.json", stop_before_bytes)
        write_private_evidence_bytes(root, "hq-state.json", state_bytes)
        for name, content in state_artifacts.items():
            write_private_evidence_bytes(root, name, content)
        write_private_evidence_bytes(root, "source-file-manifest.json", file_manifest)
        stopped_after = _dolt_stopped_attestation(
            source,
            docker_binary=docker_binary,
            host=endpoint_host,
            port=endpoint_port,
            container_name=container_name,
            runner=runner,
            environment=env,
            port_probe=port_probe,
            proc_root=proc_root,
            observed_at=clock().replace(microsecond=0),
        )
        final_source = _file_tree_manifest(source, label="Dolt data directory")
        final_root_stat = source.stat()
        if before != final_source:
            raise GasCityOpsError("HQ data changed before the final stopped-state proof")
        if (
            stat.S_IMODE(final_root_stat.st_mode) != stat.S_IMODE(source_root_stat.st_mode)
            or final_root_stat.st_mtime_ns != source_root_stat.st_mtime_ns
        ):
            raise GasCityOpsError("Dolt data root metadata changed during cold backup")
        stop_after_bytes = _candidate_lock_bytes(stopped_after)
        write_private_evidence_bytes(root, "server-stopped-after.json", stop_after_bytes)
        file_entries = [record for record in before if record["type"] == "file"]
        directory_entries = [record for record in before if record["type"] == "directory"]
        manifest = {
            "schema_version": 1,
            "kind": "dolt-cold-backup",
            "status": "pass",
            "captured_at": _format_utc(clock()),
            "source_data_dir": source.as_posix(),
            "source_root_mode": stat.S_IMODE(source_root_stat.st_mode),
            "source_root_mtime_ns": source_root_stat.st_mtime_ns,
            "payload_path": "data",
            "payload_metadata": "exact-source-mode-and-mtime",
            "source_metadata_restore_contract": "source-file-manifest.json",
            "file_manifest_path": "source-file-manifest.json",
            "file_manifest_sha256": _sha256(file_manifest),
            "file_count": len(file_entries),
            "directory_count": len(directory_entries),
            "total_bytes": sum(int(record["size_bytes"]) for record in file_entries),
            "server_stopped_before_sha256": _sha256(stop_before_bytes),
            "server_stopped_after_sha256": _sha256(stop_after_bytes),
            "hq_state_sha256": _sha256(state_bytes),
            "hq_head": state["head"],
            "hq_working_set_dirty": state["working_set_dirty"],
            "dolt_binary_sha256": lock["tools"]["dolt"]["binary_sha256"],
        }
        manifest_digest = write_private_json_evidence(
            root / "cold-backup-manifest.json",
            manifest,
            exclusive=True,
        )
    except BaseException:
        # The new directory deliberately remains as append-only forensic evidence.
        raise
    return {
        **manifest,
        "backup_directory": root.as_posix(),
        "manifest_path": (root / "cold-backup-manifest.json").as_posix(),
        "manifest_sha256": manifest_digest,
    }


def _validate_stopped_attestation(value: Any, *, source_data_dir: str) -> dt.datetime:
    if not isinstance(value, dict):
        raise GasCityOpsError("stopped-server attestation must contain one object")
    endpoint = value.get("endpoint")
    container = value.get("container")
    docker = value.get("docker")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "dolt-stopped-attestation"
        or value.get("status") != "pass"
        or value.get("source_data_dir") != source_data_dir
        or not isinstance(endpoint, dict)
        or endpoint
        != {
            "host": HQ_DOLT_ENDPOINT_HOST,
            "port": HQ_DOLT_ENDPOINT_PORT,
        }
        or not isinstance(container, dict)
        or container.get("name") != HQ_DOLT_CONTAINER_NAME
        or container.get("state") not in {"absent", "stopped"}
        or not isinstance(docker, dict)
        or docker.get("daemon_reachable") is not True
        or not isinstance(docker.get("binary_sha256"), str)
        or SHA256_RE.fullmatch(str(docker["binary_sha256"])) is None
        or not isinstance(docker.get("client_version"), str)
        or value.get("checks")
        != {
            "container_not_running": True,
            "listener_absent": True,
            "source_process_holders": 0,
        }
    ):
        raise GasCityOpsError("stopped-server attestation is not a strict passing probe")
    return _utc_timestamp(value.get("observed_at"), label="stopped-server observed_at")


def _validate_hq_state_receipt(
    value: Any,
    *,
    root: Path,
    expected_dolt_sha256: str,
) -> None:
    if not isinstance(value, dict):
        raise GasCityOpsError("HQ state receipt must contain one object")
    artifacts = value.get("artifacts")
    expected_artifacts = {
        "hq-status.txt",
        "hq-working-diff.json",
        "hq-staged-diff.json",
        "hq-head.json",
    }
    dolt = value.get("dolt")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "hq-dolt-state"
        or value.get("status") != "pass"
        or value.get("database_relative_path") != "hq"
        or value.get("branch") != "main"
        or not isinstance(value.get("head"), str)
        or re.fullmatch(r"[0-9a-v]{20,64}", str(value["head"]).lower()) is None
        or not isinstance(value.get("working_set_dirty"), bool)
        or not isinstance(value.get("empty_diff_outputs_normalized"), list)
        or any(
            name not in {"working_diff", "staged_diff"}
            for name in value["empty_diff_outputs_normalized"]
        )
        or len(set(value["empty_diff_outputs_normalized"]))
        != len(value["empty_diff_outputs_normalized"])
        or not isinstance(dolt, dict)
        or dolt.get("version") != "2.2.0"
        or dolt.get("binary_sha256") != expected_dolt_sha256
        or not isinstance(artifacts, dict)
        or set(artifacts) != expected_artifacts
        or any(
            not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None
            for digest in artifacts.values()
        )
    ):
        raise GasCityOpsError("HQ state receipt is invalid")
    loaded: dict[str, bytes] = {}
    for name, digest in artifacts.items():
        content = _regular_file_bytes(root / name, label=f"HQ state artifact {name}")
        if _sha256(content) != digest:
            raise GasCityOpsError(f"HQ state artifact digest mismatch: {name}")
        loaded[name] = content
    try:
        status_text = loaded["hq-status.txt"].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GasCityOpsError("HQ status artifact is not valid UTF-8") from exc
    if not status_text.startswith("On branch main\n"):
        raise GasCityOpsError("HQ status artifact does not prove the main branch")
    head = _head_from_json(loaded["hq-head.json"].decode("utf-8"), label="HQ head artifact")
    if head != value["head"]:
        raise GasCityOpsError("HQ state head does not match its raw artifact")
    diffs: dict[str, Mapping[str, Any]] = {}
    for name in ("hq-working-diff.json", "hq-staged-diff.json"):
        parsed = _load_json_bytes(loaded[name], label=name)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("tables"), list):
            raise GasCityOpsError(f"HQ state artifact is not a structured diff: {name}")
        diffs[name] = parsed
    counts = (
        len(diffs["hq-working-diff.json"]["tables"]),
        len(diffs["hq-staged-diff.json"]["tables"]),
    )
    normalized_names = {
        "working_diff": "hq-working-diff.json",
        "staged_diff": "hq-staged-diff.json",
    }
    for name in value["empty_diff_outputs_normalized"]:
        if loaded[normalized_names[name]] != b'{"tables":[]}\n':
            raise GasCityOpsError("normalized empty HQ diff artifact is not canonical")
    if (
        value.get("working_diff_table_count") != counts[0]
        or value.get("staged_diff_table_count") != counts[1]
        or value["working_set_dirty"] != bool(counts[0] or counts[1])
    ):
        raise GasCityOpsError("HQ state diff counts disagree with the receipt")


def verify_cold_dolt_backup(manifest_path: Path, *, deep: bool = True) -> dict[str, Any]:
    """Re-hash strict stop/state evidence and, by default, every payload byte."""

    path = _canonical_path(manifest_path, must_exist=True, label="cold backup manifest")
    root = path.parent
    if path.name != "cold-backup-manifest.json" or not root.is_dir() or root.is_symlink():
        raise GasCityOpsError("cold backup manifest is not in a valid backup directory")
    if stat.S_IMODE(root.stat().st_mode) & 0o077:
        raise GasCityOpsError("cold backup directory must be owner-only")
    payload_root = root / "data"
    for artifact in root.rglob("*"):
        inside_payload = artifact == payload_root or _is_within(artifact, payload_root)
        if (
            artifact.is_symlink()
            or not (artifact.is_dir() or artifact.is_file())
            or (not inside_payload and stat.S_IMODE(artifact.stat().st_mode) & 0o077)
        ):
            raise GasCityOpsError("cold backup artifacts must be private regular files/directories")
    content = _regular_file_bytes(path, label="cold backup manifest")
    value = _load_json_bytes(content, label="cold backup manifest")
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("kind") != "dolt-cold-backup"
        or value.get("status") != "pass"
        or value.get("payload_path") != "data"
        or value.get("payload_metadata") != "exact-source-mode-and-mtime"
        or value.get("source_metadata_restore_contract") != "source-file-manifest.json"
        or value.get("file_manifest_path") != "source-file-manifest.json"
        or value.get("source_root_mode") != 0o700
        or not isinstance(value.get("source_root_mtime_ns"), int)
        or not isinstance(value.get("dolt_binary_sha256"), str)
        or SHA256_RE.fullmatch(str(value["dolt_binary_sha256"])) is None
    ):
        raise GasCityOpsError("cold backup manifest is invalid")
    if stat.S_IMODE(payload_root.stat().st_mode) != value.get("source_root_mode"):
        raise GasCityOpsError("cold backup payload root mode does not match source metadata")
    if payload_root.stat().st_mtime_ns != value.get("source_root_mtime_ns"):
        raise GasCityOpsError("cold backup payload root mtime does not match source metadata")
    captured = _utc_timestamp(value.get("captured_at"), label="cold backup captured_at")
    file_manifest_bytes = _regular_file_bytes(
        root / "source-file-manifest.json",
        label="cold backup file manifest",
    )
    if _sha256(file_manifest_bytes) != value.get("file_manifest_sha256"):
        raise GasCityOpsError("cold backup file-manifest digest mismatch")
    entries = _validate_file_manifest(
        _load_json_bytes(file_manifest_bytes, label="cold backup file manifest")
    )
    files = [record for record in entries if record["type"] == "file"]
    directories = [record for record in entries if record["type"] == "directory"]
    if (
        value.get("file_count") != len(files)
        or value.get("directory_count") != len(directories)
        or value.get("total_bytes") != sum(int(record["size_bytes"]) for record in files)
    ):
        raise GasCityOpsError("cold backup manifest counts do not match its file manifest")
    stop_times: list[dt.datetime] = []
    for name, field in (
        ("server-stopped-before.json", "server_stopped_before_sha256"),
        ("server-stopped-after.json", "server_stopped_after_sha256"),
    ):
        evidence = _regular_file_bytes(root / name, label=f"cold backup {name}")
        if _sha256(evidence) != value.get(field):
            raise GasCityOpsError(f"cold backup {name} digest mismatch")
        stop_times.append(
            _validate_stopped_attestation(
                _load_json_bytes(evidence, label=name),
                source_data_dir=str(value.get("source_data_dir")),
            )
        )
    if stop_times[0] > stop_times[1] or stop_times[1] > captured:
        raise GasCityOpsError("cold backup stop/capture timestamps are inconsistent")
    state_bytes = _regular_file_bytes(root / "hq-state.json", label="HQ state receipt")
    if _sha256(state_bytes) != value.get("hq_state_sha256"):
        raise GasCityOpsError("HQ state receipt digest mismatch")
    state = _load_json_bytes(state_bytes, label="HQ state receipt")
    _validate_hq_state_receipt(
        state,
        root=root,
        expected_dolt_sha256=str(value["dolt_binary_sha256"]),
    )
    if (
        not isinstance(state, dict)
        or state.get("head") != value.get("hq_head")
        or state.get("working_set_dirty") != value.get("hq_working_set_dirty")
    ):
        raise GasCityOpsError("cold backup HQ summary does not match the state receipt")
    if deep:
        _verify_backup_payload(root / "data", entries)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(content),
        "file_manifest_sha256": value["file_manifest_sha256"],
        "file_count": len(files),
        "directory_count": len(directories),
        "total_bytes": value["total_bytes"],
        "captured_at": value["captured_at"],
        "dolt_binary_sha256": value["dolt_binary_sha256"],
        "hq_head": value["hq_head"],
        "hq_working_set_dirty": value["hq_working_set_dirty"],
    }


def _verified_provider_receipts(
    lock_path: Path,
    lock: Mapping[str, Any],
) -> dict[str, str]:
    expected = {
        "claude": ("claude-fable-5", None),
        "codex": ("gpt-5.6-sol", "xhigh"),
    }
    result: dict[str, str] = {}
    for provider, (model, effort) in expected.items():
        record = lock["providers"][provider]
        receipt_path = lock_path.parent / str(record["receipt_path"])
        content = _regular_file_bytes(receipt_path, label=f"{provider} model receipt")
        if stat.S_IMODE(receipt_path.stat().st_mode) & 0o077:
            raise GasCityOpsError(f"{provider} model receipt must be owner-only")
        value = _load_json_bytes(content, label=f"{provider} model receipt")
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != MODEL_RECEIPT_SCHEMA_VERSION
            or value.get("status") not in {"pass", "verified"}
            or value.get("provider") != provider
            or value.get("observed_model") != model
            or value.get("expected_model", model) != model
            or value.get("reasoning_effort", effort) != effort
            or value.get("observed_effort", effort) != effort
            or not isinstance(value.get("transcript_sha256"), str)
            or SHA256_RE.fullmatch(value["transcript_sha256"]) is None
        ):
            raise GasCityOpsError(f"{provider} model receipt does not prove the locked model")
        result[provider] = _sha256(content)
    return result


def _generation_one_migration_target_binding(
    generation_record: Mapping[str, Any],
    *,
    generation_record_sha256: str,
) -> dict[str, Any]:
    """Derive the one production repository from a verified generation-1 baseline."""

    baseline = generation_record.get("baseline_evidence")
    migration = baseline.get("migration") if type(baseline) is dict else None
    raw_target = migration.get("target_directory") if type(migration) is dict else None
    if (
        generation_record.get("generation") != 1
        or generation_record.get("transition") != "initialize-taskmaster"
        or type(baseline) is not dict
        or set(baseline) != {"snapshot", "migration", "recovery"}
        or type(migration) is not dict
        or type(raw_target) is not str
        or not raw_target
        or SHA256_RE.fullmatch(generation_record_sha256) is None
    ):
        raise GasCityOpsError(
            "verified generation-1 authority is missing its Aegis migration target"
        )
    target = Path(raw_target)
    if not target.is_absolute() or ".." in target.parts or target.as_posix() != raw_target:
        raise GasCityOpsError("verified generation-1 Aegis migration target is not canonical")
    identity = _secure_primary_repository(target)
    if identity.repository_root != target:
        raise GasCityOpsError(
            "verified generation-1 Aegis migration target is not the primary repository"
        )
    return {
        "generation": 1,
        "generation_record_sha256": generation_record_sha256,
        "repository_root": identity.repository_root.as_posix(),
        "git_common_dir": identity.git_common_dir.as_posix(),
        "repository_key": identity.repository_key,
    }


def _require_aegis_migration_target(
    requested_repo: Path,
    expected: Mapping[str, Any],
    *,
    label: str,
) -> Path:
    """Require a caller-selected path to be the authority-bound primary checkout."""

    if (
        type(expected) is not dict
        or set(expected) != AEGIS_MIGRATION_TARGET_FIELDS
        or expected.get("generation") != 1
        or type(expected.get("generation_record_sha256")) is not str
        or SHA256_RE.fullmatch(expected["generation_record_sha256"]) is None
        or any(
            type(expected.get(field)) is not str or not expected[field]
            for field in ("repository_root", "git_common_dir", "repository_key")
        )
        or SHA256_RE.fullmatch(str(expected.get("repository_key"))) is None
    ):
        raise GasCityOpsError("live authority has an invalid Aegis migration-target binding")
    identity = _secure_primary_repository(requested_repo)
    observed = {
        "generation": 1,
        "generation_record_sha256": expected["generation_record_sha256"],
        "repository_root": identity.repository_root.as_posix(),
        "git_common_dir": identity.git_common_dir.as_posix(),
        "repository_key": identity.repository_key,
    }
    if observed != dict(expected):
        raise GasCityOpsError(f"{label} is not the generation-1 canonical Aegis migration target")
    return identity.repository_root


def _full_live_authority_state(
    lock_root: Path,
) -> tuple[dict[str, Any], bytes, dict[str, Any], dict[str, Any]]:
    # Local import is intentional: gas_city_authority uses the evidence
    # validators in this module while it replays the lifecycle chain.
    from aegis_foundation import gas_city_authority

    try:
        report = gas_city_authority.verify_authority_chain(
            lock_root,
            rig=LIVE_AUTHORITY_IDENTITY["rig"],
            beads_prefix=LIVE_AUTHORITY_IDENTITY["beads_prefix"],
            database=LIVE_AUTHORITY_IDENTITY["database"],
        )
    except gas_city_authority.GasCityAuthorityError as exc:
        raise GasCityOpsError(f"live task-authority lifecycle is invalid: {exc}") from exc
    if (
        report.current is None
        or report.current.mode is not task_authority.TaskAuthorityMode.BEADS
        or report.current.generation != 2
        or len(report.generation_records) != 2
        or [record.get("generation") for record in report.generation_records] != [1, 2]
        or [record.get("transition") for record in report.generation_records]
        != ["initialize-taskmaster", "activate-beads"]
        or report.recoverable_attempt is not None
        or report.uncommitted_attempts
    ):
        raise GasCityOpsError(
            "production requires a complete generation-1 Taskmaster to generation-2 "
            "Beads authority lifecycle with no pending attempts"
        )
    receipt_path = lock_root / LIVE_AUTHORITY_RECEIPT_PATH
    try:
        receipt = task_authority.load_authority_receipt(
            receipt_path,
            expected_rig=LIVE_AUTHORITY_IDENTITY["rig"],
            expected_beads_prefix=LIVE_AUTHORITY_IDENTITY["beads_prefix"],
            expected_database=LIVE_AUTHORITY_IDENTITY["database"],
        )
    except task_authority.TaskAuthorityError as exc:
        raise GasCityOpsError(f"live task-authority receipt is invalid: {exc}") from exc
    content = _regular_file_bytes(receipt_path, label="live task-authority receipt")
    if content != task_authority.receipt_bytes(receipt):
        raise GasCityOpsError("live task-authority receipt is not canonical")
    if receipt.mode is not task_authority.TaskAuthorityMode.BEADS or receipt.generation != 2:
        raise GasCityOpsError("production requires live generation-2 Beads authority")
    mapping = task_authority.receipt_mapping(receipt)
    binding = {
        "receipt_sha256": _sha256(content),
        "rig": receipt.rig,
        "mode": receipt.mode.value,
        "generation": receipt.generation,
        "beads_prefix": receipt.beads_prefix,
        "database": receipt.database,
        "activated_at": receipt.activated_at,
        "previous_receipt_sha256": receipt.previous_receipt_sha256,
        "taskmaster_snapshot_sha256": receipt.evidence.taskmaster_snapshot_sha256,
        "migration_report_sha256": receipt.evidence.migration_report_sha256,
        "backup_restore_report_sha256": receipt.evidence.backup_restore_report_sha256,
    }
    if mapping != {
        "schema_version": task_authority.RECEIPT_SCHEMA,
        "rig": binding["rig"],
        "mode": binding["mode"],
        "beads_prefix": binding["beads_prefix"],
        "database": binding["database"],
        "taskmaster_snapshot_sha256": binding["taskmaster_snapshot_sha256"],
        "migration_report_sha256": binding["migration_report_sha256"],
        "backup_restore_report_sha256": binding["backup_restore_report_sha256"],
        "generation": binding["generation"],
        "activated_at": binding["activated_at"],
        "previous_receipt_sha256": binding["previous_receipt_sha256"],
    }:
        raise GasCityOpsError("live task-authority receipt projection is inconsistent")
    generation_records: list[dict[str, str | int]] = []
    for generation in (1, 2):
        relative = (
            Path("runtime")
            / "authority"
            / "history"
            / LIVE_AUTHORITY_IDENTITY["rig"]
            / f"generation-{generation:08d}.json"
        )
        record_path = lock_root / relative
        record_content = _regular_file_bytes(
            record_path, label=f"authority generation {generation} record"
        )
        generation_records.append(
            {
                "generation": generation,
                "path": relative.as_posix(),
                "sha256": _sha256(record_content),
            }
        )
    if report.current_record_sha256 != generation_records[-1]["sha256"]:
        raise GasCityOpsError("authority current history digest is inconsistent")
    history = {
        "current_record_sha256": report.current_record_sha256,
        "transitions": ["initialize-taskmaster", "activate-beads"],
        "generation_records": generation_records,
    }
    migration_target = _generation_one_migration_target_binding(
        report.generation_records[0],
        generation_record_sha256=str(generation_records[0]["sha256"]),
    )
    return binding, content, history, migration_target


def _live_authority_binding(lock_root: Path) -> tuple[dict[str, Any], bytes]:
    binding, content, _, _ = _full_live_authority_state(lock_root)
    return binding, content


def capture_authority_evidence(
    lock_path: Path,
    snapshot_dir: Path,
    output_path: Path,
    *,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Capture immutable evidence from the live receipt and frozen snapshot.

    ``clock`` is test-only; the operator CLI exposes no timestamp override.
    """

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    load_runtime_lock(path)
    binding, receipt_bytes, history, _ = _full_live_authority_state(path.parent)
    snapshot = _canonical_path(snapshot_dir, must_exist=True, label="snapshot directory")
    if not _is_within(snapshot, path.parent):
        raise GasCityOpsError("authority snapshot must live beneath the city root")
    source_bytes, snapshot_manifest = load_taskmaster_snapshot(snapshot)
    manifest_bytes = _regular_file_bytes(
        snapshot / "snapshot-manifest.json",
        label="snapshot manifest",
    )
    if _sha256(manifest_bytes) != binding["taskmaster_snapshot_sha256"]:
        raise GasCityOpsError("live authority is not bound to the frozen Taskmaster snapshot")
    value = {
        "schema_version": 1,
        "kind": "task-authority-canary",
        "status": "pass",
        "captured_at": _format_utc(clock()),
        "authority_receipt": {
            "path": LIVE_AUTHORITY_RECEIPT_PATH,
            "sha256": _sha256(receipt_bytes),
            "binding": binding,
        },
        "authority_history": history,
        "taskmaster_snapshot": {
            "directory": snapshot.relative_to(path.parent).as_posix(),
            "manifest_sha256": _sha256(manifest_bytes),
            "source_sha256": snapshot_manifest["source"]["sha256"],
        },
    }
    destination = _safe_evidence_output(
        path.parent,
        output_path,
        label="authority evidence output",
    )
    _, digest = _write_append_only_json(destination, value)
    return {**value, "evidence_path": destination.as_posix(), "evidence_sha256": digest}


def _validated_authority_evidence(
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    evidence_records: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Any], bytes]:
    if set(value) != {
        "schema_version",
        "kind",
        "status",
        "captured_at",
        "authority_receipt",
        "authority_history",
        "taskmaster_snapshot",
    }:
        raise GasCityOpsError("authority evidence fields are not exact")
    captured_at = _utc_timestamp(value.get("captured_at"), label="authority captured_at")
    authority_record = value.get("authority_receipt")
    history_record = value.get("authority_history")
    snapshot_record = value.get("taskmaster_snapshot")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "task-authority-canary"
        or value.get("status") != "pass"
        or not isinstance(authority_record, dict)
        or set(authority_record) != {"path", "sha256", "binding"}
        or authority_record.get("path") != LIVE_AUTHORITY_RECEIPT_PATH
        or not isinstance(history_record, dict)
        or set(history_record) != {"current_record_sha256", "transitions", "generation_records"}
        or not isinstance(snapshot_record, dict)
        or set(snapshot_record) != {"directory", "manifest_sha256", "source_sha256"}
    ):
        raise GasCityOpsError("authority evidence is invalid")
    binding, receipt_bytes, live_history, _ = _full_live_authority_state(lock_root)
    if (
        authority_record.get("sha256") != _sha256(receipt_bytes)
        or authority_record.get("binding") != binding
        or history_record != live_history
        or captured_at < _utc_timestamp(binding["activated_at"], label="authority activated_at")
    ):
        raise GasCityOpsError("authority evidence does not match the live receipt")
    raw_snapshot = snapshot_record.get("directory")
    if not isinstance(raw_snapshot, str) or not raw_snapshot:
        raise GasCityOpsError("authority snapshot directory is invalid")
    relative_snapshot = Path(raw_snapshot)
    if relative_snapshot.is_absolute() or ".." in relative_snapshot.parts:
        raise GasCityOpsError("authority snapshot directory is unsafe")
    snapshot = _canonical_path(
        lock_root / relative_snapshot,
        must_exist=True,
        label="authority snapshot directory",
    )
    if not _is_within(snapshot, lock_root):
        raise GasCityOpsError("authority snapshot escaped the city root")
    source_bytes, snapshot_manifest = load_taskmaster_snapshot(snapshot)
    manifest_bytes = _regular_file_bytes(
        snapshot / "snapshot-manifest.json",
        label="authority snapshot manifest",
    )
    source_sha = _sha256(source_bytes)
    if (
        snapshot_record.get("manifest_sha256") != _sha256(manifest_bytes)
        or snapshot_record.get("source_sha256") != source_sha
        or snapshot_manifest["source"]["sha256"] != source_sha
        or binding["taskmaster_snapshot_sha256"] != _sha256(manifest_bytes)
    ):
        raise GasCityOpsError("authority evidence does not match the frozen snapshot")
    if set(evidence_records) < {"migration", "recovery", "authority"}:
        raise GasCityOpsError("authority validation lacks migration or recovery evidence")
    _, _, migration = _load_evidence_record(
        lock_root,
        evidence_records["migration"],
        label="migration authority evidence",
    )
    artifacts = migration.get("artifacts") if isinstance(migration, dict) else None
    recovery_digest = evidence_records["recovery"].get("sha256")
    if (
        not isinstance(artifacts, dict)
        or migration.get("source_sha256") != source_sha
        or artifacts.get("migration-report.json") != binding["migration_report_sha256"]
        or recovery_digest != binding["backup_restore_report_sha256"]
    ):
        raise GasCityOpsError("live authority evidence chain does not match promotion inputs")
    return binding, source_bytes


def _validate_migration_evidence(
    path: Path,
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    deep: bool,
    source_bytes: bytes | None,
) -> None:
    artifacts = value.get("artifacts")
    if (
        set(value) != {"schema_version", "status", "source_sha256", "artifacts"}
        or value.get("schema_version") != "taskmaster-beads-migration-evidence/v1"
        or value.get("status") != "pass"
        or not isinstance(value.get("source_sha256"), str)
        or SHA256_RE.fullmatch(str(value["source_sha256"])) is None
        or not isinstance(artifacts, dict)
        or set(artifacts) != MIGRATION_REQUIRED_ARTIFACTS
    ):
        raise GasCityOpsError("migration evidence does not prove an exact successful migration")
    loaded: dict[str, bytes] = {}
    for relative_name, digest in artifacts.items():
        relative = Path(str(relative_name))
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
        ):
            raise GasCityOpsError("migration evidence contains an unsafe artifact record")
        if deep:
            artifact_path = path.parent / relative
            if stat.S_IMODE(artifact_path.stat().st_mode) & 0o077:
                raise GasCityOpsError(f"migration artifact must be owner-only: {relative_name}")
            artifact = _regular_file_bytes(
                artifact_path,
                label=f"migration artifact {relative_name}",
            )
            if _sha256(artifact) != digest:
                raise GasCityOpsError(f"migration artifact digest mismatch: {relative_name}")
            loaded[relative_name] = artifact
    if not deep:
        return
    if source_bytes is None or _sha256(source_bytes) != value["source_sha256"]:
        raise GasCityOpsError("migration evidence is not bound to the frozen Taskmaster bytes")
    report = _load_json_bytes(loaded["migration-report.json"], label="migration report")
    if not isinstance(report, dict) or set(report) != {
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
    }:
        raise GasCityOpsError("migration report fields are not exact")
    source_record = report.get("source")
    target = report.get("target")
    if (
        report.get("schema_version") != taskmaster_beads.MIGRATION_RUN_SCHEMA
        or report.get("status") != "pass"
        or source_record != {"sha256": value["source_sha256"], "tag": "master"}
        or not isinstance(target, dict)
        or set(target) != {"directory", "database", "beads_version"}
        or not isinstance(target.get("directory"), str)
        or not target["directory"]
        or target.get("database") != LIVE_AUTHORITY_IDENTITY["database"]
        or target.get("beads_version") != taskmaster_beads.TARGET_BEADS_VERSION
        or report.get("credential_transport") != "runner-environment-only"
    ):
        raise GasCityOpsError("migration report is not the locked Aegis migration")
    validate_locked_operation_toolchain_evidence(
        lock_root / "runtime-lock.json",
        report.get("locked_toolchain"),
    )
    try:
        regenerated = taskmaster_beads.build_artifacts(
            source_bytes,
            tag="master",
            prefix=LIVE_AUTHORITY_IDENTITY["beads_prefix"],
            expected_source_sha256=str(value["source_sha256"]),
        )
    except (taskmaster_beads.ConversionError, taskmaster_beads.ReconciliationError) as exc:
        raise GasCityOpsError(f"migration conversion evidence is invalid: {exc}") from exc
    conversion = {
        name.removeprefix("conversion/"): content
        for name, content in loaded.items()
        if name.startswith("conversion/")
    }
    if conversion != dict(regenerated.artifacts):
        raise GasCityOpsError("migration conversion artifacts are not deterministic")
    try:
        first_verification = taskmaster_beads.verify_export(
            loaded["exports/first.jsonl"],
            source_bytes=source_bytes,
            artifacts=conversion,
            expected_source_sha256=str(value["source_sha256"]),
        )
        final_verification = taskmaster_beads.verify_export(
            loaded["exports/final.jsonl"],
            source_bytes=source_bytes,
            artifacts=conversion,
            expected_source_sha256=str(value["source_sha256"]),
        )
    except taskmaster_beads.ReconciliationError as exc:
        raise GasCityOpsError(f"migration export reconciliation failed: {exc}") from exc
    try:
        first_canonical = taskmaster_beads._canonical_operational_export(
            loaded["exports/first.jsonl"],
            step="promotion first export",
        )
        final_canonical = taskmaster_beads._canonical_operational_export(
            loaded["exports/final.jsonl"],
            step="promotion final export",
        )
    except taskmaster_beads.OperationalMigrationError as exc:
        raise GasCityOpsError(f"migration canonical export is invalid: {exc}") from exc
    if first_canonical != final_canonical:
        raise GasCityOpsError("migration idempotency exports are not canonically identical")
    empty = _load_json_bytes(
        loaded["checkpoints/empty-target.json"],
        label="empty-target checkpoint",
    )
    first = _load_json_bytes(
        loaded["checkpoints/first-import.json"],
        label="first-import checkpoint",
    )
    second = _load_json_bytes(
        loaded["checkpoints/second-import.json"],
        label="second-import checkpoint",
    )
    empty_fields = {
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
    if (
        not isinstance(empty, dict)
        or set(empty) != empty_fields
        or empty.get("schema_version") != taskmaster_beads.MIGRATION_RUN_SCHEMA
        or empty.get("status") != "pass"
        or empty.get("phase") != "empty-target"
        or {
            name: empty.get(name)
            for name in empty_fields - {"schema_version", "status", "phase", "commit_count"}
        }
        != {
            "issue_count": 0,
            "working_set_changes": 1,
            "expected_config_changes": 1,
            "unexpected_working_changes": 0,
            "branch_count": 1,
            "main_branch_count": 1,
        }
        or not isinstance(empty.get("commit_count"), int)
        or empty["commit_count"] < 1
    ):
        raise GasCityOpsError("empty-target migration checkpoint is invalid")
    checkpoint_fields = {
        "schema_version",
        "status",
        "phase",
        "source_sha256",
        "preflight_dolt_main_head",
        "first_dolt_main_head",
        "import",
    }
    second_fields = checkpoint_fields - {"preflight_dolt_main_head"} | {"final_dolt_main_head"}
    if (
        not isinstance(first, dict)
        or set(first) != checkpoint_fields
        or first.get("schema_version") != taskmaster_beads.MIGRATION_RUN_SCHEMA
        or first.get("status") != "mutation-observed"
        or first.get("phase") != "first-import"
        or first.get("source_sha256") != value["source_sha256"]
        or not isinstance(second, dict)
        or set(second) != second_fields
        or second.get("schema_version") != taskmaster_beads.MIGRATION_RUN_SCHEMA
        or second.get("status") != "mutation-observed"
        or second.get("phase") != "second-import"
        or second.get("source_sha256") != value["source_sha256"]
    ):
        raise GasCityOpsError("migration import checkpoints are invalid")
    issue_count = int(regenerated.manifest["counts"]["issues"])
    summary_fields = {
        "schema_version",
        "created",
        "skipped",
        "dry_run",
        "ids_count",
        "stale_skipped_ids_count",
        "tie_kept_local_ids_count",
        "updated_issues_count",
    }
    for label, summary, dry_run, ids_count in (
        ("dry run", report.get("dry_run"), True, 0),
        ("first import", report.get("first_import"), False, issue_count),
        ("second import", report.get("second_import"), False, issue_count),
    ):
        if (
            not isinstance(summary, dict)
            or set(summary) != summary_fields
            or summary.get("created") != issue_count
            or summary.get("skipped") != 0
            or summary.get("dry_run") is not dry_run
            or summary.get("ids_count") != ids_count
            or any(
                summary.get(name) != 0
                for name in (
                    "stale_skipped_ids_count",
                    "tie_kept_local_ids_count",
                    "updated_issues_count",
                )
            )
        ):
            raise GasCityOpsError(f"migration {label} summary is invalid")
    if (
        first.get("import") != report["first_import"]
        or second.get("import") != report["second_import"]
    ):
        raise GasCityOpsError("migration checkpoint import summaries disagree")
    counts = regenerated.manifest["counts"]
    if (
        report.get("counts")
        != {
            "preexisting_records": 0,
            "manifest_issues": issue_count,
            "blocker_relationships": counts["blocker_relationships"],
            "hierarchy_relationships": counts["hierarchy_relationships"],
        }
        or report.get("artifact_digests") != regenerated.manifest["digests"]
    ):
        raise GasCityOpsError("migration report counts or artifact digests disagree")
    empty_attestation = {
        key: empty[key] for key in empty_fields - {"schema_version", "status", "phase"}
    }
    if (
        report.get("empty_target_attestation") != empty_attestation
        or report.get("first_verification") != first_verification
        or report.get("final_verification") != final_verification
    ):
        raise GasCityOpsError("migration report does not match checkpoints or exports")
    preflight_head = first.get("preflight_dolt_main_head")
    first_head = first.get("first_dolt_main_head")
    final_head = second.get("final_dolt_main_head")
    idempotency = report.get("idempotency")
    expected_idempotency_fields = {
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
    canonical_export_digest = _sha256(final_canonical)
    first_raw_digest = _sha256(loaded["exports/first.jsonl"])
    final_raw_digest = _sha256(loaded["exports/final.jsonl"])
    raw_export_unchanged = loaded["exports/first.jsonl"] == loaded["exports/final.jsonl"]
    if (
        second.get("first_dolt_main_head") != first_head
        or first_head == preflight_head
        or final_head != first_head
        or not isinstance(idempotency, dict)
        or set(idempotency) != expected_idempotency_fields
        or idempotency
        != {
            "status": "pass",
            "canonical_export_sha256": canonical_export_digest,
            "first_raw_export_sha256": first_raw_digest,
            "final_raw_export_sha256": final_raw_digest,
            "preflight_dolt_main_head": preflight_head,
            "post_dry_run_dolt_main_head": preflight_head,
            "first_dolt_main_head": first_head,
            "final_dolt_main_head": final_head,
            "dry_run_head_unchanged": True,
            "first_import_advanced_main": True,
            "export_unchanged": True,
            "raw_export_unchanged": raw_export_unchanged,
            "dolt_main_head_unchanged": True,
        }
    ):
        raise GasCityOpsError("migration report does not prove exact idempotency")


def _validate_recorded_dolt_server(
    value: Any,
    endpoint: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "container_name",
        "container_id",
        "image_id",
        "running",
        "published_endpoint",
        "endpoint_publisher",
        "data_mount",
        "backup_mount",
        "docker_binary_sha256",
    }:
        raise GasCityOpsError(f"{label} identity fields are not exact")
    published = value.get("published_endpoint")
    publisher = value.get("endpoint_publisher")
    mount = value.get("data_mount")
    backup_mount = value.get("backup_mount")
    if (
        type(value.get("container_name")) is not str
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value["container_name"]) is None
        or type(value.get("container_id")) is not str
        or re.fullmatch(r"[0-9a-f]{64}", value["container_id"]) is None
        or type(value.get("image_id")) is not str
        or re.fullmatch(r"[0-9a-f]{64}", value["image_id"]) is None
        or value.get("running") is not True
        or type(value.get("docker_binary_sha256")) is not str
        or SHA256_RE.fullmatch(value["docker_binary_sha256"]) is None
        or type(published) is not dict
        or published != {"host": "loopback", "port": endpoint.get("port")}
        or type(publisher) is not dict
        or set(publisher)
        != {
            "mode",
            "container_name",
            "container_id",
            "image_id",
            "published_endpoint",
            "target_container_id",
            "target_service",
            "shared_networks",
            "read_only_rootfs",
            "cap_drop",
            "no_new_privileges",
            "command",
        }
        or _loopback_host(str(endpoint.get("host", ""))) != "loopback"
        or type(mount) is not dict
        or set(mount) != {"type", "source", "name", "destination"}
        or mount.get("type") not in {"bind", "volume"}
        or type(mount.get("source")) is not str
        or not Path(mount["source"]).is_absolute()
        or mount.get("destination") != DOLT_DATA_MOUNT_DESTINATION
        or (
            mount.get("type") == "volume"
            and (
                type(mount.get("name")) is not str
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", mount["name"]) is None
            )
        )
        or (mount.get("type") == "bind" and mount.get("name") is not None)
        or type(backup_mount) is not dict
        or set(backup_mount) != {"type", "source", "name", "destination", "read_write"}
        or backup_mount.get("type") != "bind"
        or type(backup_mount.get("source")) is not str
        or not Path(backup_mount["source"]).is_absolute()
        or backup_mount.get("name") is not None
        or backup_mount.get("destination") != backup_mount.get("source")
        or type(backup_mount.get("read_write")) is not bool
    ):
        raise GasCityOpsError(f"{label} identity is invalid")
    publisher_mode = publisher.get("mode")
    publisher_name = publisher.get("container_name")
    publisher_id = publisher.get("container_id")
    publisher_image = publisher.get("image_id")
    target_service = publisher.get("target_service")
    shared_networks = publisher.get("shared_networks")
    command = publisher.get("command")
    if (
        publisher_mode not in {"direct", "relay"}
        or type(publisher_name) is not str
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", publisher_name) is None
        or type(publisher_id) is not str
        or re.fullmatch(r"[0-9a-f]{64}", publisher_id) is None
        or type(publisher_image) is not str
        or re.fullmatch(r"[0-9a-f]{64}", publisher_image) is None
        or publisher.get("published_endpoint") != published
        or publisher.get("target_container_id") != value.get("container_id")
        or type(shared_networks) is not list
        or shared_networks != sorted(set(shared_networks))
        or any(
            type(network) is not str
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", network) is None
            for network in shared_networks
        )
        or publisher.get("read_only_rootfs") is not True
        or publisher.get("cap_drop") != ["ALL"]
        or publisher.get("no_new_privileges") is not True
    ):
        raise GasCityOpsError(f"{label} endpoint publisher identity is invalid")
    if publisher_mode == "direct":
        if (
            publisher_name != value.get("container_name")
            or publisher_id != value.get("container_id")
            or publisher_image != value.get("image_id")
            or target_service is not None
            or shared_networks
            or command is not None
        ):
            raise GasCityOpsError(f"{label} direct endpoint publisher is inconsistent")
    else:
        expected_name = f"{value.get('container_name')}-loopback"
        if (
            publisher_name != expected_name
            or publisher_id == value.get("container_id")
            or type(target_service) is not str
            or SAFE_NAME_RE.fullmatch(target_service) is None
            or not shared_networks
            or type(command) is not list
            or command
            != [
                "/usr/bin/socat",
                "TCP4-LISTEN:3306,reuseaddr,fork,nodelay",
                f"TCP4:{target_service}:3306,nodelay",
            ]
        ):
            raise GasCityOpsError(f"{label} relay endpoint publisher is inconsistent")
    return dict(value)


def validate_native_restore_evidence(
    lock_path: Path,
    value: Mapping[str, Any],
    *,
    expected_source_endpoint: DoltEndpoint | None = None,
    expected_source_container: str | None = None,
    expected_source_image_id: str | None = None,
    expected_source_relay_image_id: str | None = None,
) -> dict[str, Any]:
    source = value.get("source_endpoint")
    restore = value.get("restore_endpoint")
    captured_at = _utc_timestamp(
        value.get("captured_at"),
        label="recovery captured_at",
    )
    verified_at = _utc_timestamp(
        value.get("verified_at"),
        label="recovery verified_at",
    )
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "captured_at",
            "verified_at",
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
        or value.get("schema_version") != NATIVE_RESTORE_SCHEMA_VERSION
        or value.get("kind") != "dolt-native-restore-drill"
        or value.get("status") != "pass"
        or value.get("secrets_included") is not False
        or not isinstance(source, dict)
        or not isinstance(restore, dict)
        or set(source) != {"host", "port", "user", "database"}
        or set(restore) != {"host", "port", "user", "database"}
        or not isinstance(source.get("host"), str)
        or not source["host"]
        or not isinstance(restore.get("host"), str)
        or not restore["host"]
        or not isinstance(source.get("port"), int)
        or not 1 <= source["port"] <= 65535
        or not isinstance(restore.get("port"), int)
        or not 1 <= restore["port"] <= 65535
        or any(
            not isinstance(endpoint.get(field), str)
            or SAFE_NAME_RE.fullmatch(str(endpoint[field])) is None
            for endpoint in (source, restore)
            for field in ("user", "database")
        )
        or (_loopback_host(str(source.get("host"))), source.get("port"))
        == (_loopback_host(str(restore.get("host"))), restore.get("port"))
        or not isinstance(value.get("backup_path"), str)
        or not Path(str(value["backup_path"])).is_absolute()
        or not isinstance(value.get("backup_server_path"), str)
        or not Path(str(value["backup_server_path"])).is_absolute()
        or not isinstance(value.get("backup_manifest_path"), str)
        or not Path(str(value["backup_manifest_path"])).is_absolute()
        or not isinstance(value.get("backup_manifest_sha256"), str)
        or SHA256_RE.fullmatch(str(value["backup_manifest_sha256"])) is None
        or not isinstance(value.get("dolt_head"), str)
        or re.fullmatch(r"[0-9a-v]{20,64}", str(value["dolt_head"]).lower()) is None
        or not isinstance(value.get("canonical_export_sha256"), str)
        or SHA256_RE.fullmatch(str(value["canonical_export_sha256"])) is None
        or not isinstance(value.get("backup_status"), Mapping)
        or not value["backup_status"]
        or verified_at < captured_at
    ):
        raise GasCityOpsError("recovery evidence does not prove a distinct-server restore")
    source_server = _validate_recorded_dolt_server(
        value.get("source_server"), source, label="source Dolt server"
    )
    restore_server = _validate_recorded_dolt_server(
        value.get("restore_server"), restore, label="restore Dolt server"
    )
    if expected_source_endpoint is not None and source != dataclasses.asdict(
        expected_source_endpoint
    ):
        raise GasCityOpsError("recovery source endpoint is not the Aegis authority endpoint")
    if (
        expected_source_container is not None
        and source_server["container_name"] != expected_source_container
    ):
        raise GasCityOpsError("recovery source container is not the Aegis Dolt server")
    if expected_source_image_id is not None:
        normalized_image = expected_source_image_id.removeprefix("sha256:")
        if (
            re.fullmatch(r"[0-9a-f]{64}", normalized_image) is None
            or source_server["image_id"] != normalized_image
        ):
            raise GasCityOpsError("recovery source image does not match the runtime lock")
    if expected_source_relay_image_id is not None:
        normalized_relay = expected_source_relay_image_id.removeprefix("sha256:")
        publisher = source_server["endpoint_publisher"]
        if (
            re.fullmatch(r"[0-9a-f]{64}", normalized_relay) is None
            or publisher["mode"] != "relay"
            or publisher["image_id"] != normalized_relay
        ):
            raise GasCityOpsError("recovery source endpoint relay does not match the runtime lock")
    if (
        source_server["container_id"] == restore_server["container_id"]
        or source_server["docker_binary_sha256"] != restore_server["docker_binary_sha256"]
        or (
            source_server["data_mount"]["type"],
            source_server["data_mount"]["source"],
            source_server["data_mount"]["name"],
        )
        == (
            restore_server["data_mount"]["type"],
            restore_server["data_mount"]["source"],
            restore_server["data_mount"]["name"],
        )
    ):
        raise GasCityOpsError("recovery evidence does not prove isolated containers and data")
    source_backup_mount = source_server["backup_mount"]
    restore_backup_mount = restore_server["backup_mount"]
    if (
        source_backup_mount["source"] != restore_backup_mount["source"]
        or source_backup_mount["destination"] != source_backup_mount["source"]
        or restore_backup_mount["destination"] != restore_backup_mount["source"]
        or source_backup_mount["read_write"] is not True
        or restore_backup_mount["read_write"] is not False
    ):
        raise GasCityOpsError(
            "recovery evidence does not bind the shared least-privilege backup mount"
        )
    preflight = value.get("restore_preflight")
    if (
        type(preflight) is not dict
        or set(preflight) != {"empty_issue_count", "empty_export_sha256", "dolt_head"}
        or preflight.get("empty_issue_count") != 0
        or preflight.get("empty_export_sha256") != _sha256(b"")
        or type(preflight.get("dolt_head")) is not str
        or re.fullmatch(r"[0-9a-v]{20,64}", preflight["dolt_head"].lower()) is None
    ):
        raise GasCityOpsError("recovery evidence does not prove an empty restore target")
    validate_locked_operation_toolchain_evidence(
        lock_path,
        value.get("locked_toolchain"),
    )
    backup = _canonical_path(
        Path(str(value["backup_path"])),
        must_exist=True,
        label="native backup directory",
    )
    backup_mount_root = _canonical_path(
        Path(source_backup_mount["source"]),
        must_exist=True,
        label="native backup mount root",
    )
    if not _is_within(backup, backup_mount_root) or backup == backup_mount_root:
        raise GasCityOpsError("native backup is outside its recorded server mount")
    expected_server_backup = (
        Path(source_backup_mount["destination"]) / backup.relative_to(backup_mount_root)
    ).as_posix()
    if value["backup_server_path"] != expected_server_backup:
        raise GasCityOpsError("native backup server path is not derived from its host mount")
    manifest_path = _canonical_path(
        Path(str(value["backup_manifest_path"])),
        must_exist=True,
        label="native backup manifest",
    )
    expected_manifest_path = backup.parent / f"{backup.name}{NATIVE_BACKUP_MANIFEST_SUFFIX}"
    if manifest_path != expected_manifest_path:
        raise GasCityOpsError("native backup manifest path is not bound to the backup")
    manifest_bytes = _regular_file_bytes(manifest_path, label="native backup manifest")
    if (
        stat.S_IMODE(manifest_path.stat().st_mode) & 0o077
        or _sha256(manifest_bytes) != value["backup_manifest_sha256"]
    ):
        raise GasCityOpsError("native backup manifest is not private or has drifted")
    manifest = _load_json_bytes(manifest_bytes, label="native backup manifest")
    entries = _validate_file_manifest(
        manifest,
        expected_kind="dolt-native-backup-file-manifest",
        label="native backup",
    )
    current_entries = _file_tree_manifest(backup, label="Dolt native backup")
    if entries != current_entries:
        raise GasCityOpsError("native backup bytes or metadata drifted after the drill")
    return dict(value)


def _validate_recovery_evidence(
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    lock: Mapping[str, Any],
) -> None:
    validate_native_restore_evidence(
        lock_root / "runtime-lock.json",
        value,
        expected_source_endpoint=DoltEndpoint(
            AEGIS_BEADS_INIT_HOST,
            AEGIS_BEADS_INIT_PORT,
            AEGIS_RECOVERY_USER,
            AEGIS_BEADS_INIT_DATABASE,
        ),
        expected_source_container="gas-city-aegis-dolt",
        expected_source_image_id=lock["images"]["dolt_server"]["image_id"],
        expected_source_relay_image_id=lock["images"]["egress_proxy"]["image_id"],
    )


def _provider_session_artifact(
    lock_root: Path,
    path: Path,
    *,
    provider: str,
    kind: str,
) -> tuple[str, bytes, tuple[str, str]]:
    relative = _relative_evidence_path(path, lock_root, label=f"{provider} {kind}")
    parts = Path(relative).parts
    if kind == "supervisor receipt":
        expected_prefix = ("runtime", "state", "model-receipts", "rig-aegis")
        if (
            len(parts) != 8
            or parts[:4] != expected_prefix
            or parts[5] != provider
            or parts[7] != "model-receipt.json"
        ):
            raise GasCityOpsError(
                f"{provider} supervisor receipt is outside its exact Aegis session scope"
            )
    elif kind == "transcript":
        expected_prefix = ("runtime", "state", "provider-sessions", "rig-aegis")
        expected_overlay = {"claude": "projects", "codex": "sessions"}[provider]
        if (
            len(parts) < 9
            or parts[:4] != expected_prefix
            or parts[5] != provider
            or parts[7] != expected_overlay
            or not parts[-1].endswith(".jsonl")
        ):
            raise GasCityOpsError(
                f"{provider} transcript is outside its exact Aegis session overlay"
            )
    else:  # pragma: no cover - internal callers use two fixed kinds.
        raise GasCityOpsError(f"unsupported provider artifact kind: {kind}")
    for field, value in (("agent", parts[4]), ("session", parts[6])):
        if (
            SAFE_NAME_RE.fullmatch(value) is None
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value) is None
        ):
            raise GasCityOpsError(f"{provider} {field} identity is unsafe")
    artifact = lock_root / relative
    content = _regular_file_bytes(artifact, label=f"{provider} {kind}")
    if stat.S_IMODE(artifact.stat().st_mode) & 0o077:
        raise GasCityOpsError(f"{provider} {kind} must be owner-only")
    return relative, content, (parts[4], parts[6])


def _verified_provider_session(
    lock_root: Path,
    lock: Mapping[str, Any],
    *,
    provider: str,
    supervisor_receipt_path: Path,
    transcript_path: Path,
) -> dict[str, Any]:
    expected_model, expected_effort = {
        "claude": ("claude-fable-5", None),
        "codex": ("gpt-5.6-sol", "xhigh"),
    }[provider]
    receipt_relative, receipt_content, receipt_identity = _provider_session_artifact(
        lock_root,
        supervisor_receipt_path,
        provider=provider,
        kind="supervisor receipt",
    )
    transcript_relative, transcript_content, transcript_identity = _provider_session_artifact(
        lock_root,
        transcript_path,
        provider=provider,
        kind="transcript",
    )
    if receipt_identity != transcript_identity:
        raise GasCityOpsError(f"{provider} receipt and transcript name different sessions")
    receipt = _load_json_bytes(receipt_content, label=f"{provider} supervisor receipt")
    receipt_fields = {
        "schema_version",
        "status",
        "provider",
        "expected_model",
        "expected_effort",
        "observed_model",
        "observed_effort",
        "transcript",
        "transcript_sha256",
        "provider_exit_code",
    }
    transcript_sha = _sha256(transcript_content)
    if (
        type(receipt) is not dict
        or set(receipt) != receipt_fields
        or receipt.get("schema_version") != 1
        or receipt.get("status") != "verified"
        or receipt.get("provider") != provider
        or receipt.get("expected_model") != expected_model
        or receipt.get("expected_effort") != expected_effort
        or receipt.get("observed_model") != expected_model
        or receipt.get("observed_effort") != expected_effort
        or type(receipt.get("transcript")) is not str
        or not receipt["transcript"]
        or receipt.get("transcript_sha256") != transcript_sha
        or receipt.get("provider_exit_code") != 0
    ):
        raise GasCityOpsError(f"{provider} supervisor receipt is not a successful model run")
    transcript_receipt = verify_model_transcript(
        provider,
        lock_root / transcript_relative,
        expected_model=expected_model,
        expected_effort=expected_effort,
    )
    locked_record = lock["providers"][provider]
    locked_relative = str(locked_record["receipt_path"])
    locked_path = lock_root / locked_relative
    locked_content = _regular_file_bytes(locked_path, label=f"{provider} locked model receipt")
    if stat.S_IMODE(locked_path.stat().st_mode) & 0o077:
        raise GasCityOpsError(f"{provider} locked model receipt must be owner-only")
    locked_receipt = _load_json_bytes(locked_content, label=f"{provider} locked model receipt")
    if (
        type(locked_receipt) is not dict
        or locked_receipt.get("provider") != provider
        or locked_receipt.get("observed_model") != expected_model
        or locked_receipt.get("observed_effort", expected_effort) != expected_effort
        or locked_receipt.get("transcript_sha256") != transcript_sha
    ):
        raise GasCityOpsError(f"{provider} locked receipt is not bound to the session transcript")
    return {
        "provider": provider,
        "model": expected_model,
        "reasoning_effort": expected_effort,
        "agent": receipt_identity[0],
        "session": receipt_identity[1],
        "supervisor_receipt": {
            "path": receipt_relative,
            "sha256": _sha256(receipt_content),
        },
        "transcript": {
            "path": transcript_relative,
            "sha256": transcript_sha,
            "observations": transcript_receipt["observations"],
        },
        "locked_model_receipt": {
            "path": locked_relative,
            "sha256": _sha256(locked_content),
        },
        "provider_exit_code": 0,
    }


def capture_provider_evidence(
    lock_path: Path,
    *,
    claude_supervisor_receipt: Path,
    claude_transcript: Path,
    codex_supervisor_receipt: Path,
    codex_transcript: Path,
    output_path: Path,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Derive provider promotion evidence from real session artifacts."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(path)
    locked_digests = _verified_provider_receipts(path, lock)
    binding, _ = _live_authority_binding(path.parent)
    sessions = {
        "claude": _verified_provider_session(
            path.parent,
            lock,
            provider="claude",
            supervisor_receipt_path=claude_supervisor_receipt,
            transcript_path=claude_transcript,
        ),
        "codex": _verified_provider_session(
            path.parent,
            lock,
            provider="codex",
            supervisor_receipt_path=codex_supervisor_receipt,
            transcript_path=codex_transcript,
        ),
    }
    if sessions["claude"]["session"] == sessions["codex"]["session"]:
        raise GasCityOpsError("Claude and Codex provider canaries require distinct sessions")
    if any(
        sessions[provider]["locked_model_receipt"]["sha256"] != locked_digests[provider]
        for provider in sessions
    ):
        raise GasCityOpsError("provider session evidence disagrees with the locked receipts")
    value = {
        "schema_version": 2,
        "kind": "provider-model-canary",
        "status": "pass",
        "captured_at": _format_utc(clock()),
        "authority_receipt_sha256": binding["receipt_sha256"],
        "sessions": sessions,
    }
    destination = _safe_evidence_output(path.parent, output_path, label="provider evidence output")
    _, digest = _write_append_only_json(destination, value)
    return {**value, "evidence_path": destination.as_posix(), "evidence_sha256": digest}


def _require_private_tree(root: Path, *, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise GasCityOpsError(f"{label} must be a real directory")
    for path in (root, *root.rglob("*")):
        if path.is_symlink():
            raise GasCityOpsError(f"{label} must not contain symlinks: {path}")
        metadata = path.stat()
        if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise GasCityOpsError(f"{label} must be owner-only: {path}")


def _validated_obsidian_manifest(
    vault: Path,
    *,
    expected_bd_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    from aegis_foundation import obsidian_vault

    _require_private_tree(vault, label="Obsidian build")
    manifest_path = vault / obsidian_vault.MANIFEST_NAME
    manifest_bytes = _regular_file_bytes(manifest_path, label="Obsidian build manifest")
    manifest = _load_json_bytes(manifest_bytes, label="Obsidian build manifest")
    check = obsidian_vault.check_vault(vault)
    if (
        type(manifest) is not dict
        or manifest.get("schema_version") != obsidian_vault.SCHEMA_VERSION
        or manifest.get("generator") != obsidian_vault.GENERATOR
        or manifest.get("managed_root") is not True
        or manifest.get("task_authority") != "beads/dolt"
        or manifest.get("task_export_command") != " ".join(obsidian_vault.BEADS_EXPORT_COMMAND)
        or manifest.get("task_bd_binary_sha256") != expected_bd_sha256
        or type(manifest.get("task_bd_version")) is not str
        or re.fullmatch(
            rf"bd version {re.escape(taskmaster_beads.TARGET_BEADS_VERSION)} \([0-9a-f]+\)",
            manifest["task_bd_version"],
        )
        is None
        or type(manifest.get("task_dolt_main_head")) is not str
        or re.fullmatch(r"[0-9a-v]{20,128}", manifest["task_dolt_main_head"].lower()) is None
        or type(manifest.get("source_digest")) is not str
        or SHA256_RE.fullmatch(manifest["source_digest"]) is None
        or type(manifest.get("files")) is not dict
        or not manifest["files"]
        or check.get("ok") is not True
        or check.get("fresh") is not True
        or check.get("source_digest") != manifest["source_digest"]
    ):
        raise GasCityOpsError("Obsidian build does not prove a valid Beads projection")
    return manifest_bytes, manifest


def capture_obsidian_evidence(
    lock_path: Path,
    *,
    target_repo: Path,
    first_vault: Path,
    second_vault: Path,
    output_path: Path,
    source_root: Path,
    python_binary: Path = Path(sys.executable),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Build the live Beads-backed Obsidian vault twice and bind both manifests."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(path)
    binding, _, _, authority_target = _full_live_authority_state(path.parent)
    repo = _require_aegis_migration_target(
        target_repo,
        authority_target,
        label="Obsidian target repository",
    )
    source = _canonical_path(source_root, must_exist=True, label="Aegis source root")
    python = _canonical_path(python_binary, must_exist=True, label="Python binary")
    bd = path.parent / "bin" / "bd"
    if (
        _sha256(_regular_file_bytes(bd, label="Obsidian Beads binary"))
        != lock["tools"]["bd"]["binary_sha256"]
    ):
        raise GasCityOpsError("Obsidian build requires the lock-pinned city/bin/bd")
    builds = [
        _canonical_path(first_vault, must_exist=False, label="first Obsidian vault"),
        _canonical_path(second_vault, must_exist=False, label="second Obsidian vault"),
    ]
    if builds[0] == builds[1] or any(
        not _is_within(vault, path.parent / "runtime" / "evidence" / "obsidian") for vault in builds
    ):
        raise GasCityOpsError("Obsidian double builds require distinct evidence directories")
    if any(vault.exists() or vault.is_symlink() for vault in builds):
        raise GasCityOpsError("Obsidian double-build outputs must be new append-only directories")
    for vault in builds:
        _make_private_parents(vault.parent)
    env = dict(os.environ if environment is None else environment)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    build_results: list[dict[str, Any]] = []
    for number, vault in enumerate(builds, start=1):
        command = (
            python.as_posix(),
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            source.as_posix(),
            "vault",
            "build",
            "--target-dir",
            repo.as_posix(),
            "--output",
            vault.as_posix(),
            "--bd-executable",
            bd.as_posix(),
            "--expected-bd-sha256",
            lock["tools"]["bd"]["binary_sha256"],
        )
        result = _checked(command, cwd=source, environment=env, runner=runner)
        build_result = _strict_json_object(result.stdout, label=f"Obsidian build {number} result")
        if (
            build_result.get("status") != "built"
            or build_result.get("changed") is not True
            or build_result.get("output") != vault.as_posix()
            or build_result.get("authority") != "derived-read-only"
        ):
            raise GasCityOpsError(f"Obsidian build {number} was not a new real build")
        build_results.append(build_result)
    validated = [
        _validated_obsidian_manifest(
            vault,
            expected_bd_sha256=lock["tools"]["bd"]["binary_sha256"],
        )
        for vault in builds
    ]
    first_bytes, first_manifest = validated[0]
    second_bytes, second_manifest = validated[1]
    if first_bytes != second_bytes or first_manifest != second_manifest:
        raise GasCityOpsError("two actual Obsidian builds were not byte-for-byte deterministic")
    if any(
        result.get("source_digest") != first_manifest["source_digest"] for result in build_results
    ):
        raise GasCityOpsError("Obsidian build output disagrees with its ownership manifest")
    build_records = []
    for vault, manifest_bytes in zip(builds, (first_bytes, second_bytes)):
        manifest_path = vault / ".aegis-vault.json"
        build_records.append(
            {
                "directory": vault.relative_to(path.parent).as_posix(),
                "manifest_path": manifest_path.relative_to(path.parent).as_posix(),
                "manifest_sha256": _sha256(manifest_bytes),
            }
        )
    value = {
        "schema_version": OBSIDIAN_EVIDENCE_SCHEMA_VERSION,
        "kind": "obsidian-deterministic-projection",
        "status": "pass",
        "captured_at": _format_utc(clock()),
        "authority_receipt_sha256": binding["receipt_sha256"],
        "authority_target": authority_target,
        "source_digest": first_manifest["source_digest"],
        "dolt_main_head": first_manifest["task_dolt_main_head"],
        "bd_binary_sha256": lock["tools"]["bd"]["binary_sha256"],
        "builds": build_records,
    }
    destination = _safe_evidence_output(path.parent, output_path, label="Obsidian evidence output")
    _, digest = _write_append_only_json(destination, value)
    return {**value, "evidence_path": destination.as_posix(), "evidence_sha256": digest}


def _canary_run_id() -> str:
    return secrets.token_hex(16)


def _github_environment(
    environment: Mapping[str, str] | None,
) -> tuple[dict[str, str], str]:
    env = dict(os.environ if environment is None else environment)
    token = env.get("GH_TOKEN", "")
    if not 32 <= len(token) <= 128 or any(
        character.isspace() or not 33 <= ord(character) <= 126 for character in token
    ):
        raise GasCityOpsError("GH_TOKEN must contain one private 32-128 character token")
    return env, token


def _command_stdout(
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    runner: Runner,
    secrets_to_redact: Sequence[str] = (),
    label: str,
    allow_empty: bool = False,
    include_stderr: bool = False,
) -> bytes:
    result = _checked(
        argv,
        cwd=cwd,
        environment=environment,
        runner=runner,
        secrets=secrets_to_redact,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if any(secret and (secret in stdout or secret in stderr) for secret in secrets_to_redact):
        raise GasCityOpsError(f"{label} exposed secret material in command output")
    output = stdout + (stderr if include_stderr else "")
    try:
        content = output.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - CompletedProcess[str] is UTF-8 text.
        raise GasCityOpsError(f"{label} did not return UTF-8 text") from exc
    if len(content) > 4 * 1024 * 1024:
        raise GasCityOpsError(f"{label} output exceeds the 4 MiB evidence limit")
    if not allow_empty and not content.strip():
        raise GasCityOpsError(f"{label} returned empty output")
    return content


def _json_object_output(content: bytes, *, label: str) -> dict[str, Any]:
    value = _load_json_bytes(content, label=label)
    if type(value) is not dict:
        raise GasCityOpsError(f"{label} must contain exactly one JSON object")
    return value


def _json_array_output(content: bytes, *, label: str) -> list[Any]:
    value = _load_json_bytes(content, label=label)
    if type(value) is not list:
        raise GasCityOpsError(f"{label} must contain exactly one JSON array")
    return value


def _one_line_output(content: bytes, *, label: str) -> str:
    try:
        value = content.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise GasCityOpsError(f"{label} is not valid UTF-8") from exc
    if not value or "\n" in value or "\r" in value:
        raise GasCityOpsError(f"{label} must contain exactly one non-empty line")
    return value


def _parse_github_origin(origin: str) -> str:
    patterns = (
        r"git@github\.com:([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?\Z",
        r"ssh://git@github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?\Z",
        r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?\Z",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, origin)
        if match is not None:
            return match.group(1)
    raise GasCityOpsError("origin must be an SSH or HTTPS github.com owner/repository URL")


def _git_common_directory(repo: Path, raw: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo / candidate
    common = _canonical_path(candidate, must_exist=True, label="Git common directory")
    if not common.is_dir() or common.is_symlink():
        raise GasCityOpsError("Git common directory must be a real directory")
    return common


def _tool_binding(path: Path, *, label: str) -> dict[str, str]:
    content = _regular_file_bytes(path, label=label)
    return {"path": path.as_posix(), "sha256": _sha256(content)}


def _git_repository_probe(
    git: Path,
    repo: Path,
    *,
    environment: Mapping[str, str],
    runner: Runner,
    artifact_prefix: str,
) -> tuple[dict[str, str], dict[str, bytes]]:
    commands = {
        "head": ("rev-parse", "HEAD"),
        "branch": ("symbolic-ref", "--quiet", "--short", "HEAD"),
        "status": ("status", "--porcelain=v1", "--untracked-files=all"),
        "origin": ("remote", "get-url", "origin"),
        "common_git_dir": ("rev-parse", "--path-format=absolute", "--git-common-dir"),
    }
    raw: dict[str, bytes] = {}
    for name, arguments in commands.items():
        raw[name] = _command_stdout(
            (git.as_posix(), "-C", repo.as_posix(), *arguments),
            cwd=repo,
            environment=environment,
            runner=runner,
            label=f"{artifact_prefix} Git {name}",
            allow_empty=name == "status",
        )
    head = _one_line_output(raw["head"], label=f"{artifact_prefix} Git head")
    branch = _one_line_output(raw["branch"], label=f"{artifact_prefix} Git branch")
    origin = _one_line_output(raw["origin"], label=f"{artifact_prefix} Git origin")
    common_raw = _one_line_output(
        raw["common_git_dir"], label=f"{artifact_prefix} Git common directory"
    )
    if GIT_OBJECT_RE.fullmatch(head) is None or GIT_REF_RE.fullmatch(branch) is None:
        raise GasCityOpsError(f"{artifact_prefix} Git identity is invalid")
    common = _git_common_directory(repo, common_raw)
    return (
        {
            "path": repo.as_posix(),
            "head": head,
            "branch": branch,
            "origin": origin,
            "common_git_dir": common.as_posix(),
            "status_sha256": _sha256(raw["status"]),
        },
        raw,
    )


def _beads_record(export: bytes, *, bead_id: str, label: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for number, line in enumerate(export.splitlines(), start=1):
        if not line.strip():
            continue
        value = _load_json_bytes(line, label=f"{label} line {number}")
        if type(value) is not dict:
            raise GasCityOpsError(f"{label} line {number} must contain one JSON object")
        if value.get("id") == bead_id:
            matches.append(value)
    if len(matches) != 1:
        raise GasCityOpsError(f"{label} must contain exactly one authoritative {bead_id} record")
    return matches[0]


def _bead_binding(record: Mapping[str, Any], *, expected_status: str) -> dict[str, str]:
    bead_id = record.get("id")
    status_value = record.get("status")
    assignee = record.get("assignee")
    if (
        type(bead_id) is not str
        or re.fullmatch(r"ags-[A-Za-z0-9._-]{1,128}", bead_id) is None
        or status_value != expected_status
        or type(assignee) is not str
        or not assignee.strip()
        or len(assignee) > 128
    ):
        raise GasCityOpsError(
            f"authoritative Bead must be {expected_status} with a non-empty assignee"
        )
    canonical = (json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n").encode()
    return {
        "id": bead_id,
        "status": status_value,
        "assignee": assignee,
        "record_sha256": _sha256(canonical),
    }


def _canary_bead_binding(
    record: Mapping[str, Any],
    *,
    expected_status: str,
    expected_branch: str | None = None,
    expected_worktree: str | None = None,
    expected_target: str | None = None,
    expected_pr_url: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = _bead_binding(record, expected_status=expected_status)
    metadata = record.get("metadata")
    branch = metadata.get("branch") if type(metadata) is dict else None
    worktree_raw = metadata.get("work_dir") if type(metadata) is dict else None
    target = metadata.get("target") if type(metadata) is dict else None
    pr_url = metadata.get("pr_url") if type(metadata) is dict else None
    required_branch = expected_branch or f"polecat/{result['id']}"
    if (
        type(metadata) is not dict
        or branch != required_branch
        or type(worktree_raw) is not str
        or not Path(worktree_raw).is_absolute()
        or (expected_worktree is not None and worktree_raw != expected_worktree)
        or (expected_target is not None and target != expected_target)
        or (expected_pr_url is not None and pr_url != expected_pr_url)
    ):
        raise GasCityOpsError(
            "authoritative Bead metadata does not bind the exact polecat worktree and delivery"
        )
    if expected_worktree is None:
        worktree = _canonical_path(
            Path(worktree_raw), must_exist=True, label="authoritative Bead worktree"
        )
        if not worktree.is_dir() or worktree.is_symlink():
            raise GasCityOpsError("authoritative Bead worktree must be a real directory")
        worktree_value = worktree.as_posix()
    else:
        worktree_value = worktree_raw
    result.update(
        {
            "branch": branch,
            "worktree": worktree_value,
            "target": target,
            "pr_url": pr_url,
        }
    )
    return result


def _github_repository_binding(
    value: Mapping[str, Any], *, origin_repository: str
) -> dict[str, str]:
    default = value.get("defaultBranchRef")
    name = value.get("nameWithOwner")
    url = value.get("url")
    permission = value.get("viewerPermission")
    if (
        type(default) is not dict
        or set(default) != {"name"}
        or type(default.get("name")) is not str
        or GIT_REF_RE.fullmatch(default["name"]) is None
        or type(name) is not str
        or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name) is None
        or name.casefold() != origin_repository.casefold()
        or url != f"https://github.com/{name}"
        or permission not in {"WRITE", "MAINTAIN", "ADMIN"}
    ):
        raise GasCityOpsError("GitHub repository evidence does not prove scoped write access")
    return {
        "name_with_owner": name,
        "url": url,
        "viewer_permission": permission,
        "default_branch": default["name"],
    }


def _github_ref_oid(value: Mapping[str, Any], *, expected_ref: str) -> str:
    object_value = value.get("object")
    if (
        value.get("ref") != f"refs/heads/{expected_ref}"
        or type(object_value) is not dict
        or type(object_value.get("sha")) is not str
        or GIT_OBJECT_RE.fullmatch(object_value["sha"]) is None
    ):
        raise GasCityOpsError("GitHub ref evidence is not an exact branch commit")
    return object_value["sha"]


def _github_pr_binding(
    value: Mapping[str, Any],
    *,
    repository: str,
    expected_branch: str,
    expected_head: str,
    expected_base: str,
) -> dict[str, Any]:
    merge = value.get("mergeCommit")
    merged_by = value.get("mergedBy")
    number = value.get("number")
    url = value.get("url")
    if (
        type(number) is not int
        or number < 1
        or url != f"https://github.com/{repository}/pull/{number}"
        or value.get("state") != "MERGED"
        or value.get("isDraft") is not False
        or value.get("headRefName") != expected_branch
        or value.get("headRefOid") != expected_head
        or value.get("baseRefName") != expected_base
        or type(merge) is not dict
        or set(merge) != {"oid"}
        or type(merge.get("oid")) is not str
        or GIT_OBJECT_RE.fullmatch(merge["oid"]) is None
        or type(value.get("mergedAt")) is not str
        or type(merged_by) is not dict
        or set(merged_by) != {"login"}
        or type(merged_by.get("login")) is not str
        or not merged_by["login"]
    ):
        raise GasCityOpsError("GitHub PR evidence is not the exact merged canary branch")
    _utc_timestamp(value["mergedAt"], label="GitHub PR mergedAt")
    return {
        "number": number,
        "url": url,
        "state": "MERGED",
        "is_draft": False,
        "head_ref": expected_branch,
        "head_oid": expected_head,
        "base_ref": expected_base,
        "merge_commit": merge["oid"],
        "merged_at": value["mergedAt"],
        "merged_by": merged_by["login"],
    }


def _github_checks_binding(values: Sequence[Any]) -> list[dict[str, str]]:
    if not values:
        raise GasCityOpsError("GitHub PR must have at least one reported required check")
    checks: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    for value in values:
        if type(value) is not dict or set(value) != {
            "name",
            "state",
            "bucket",
            "link",
            "workflow",
        }:
            raise GasCityOpsError("GitHub PR check output has an unexpected shape")
        if any(type(value[field]) is not str for field in value):
            raise GasCityOpsError("GitHub PR check fields must be strings")
        identity = (value["workflow"], value["name"])
        if (
            not value["name"]
            or identity in identities
            or value["bucket"].casefold() != "pass"
            or value["state"].upper() != "SUCCESS"
        ):
            raise GasCityOpsError("every unique GitHub PR check must have succeeded")
        identities.add(identity)
        checks.append({field: value[field] for field in sorted(value)})
    return sorted(checks, key=lambda item: (item["workflow"], item["name"]))


def _write_canary_artifact(
    run_root: Path,
    lock_root: Path,
    name: str,
    content: bytes,
) -> dict[str, str]:
    digest = write_private_evidence_bytes(run_root, f"artifacts/{name}", content)
    path = run_root / "artifacts" / name
    return {"path": path.relative_to(lock_root).as_posix(), "sha256": digest}


def _load_canary_artifact(
    lock_root: Path,
    record: Any,
    *,
    run_id: str,
    label: str,
) -> bytes:
    if (
        type(record) is not dict
        or set(record) != {"path", "sha256"}
        or type(record.get("path")) is not str
        or type(record.get("sha256")) is not str
        or SHA256_RE.fullmatch(record["sha256"]) is None
    ):
        raise GasCityOpsError(f"{label} artifact record is invalid")
    relative = Path(record["path"])
    expected_prefix = Path("runtime") / "evidence" / "canary-runs" / run_id / "artifacts"
    if relative.is_absolute() or ".." in relative.parts or relative.parent != expected_prefix:
        raise GasCityOpsError(f"{label} artifact is outside its exact canary run")
    path = _canonical_path(lock_root / relative, must_exist=True, label=label)
    if path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GasCityOpsError(f"{label} artifact must be owner-only and non-symlink")
    content = _regular_file_bytes(path, label=label)
    if _sha256(content) != record["sha256"]:
        raise GasCityOpsError(f"{label} artifact digest mismatch")
    return content


def _validated_canary_intent(
    lock_root: Path,
    intent_path: Path,
    *,
    now: dt.datetime | None = None,
) -> tuple[dict[str, Any], bytes]:
    path = _canonical_path(intent_path, must_exist=True, label="controlled canary intent")
    content = _regular_file_bytes(path, label="controlled canary intent")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GasCityOpsError("controlled canary intent must be owner-only")
    value = _load_json_bytes(content, label="controlled canary intent")
    run_id = value.get("run_id") if type(value) is dict else None
    expected_path = lock_root / "runtime" / "evidence" / "canary-runs" / str(run_id) / "intent.json"
    if (
        type(value) is not dict
        or set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "created_at",
            "run_id",
            "rig",
            "authority",
            "authority_history",
            "authority_target",
            "tools",
            "repository",
            "primary",
            "bead",
            "expected_branch",
            "artifacts",
        }
        or value.get("schema_version") != CANARY_RUN_SCHEMA
        or value.get("kind") != "aegis-controlled-canary-intent"
        or value.get("status") != "ready"
        or type(run_id) is not str
        or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or path != expected_path
        or value.get("rig") != "aegis"
    ):
        raise GasCityOpsError("controlled canary intent identity or path is invalid")
    created = _utc_timestamp(value["created_at"], label="canary intent created_at")
    if now is not None:
        current = now
        if current.tzinfo is None or current.utcoffset() != dt.timedelta(0):
            raise GasCityOpsError("clock returned a non-UTC time")
        if current < created or current - created > CANARY_RUN_MAX_AGE:
            raise GasCityOpsError("controlled canary intent is stale")
    binding, _, history, authority_target = _full_live_authority_state(lock_root)
    if (
        value.get("authority") != binding
        or value.get("authority_history") != history
        or value.get("authority_target") != authority_target
    ):
        raise GasCityOpsError("controlled canary intent is not bound to live Aegis authority")
    repository = value.get("repository")
    tools = value.get("tools")
    primary = value.get("primary")
    bead = value.get("bead")
    artifacts = value.get("artifacts")
    if (
        type(tools) is not dict
        or set(tools) != {"git", "gh", "bd"}
        or any(
            type(record) is not dict
            or set(record) != {"path", "sha256"}
            or type(record.get("path")) is not str
            or type(record.get("sha256")) is not str
            or SHA256_RE.fullmatch(record["sha256"]) is None
            for record in tools.values()
        )
        or type(repository) is not dict
        or set(repository)
        != {
            "name_with_owner",
            "url",
            "viewer_permission",
            "origin",
            "default_branch",
            "remote_base_oid",
        }
        or type(primary) is not dict
        or set(primary) != {"path", "head", "branch", "origin", "common_git_dir", "status_sha256"}
        or any(
            type(primary.get(field)) is not str or not primary[field]
            for field in ("path", "head", "branch", "origin", "common_git_dir", "status_sha256")
        )
        or type(bead) is not dict
        or set(bead)
        != {
            "id",
            "status",
            "assignee",
            "record_sha256",
            "branch",
            "worktree",
            "target",
            "pr_url",
        }
        or type(artifacts) is not dict
        or set(artifacts)
        != {
            "primary_head",
            "primary_branch",
            "primary_status",
            "primary_origin",
            "primary_common_git_dir",
            "beads_start",
            "github_auth_start",
            "github_repository_start",
            "github_base_ref_start",
            "git_version_start",
            "gh_version_start",
        }
        or value.get("expected_branch") != f"polecat/{bead.get('id')}"
        or primary.get("head") != repository.get("remote_base_oid")
        or primary.get("branch") != repository.get("default_branch")
        or primary.get("origin") != repository.get("origin")
        or bead.get("status") != "in_progress"
        or type(bead.get("assignee")) is not str
        or CANARY_POLECAT_ASSIGNEE_RE.fullmatch(bead["assignee"]) is None
        or bead.get("branch") != value.get("expected_branch")
        or bead.get("target") not in {None, repository.get("default_branch")}
        or bead.get("pr_url") is not None
    ):
        raise GasCityOpsError("controlled canary intent bindings are incomplete")
    _require_aegis_migration_target(
        Path(primary["path"]),
        authority_target,
        label="controlled canary primary repository",
    )
    for name, record in tools.items():
        tool_path = _canonical_path(Path(record["path"]), must_exist=True, label=f"{name} tool")
        if _tool_binding(tool_path, label=f"{name} tool") != record:
            raise GasCityOpsError(f"controlled canary {name} tool drifted")
    loaded = {
        name: _load_canary_artifact(lock_root, record, run_id=run_id, label=f"canary intent {name}")
        for name, record in artifacts.items()
    }
    if (
        _one_line_output(loaded["primary_head"], label="intent primary head") != primary["head"]
        or _one_line_output(loaded["primary_branch"], label="intent primary branch")
        != primary["branch"]
        or _sha256(loaded["primary_status"]) != primary["status_sha256"]
        or _one_line_output(loaded["primary_origin"], label="intent primary origin")
        != primary["origin"]
        or _git_common_directory(
            Path(primary["path"]),
            _one_line_output(
                loaded["primary_common_git_dir"], label="intent primary common git directory"
            ),
        ).as_posix()
        != primary["common_git_dir"]
    ):
        raise GasCityOpsError("controlled canary primary artifacts drifted")
    start_record = _beads_record(
        loaded["beads_start"], bead_id=bead["id"], label="canary start Beads export"
    )
    if (
        _canary_bead_binding(
            start_record,
            expected_status="in_progress",
            expected_branch=value["expected_branch"],
            expected_worktree=bead["worktree"],
        )
        != bead
    ):
        raise GasCityOpsError("controlled canary start Bead drifted")
    repository_raw = _json_object_output(
        loaded["github_repository_start"], label="canary start GitHub repository"
    )
    observed_repository = _github_repository_binding(
        repository_raw,
        origin_repository=_parse_github_origin(primary["origin"]),
    )
    base_raw = _json_object_output(
        loaded["github_base_ref_start"], label="canary start GitHub base ref"
    )
    if (
        observed_repository != {key: repository[key] for key in observed_repository}
        or _github_ref_oid(base_raw, expected_ref=repository["default_branch"])
        != repository["remote_base_oid"]
        or not loaded["github_auth_start"].strip()
        or not loaded["git_version_start"].startswith(b"git version ")
        or not loaded["gh_version_start"].startswith(b"gh version ")
    ):
        raise GasCityOpsError("controlled canary GitHub start artifacts drifted")
    return value, content


def start_controlled_canary(
    lock_path: Path,
    *,
    target_repo: Path,
    bead_id: str,
    git_binary: Path = Path("/usr/bin/git"),
    gh_binary: Path = Path("/usr/bin/gh"),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
    nonce_factory: Callable[[], str] = _canary_run_id,
) -> dict[str, Any]:
    """Derive a run-bound Aegis canary intent from GitHub, Git, and Beads state."""

    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_value = load_runtime_lock(lock)
    _verified_provider_receipts(lock, lock_value)
    binding, _, history, authority_target = _full_live_authority_state(lock.parent)
    repo = _require_aegis_migration_target(
        target_repo,
        authority_target,
        label="Aegis canary repository",
    )
    git = _canonical_path(git_binary, must_exist=True, label="Git binary")
    gh = _canonical_path(gh_binary, must_exist=True, label="GitHub CLI binary")
    if not git.is_file() or not gh.is_file():
        raise GasCityOpsError("Git and GitHub CLI paths must be files")
    bd = lock.parent / "bin" / "bd"
    if (
        _sha256(_regular_file_bytes(bd, label="controlled canary Beads binary"))
        != lock_value["tools"]["bd"]["binary_sha256"]
    ):
        raise GasCityOpsError("controlled canary requires the lock-pinned city/bin/bd")
    if re.fullmatch(r"ags-[A-Za-z0-9._-]{1,128}", bead_id) is None:
        raise GasCityOpsError("controlled canary requires one exact ags-* Bead ID")
    env, token = _github_environment(environment)
    non_github_env = dict(env)
    non_github_env.pop("GH_TOKEN", None)
    git_version_raw = _command_stdout(
        (git.as_posix(), "--version"),
        cwd=repo,
        environment=non_github_env,
        runner=runner,
        label="Git version",
    )
    gh_version_raw = _command_stdout(
        (gh.as_posix(), "--version"),
        cwd=repo,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub CLI version",
    )
    primary, primary_raw = _git_repository_probe(
        git,
        repo,
        environment=non_github_env,
        runner=runner,
        artifact_prefix="primary",
    )
    origin_repository = _parse_github_origin(primary["origin"])
    auth_raw = _command_stdout(
        (gh.as_posix(), "auth", "status", "--hostname", "github.com"),
        cwd=repo,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub authentication",
        include_stderr=True,
    )
    repository_raw = _command_stdout(
        (
            gh.as_posix(),
            "repo",
            "view",
            origin_repository,
            "--json",
            "nameWithOwner,url,viewerPermission,defaultBranchRef",
        ),
        cwd=repo,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub repository",
    )
    repository = _github_repository_binding(
        _json_object_output(repository_raw, label="GitHub repository"),
        origin_repository=origin_repository,
    )
    base_raw = _command_stdout(
        (
            gh.as_posix(),
            "api",
            f"repos/{repository['name_with_owner']}/git/ref/heads/{repository['default_branch']}",
        ),
        cwd=repo,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub base ref",
    )
    base_oid = _github_ref_oid(
        _json_object_output(base_raw, label="GitHub base ref"),
        expected_ref=repository["default_branch"],
    )
    if primary["branch"] != repository["default_branch"] or primary["head"] != base_oid:
        raise GasCityOpsError(
            "controlled canary must start from the local default branch at the exact remote head"
        )
    beads_raw = _command_stdout(
        (bd.as_posix(), "--readonly", "-C", repo.as_posix(), "export", "--all"),
        cwd=repo,
        environment=non_github_env,
        runner=runner,
        label="authoritative Beads start export",
    )
    bead = _canary_bead_binding(
        _beads_record(beads_raw, bead_id=bead_id, label="authoritative Beads start export"),
        expected_status="in_progress",
        expected_branch=f"polecat/{bead_id}",
    )
    if CANARY_POLECAT_ASSIGNEE_RE.fullmatch(bead["assignee"]) is None:
        raise GasCityOpsError(
            "controlled canary must start under an exact Aegis Gas Town polecat owner"
        )
    if bead["target"] not in {None, repository["default_branch"]} or bead["pr_url"] is not None:
        raise GasCityOpsError("controlled canary Bead has stale target or PR metadata")
    run_id = nonce_factory()
    if type(run_id) is not str or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
        raise GasCityOpsError("controlled canary nonce factory returned an invalid run ID")
    run_root = create_private_evidence_directory(
        lock.parent / "runtime" / "evidence" / "canary-runs" / run_id
    )
    contents = {
        "primary_head": primary_raw["head"],
        "primary_branch": primary_raw["branch"],
        "primary_status": primary_raw["status"],
        "primary_origin": primary_raw["origin"],
        "primary_common_git_dir": primary_raw["common_git_dir"],
        "beads_start": beads_raw,
        "github_auth_start": auth_raw,
        "github_repository_start": repository_raw,
        "github_base_ref_start": base_raw,
        "git_version_start": git_version_raw,
        "gh_version_start": gh_version_raw,
    }
    artifacts = {
        name: _write_canary_artifact(
            run_root, lock.parent, f"{name.replace('_', '-')}.txt", content
        )
        for name, content in contents.items()
    }
    created_at = _format_utc(clock())
    value = {
        "schema_version": CANARY_RUN_SCHEMA,
        "kind": "aegis-controlled-canary-intent",
        "status": "ready",
        "created_at": created_at,
        "run_id": run_id,
        "rig": "aegis",
        "authority": binding,
        "authority_history": history,
        "authority_target": authority_target,
        "tools": {
            "git": _tool_binding(git, label="Git binary"),
            "gh": _tool_binding(gh, label="GitHub CLI binary"),
            "bd": _tool_binding(bd, label="controlled canary Beads binary"),
        },
        "repository": {
            **repository,
            "origin": primary["origin"],
            "remote_base_oid": base_oid,
        },
        "primary": primary,
        "bead": bead,
        "expected_branch": f"polecat/{bead_id}",
        "artifacts": artifacts,
    }
    intent_path = run_root / "intent.json"
    intent_bytes, _ = _write_append_only_json(intent_path, value)
    _validated_canary_intent(lock.parent, intent_path)
    return {
        **value,
        "intent_path": intent_path.as_posix(),
        "intent_sha256": _sha256(intent_bytes),
        "run_root": run_root.as_posix(),
        "next_contract": {
            "branch": value["expected_branch"],
            "base_commit": base_oid,
            "bead_id": bead_id,
            "required_final_bead_status": "closed",
            "required_pr_state": "MERGED",
        },
    }


def capture_controlled_canary(
    lock_path: Path,
    *,
    intent_path: Path,
    canary_worktree: Path,
    git_binary: Path = Path("/usr/bin/git"),
    gh_binary: Path = Path("/usr/bin/gh"),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Capture a merged run-bound canary from actual Git, GitHub, clone, and Beads state."""

    lock = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_value = load_runtime_lock(lock)
    _verified_provider_receipts(lock, lock_value)
    observed_at = clock()
    intent, intent_bytes = _validated_canary_intent(lock.parent, intent_path, now=observed_at)
    run_id = intent["run_id"]
    run_root = lock.parent / "runtime" / "evidence" / "canary-runs" / run_id
    git = _canonical_path(git_binary, must_exist=True, label="Git binary")
    gh = _canonical_path(gh_binary, must_exist=True, label="GitHub CLI binary")
    if not git.is_file() or not gh.is_file():
        raise GasCityOpsError("Git and GitHub CLI paths must be files")
    bd = lock.parent / "bin" / "bd"
    if (
        _sha256(_regular_file_bytes(bd, label="controlled canary Beads binary"))
        != lock_value["tools"]["bd"]["binary_sha256"]
    ):
        raise GasCityOpsError("controlled canary requires the lock-pinned city/bin/bd")
    if {
        "git": _tool_binding(git, label="Git binary"),
        "gh": _tool_binding(gh, label="GitHub CLI binary"),
        "bd": _tool_binding(bd, label="controlled canary Beads binary"),
    } != intent["tools"]:
        raise GasCityOpsError("controlled canary capture tools differ from the run intent")
    env, token = _github_environment(environment)
    non_github_env = dict(env)
    non_github_env.pop("GH_TOKEN", None)
    primary_repo = _require_aegis_migration_target(
        Path(intent["primary"]["path"]),
        intent["authority_target"],
        label="canary primary repository",
    )
    worktree = _canonical_path(canary_worktree, must_exist=True, label="controlled canary worktree")
    if (
        worktree.as_posix() != intent["bead"]["worktree"]
        or worktree == primary_repo
        or _is_within(worktree, primary_repo)
        or _is_within(primary_repo, worktree)
    ):
        raise GasCityOpsError("controlled canary requires a disjoint Git worktree")

    primary_before, primary_before_raw = _git_repository_probe(
        git,
        primary_repo,
        environment=non_github_env,
        runner=runner,
        artifact_prefix="primary before capture",
    )
    if primary_before != intent["primary"]:
        raise GasCityOpsError("primary repository changed after the canary intent")
    worktree_probe, worktree_raw = _git_repository_probe(
        git,
        worktree,
        environment=non_github_env,
        runner=runner,
        artifact_prefix="canary worktree",
    )
    if (
        worktree_probe["branch"] not in {intent["expected_branch"], "HEAD"}
        or worktree_probe["origin"] != intent["primary"]["origin"]
        or worktree_probe["common_git_dir"] != intent["primary"]["common_git_dir"]
        or worktree_raw["status"].strip()
    ):
        raise GasCityOpsError("canary worktree is not the clean run-bound isolated branch")

    repository_name = intent["repository"]["name_with_owner"]
    auth_raw = _command_stdout(
        (gh.as_posix(), "auth", "status", "--hostname", "github.com"),
        cwd=worktree,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub capture authentication",
        include_stderr=True,
    )
    repository_raw = _command_stdout(
        (
            gh.as_posix(),
            "repo",
            "view",
            repository_name,
            "--json",
            "nameWithOwner,url,viewerPermission,defaultBranchRef",
        ),
        cwd=worktree,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub capture repository",
    )
    repository = _github_repository_binding(
        _json_object_output(repository_raw, label="GitHub capture repository"),
        origin_repository=repository_name,
    )
    if (
        repository["name_with_owner"] != repository_name
        or repository["url"] != intent["repository"]["url"]
        or repository["default_branch"] != intent["repository"]["default_branch"]
    ):
        raise GasCityOpsError("GitHub repository identity changed during the controlled canary")
    pr_raw = _command_stdout(
        (
            gh.as_posix(),
            "pr",
            "view",
            intent["expected_branch"],
            "--repo",
            repository_name,
            "--json",
            (
                "number,url,state,isDraft,headRefName,headRefOid,baseRefName,"
                "mergeCommit,mergedAt,mergedBy"
            ),
        ),
        cwd=worktree,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub canary PR",
    )
    pr = _github_pr_binding(
        _json_object_output(pr_raw, label="GitHub canary PR"),
        repository=repository_name,
        expected_branch=intent["expected_branch"],
        expected_head=worktree_probe["head"],
        expected_base=repository["default_branch"],
    )
    checks_raw = _command_stdout(
        (
            gh.as_posix(),
            "pr",
            "checks",
            str(pr["number"]),
            "--repo",
            repository_name,
            "--json",
            "name,state,bucket,link,workflow",
        ),
        cwd=worktree,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub canary PR checks",
    )
    checks = _github_checks_binding(_json_array_output(checks_raw, label="GitHub canary PR checks"))
    base_ref_raw = _command_stdout(
        (
            gh.as_posix(),
            "api",
            f"repos/{repository_name}/git/ref/heads/{repository['default_branch']}",
        ),
        cwd=worktree,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub merged base ref",
    )
    remote_base_oid = _github_ref_oid(
        _json_object_output(base_ref_raw, label="GitHub merged base ref"),
        expected_ref=repository["default_branch"],
    )
    if remote_base_oid != pr["merge_commit"]:
        raise GasCityOpsError("GitHub base ref is not the captured PR merge commit")

    final_beads_raw = _command_stdout(
        (bd.as_posix(), "--readonly", "-C", primary_repo.as_posix(), "export", "--all"),
        cwd=primary_repo,
        environment=non_github_env,
        runner=runner,
        label="authoritative Beads completion export",
    )
    final_bead = _canary_bead_binding(
        _beads_record(
            final_beads_raw,
            bead_id=intent["bead"]["id"],
            label="authoritative Beads completion export",
        ),
        expected_status="closed",
        expected_branch=intent["expected_branch"],
        expected_worktree=intent["bead"]["worktree"],
        expected_target=repository["default_branch"],
        expected_pr_url=pr["url"],
    )
    if final_bead["assignee"] != CANARY_REFINERY_ASSIGNEE:
        raise GasCityOpsError(
            "authoritative Bead was not closed by the exact Aegis Gas Town refinery owner"
        )

    clone = run_root / "verification-clone"
    if clone.exists() or clone.is_symlink():
        raise GasCityOpsError("clean verification clone path already exists")
    clone_raw = _command_stdout(
        (
            gh.as_posix(),
            "repo",
            "clone",
            repository_name,
            clone.as_posix(),
            "--",
            "--no-checkout",
        ),
        cwd=run_root,
        environment=env,
        runner=runner,
        secrets_to_redact=(token,),
        label="GitHub clean verification clone",
        allow_empty=True,
        include_stderr=True,
    )
    clone = _canonical_path(clone, must_exist=True, label="clean verification clone")
    if not clone.is_dir() or clone.is_symlink() or not _is_within(clone, run_root):
        raise GasCityOpsError("GitHub CLI did not create the exact verification clone")
    os.chmod(clone, 0o700)
    checkout_raw = _command_stdout(
        (
            git.as_posix(),
            "-C",
            clone.as_posix(),
            "checkout",
            "--detach",
            pr["merge_commit"],
        ),
        cwd=clone,
        environment=non_github_env,
        runner=runner,
        label="verification clone checkout",
        allow_empty=True,
        include_stderr=True,
    )
    clone_head_raw = _command_stdout(
        (git.as_posix(), "-C", clone.as_posix(), "rev-parse", "HEAD"),
        cwd=clone,
        environment=non_github_env,
        runner=runner,
        label="verification clone head",
    )
    clone_status_raw = _command_stdout(
        (
            git.as_posix(),
            "-C",
            clone.as_posix(),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        cwd=clone,
        environment=non_github_env,
        runner=runner,
        label="verification clone status",
        allow_empty=True,
    )
    clone_fsck_raw = _command_stdout(
        (git.as_posix(), "-C", clone.as_posix(), "fsck", "--full", "--strict"),
        cwd=clone,
        environment=non_github_env,
        runner=runner,
        label="verification clone fsck",
        allow_empty=True,
        include_stderr=True,
    )
    clone_head = _one_line_output(clone_head_raw, label="verification clone head")
    if clone_head != pr["merge_commit"] or clone_status_raw.strip():
        raise GasCityOpsError("verification clone is not clean at the exact merge commit")

    primary_after, primary_after_raw = _git_repository_probe(
        git,
        primary_repo,
        environment=non_github_env,
        runner=runner,
        artifact_prefix="primary after capture",
    )
    if (
        primary_after != intent["primary"]
        or primary_after_raw["status"] != primary_before_raw["status"]
    ):
        raise GasCityOpsError("primary repository changed during controlled canary capture")
    finished_at = clock()
    created_at = _utc_timestamp(intent["created_at"], label="canary intent created_at")
    if (
        finished_at.tzinfo is None
        or finished_at.utcoffset() != dt.timedelta(0)
        or finished_at < observed_at
        or finished_at - created_at > CANARY_RUN_MAX_AGE
    ):
        raise GasCityOpsError("controlled canary capture exceeded its freshness window")

    artifact_contents: dict[str, bytes] = {
        "github_auth_capture": auth_raw,
        "github_repository_capture": repository_raw,
        "github_pr": pr_raw,
        "github_checks": checks_raw,
        "github_base_ref_capture": base_ref_raw,
        "github_clone": clone_raw,
        "primary_before_head": primary_before_raw["head"],
        "primary_before_branch": primary_before_raw["branch"],
        "primary_before_status": primary_before_raw["status"],
        "primary_before_origin": primary_before_raw["origin"],
        "primary_before_common_git_dir": primary_before_raw["common_git_dir"],
        "primary_after_head": primary_after_raw["head"],
        "primary_after_branch": primary_after_raw["branch"],
        "primary_after_status": primary_after_raw["status"],
        "primary_after_origin": primary_after_raw["origin"],
        "primary_after_common_git_dir": primary_after_raw["common_git_dir"],
        "worktree_head": worktree_raw["head"],
        "worktree_branch": worktree_raw["branch"],
        "worktree_status": worktree_raw["status"],
        "worktree_origin": worktree_raw["origin"],
        "worktree_common_git_dir": worktree_raw["common_git_dir"],
        "beads_final": final_beads_raw,
        "clone_checkout": checkout_raw,
        "clone_head": clone_head_raw,
        "clone_status": clone_status_raw,
        "clone_fsck": clone_fsck_raw,
    }
    artifacts = {
        name: _write_canary_artifact(
            run_root, lock.parent, f"{name.replace('_', '-')}.txt", content
        )
        for name, content in artifact_contents.items()
    }
    captured_at = _format_utc(finished_at)
    intent_reference = {
        "path": Path(intent_path).resolve().relative_to(lock.parent).as_posix(),
        "sha256": _sha256(intent_bytes),
    }
    binding, _, history, authority_target = _full_live_authority_state(lock.parent)
    if authority_target != intent["authority_target"]:
        raise GasCityOpsError(
            "canonical Aegis migration target changed during controlled canary capture"
        )
    _require_aegis_migration_target(
        primary_repo,
        authority_target,
        label="controlled canary primary repository",
    )
    github_artifact_names = {
        "github_auth_capture",
        "github_repository_capture",
        "github_pr",
        "github_checks",
        "github_base_ref_capture",
    }
    github_value = {
        "schema_version": 2,
        "kind": "github-delivery-canary",
        "status": "verified",
        "captured_at": captured_at,
        "run_id": run_id,
        "intent": intent_reference,
        "authority": binding,
        "authority_history": history,
        "repository": {
            **repository,
            "origin": worktree_probe["origin"],
        },
        "delivery": {
            **pr,
            "remote_base_oid": remote_base_oid,
            "checks": checks,
        },
        "artifacts": {name: artifacts[name] for name in sorted(github_artifact_names)},
    }
    github_path = run_root / "github.json"
    github_bytes, github_digest = _write_append_only_json(github_path, github_value)
    canary_artifact_names = set(artifacts) - github_artifact_names
    canary_value = {
        "schema_version": CANARY_EVIDENCE_SCHEMA_VERSION,
        "kind": "aegis-controlled-canary",
        "status": "verified",
        "captured_at": captured_at,
        "run_id": run_id,
        "rig": "aegis",
        "intent": intent_reference,
        "github_evidence": {
            "path": github_path.relative_to(lock.parent).as_posix(),
            "sha256": github_digest,
        },
        "authority": binding,
        "authority_history": history,
        "authority_target": authority_target,
        "primary": primary_after,
        "worktree": worktree_probe,
        "verification_clone": {
            "path": clone.as_posix(),
            "head": clone_head,
            "status_sha256": _sha256(clone_status_raw),
            "fsck_sha256": _sha256(clone_fsck_raw),
        },
        "bead": {
            "id": final_bead["id"],
            "start_assignee": intent["bead"]["assignee"],
            "final_assignee": final_bead["assignee"],
            "start_status": intent["bead"]["status"],
            "start_record_sha256": intent["bead"]["record_sha256"],
            "final_status": final_bead["status"],
            "final_record_sha256": final_bead["record_sha256"],
            "branch": final_bead["branch"],
            "worktree": final_bead["worktree"],
            "target": final_bead["target"],
            "pr_url": final_bead["pr_url"],
        },
        "artifacts": {name: artifacts[name] for name in sorted(canary_artifact_names)},
    }
    canary_path = run_root / "canary.json"
    canary_bytes, _ = _write_append_only_json(canary_path, canary_value)
    return {
        "status": "verified",
        "run_id": run_id,
        "intent_path": Path(intent_path).resolve().as_posix(),
        "intent_sha256": _sha256(intent_bytes),
        "github_evidence_path": github_path.as_posix(),
        "github_evidence_sha256": _sha256(github_bytes),
        "canary_evidence_path": canary_path.as_posix(),
        "canary_evidence_sha256": _sha256(canary_bytes),
        "pr": pr,
        "bead": canary_value["bead"],
    }


def _validate_provider_evidence(
    value: Mapping[str, Any],
    lock: Mapping[str, Any],
    *,
    lock_root: Path,
) -> None:
    sessions = value.get("sessions")
    captured_at = _utc_timestamp(value.get("captured_at"), label="provider captured_at")
    binding, _ = _live_authority_binding(lock_root)
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "captured_at",
            "authority_receipt_sha256",
            "sessions",
        }
        or value.get("schema_version") != 2
        or value.get("kind") != "provider-model-canary"
        or value.get("status") != "pass"
        or value.get("authority_receipt_sha256") != binding["receipt_sha256"]
        or captured_at
        < _utc_timestamp(binding["activated_at"], label="provider authority activated_at")
        or not isinstance(sessions, dict)
        or set(sessions) != {"claude", "codex"}
    ):
        raise GasCityOpsError("provider evidence is not bound to live Aegis authority")
    for provider in ("claude", "codex"):
        record = sessions[provider]
        if type(record) is not dict:
            raise GasCityOpsError(f"provider evidence is invalid for {provider}")
        supervisor = record.get("supervisor_receipt")
        transcript = record.get("transcript")
        if (
            type(supervisor) is not dict
            or set(supervisor) != {"path", "sha256"}
            or type(transcript) is not dict
            or set(transcript) != {"path", "sha256", "observations"}
            or type(supervisor.get("path")) is not str
            or type(transcript.get("path")) is not str
        ):
            raise GasCityOpsError(f"provider artifact records are invalid for {provider}")
        observed = _verified_provider_session(
            lock_root,
            lock,
            provider=provider,
            supervisor_receipt_path=lock_root / supervisor["path"],
            transcript_path=lock_root / transcript["path"],
        )
        if record != observed:
            raise GasCityOpsError(f"provider evidence artifacts drifted for {provider}")
    if sessions["claude"]["session"] == sessions["codex"]["session"]:
        raise GasCityOpsError("provider evidence reused one session across providers")


def _intent_reference(
    lock_root: Path,
    record: Any,
    *,
    run_id: str,
) -> tuple[dict[str, Any], bytes]:
    if (
        type(record) is not dict
        or set(record) != {"path", "sha256"}
        or record.get("path") != f"runtime/evidence/canary-runs/{run_id}/intent.json"
        or type(record.get("sha256")) is not str
        or SHA256_RE.fullmatch(record["sha256"]) is None
    ):
        raise GasCityOpsError("canary evidence intent reference is invalid")
    intent_path = lock_root / record["path"]
    intent, content = _validated_canary_intent(lock_root, intent_path)
    if _sha256(content) != record["sha256"] or intent["run_id"] != run_id:
        raise GasCityOpsError("canary evidence intent digest or run identity mismatched")
    return intent, content


def _validate_github_evidence(
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    evidence_path: Path,
) -> None:
    run_id = value.get("run_id")
    repository = value.get("repository")
    delivery = value.get("delivery")
    artifacts = value.get("artifacts")
    expected_path = lock_root / "runtime" / "evidence" / "canary-runs" / str(run_id) / "github.json"
    binding, _, history, _ = _full_live_authority_state(lock_root)
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "captured_at",
            "run_id",
            "intent",
            "authority",
            "authority_history",
            "repository",
            "delivery",
            "artifacts",
        }
        or value.get("schema_version") != 2
        or value.get("kind") != "github-delivery-canary"
        or value.get("status") != "verified"
        or type(run_id) is not str
        or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or _canonical_path(evidence_path, must_exist=True, label="GitHub evidence") != expected_path
        or value.get("authority") != binding
        or value.get("authority_history") != history
        or type(repository) is not dict
        or set(repository)
        != {"name_with_owner", "url", "viewer_permission", "default_branch", "origin"}
        or type(delivery) is not dict
        or set(delivery)
        != {
            "number",
            "url",
            "state",
            "is_draft",
            "head_ref",
            "head_oid",
            "base_ref",
            "merge_commit",
            "merged_at",
            "merged_by",
            "remote_base_oid",
            "checks",
        }
        or type(artifacts) is not dict
        or set(artifacts)
        != {
            "github_auth_capture",
            "github_repository_capture",
            "github_pr",
            "github_checks",
            "github_base_ref_capture",
        }
    ):
        raise GasCityOpsError("GitHub evidence is not an exact run-bound delivery receipt")
    intent, _ = _intent_reference(lock_root, value["intent"], run_id=run_id)
    captured = _utc_timestamp(value["captured_at"], label="GitHub captured_at")
    created = _utc_timestamp(intent["created_at"], label="canary intent created_at")
    if captured < created or captured - created > CANARY_RUN_MAX_AGE:
        raise GasCityOpsError("GitHub delivery evidence was captured from a stale intent")
    if (
        repository.get("name_with_owner") != intent["repository"]["name_with_owner"]
        or repository.get("url") != intent["repository"]["url"]
        or repository.get("default_branch") != intent["repository"]["default_branch"]
        or repository.get("origin") != intent["repository"]["origin"]
        or repository.get("viewer_permission") not in {"WRITE", "MAINTAIN", "ADMIN"}
        or delivery.get("head_ref") != intent["expected_branch"]
        or delivery.get("base_ref") != repository.get("default_branch")
        or delivery.get("remote_base_oid") != delivery.get("merge_commit")
    ):
        raise GasCityOpsError("GitHub delivery identity disagrees with the run intent")
    loaded = {
        name: _load_canary_artifact(
            lock_root, record, run_id=run_id, label=f"GitHub delivery {name}"
        )
        for name, record in artifacts.items()
    }
    if not loaded["github_auth_capture"].strip():
        raise GasCityOpsError("GitHub authentication artifact is empty")
    raw_repository = _github_repository_binding(
        _json_object_output(
            loaded["github_repository_capture"], label="GitHub repository artifact"
        ),
        origin_repository=intent["repository"]["name_with_owner"],
    )
    if raw_repository != {key: repository[key] for key in raw_repository}:
        raise GasCityOpsError("GitHub repository artifact drifted")
    raw_pr = _github_pr_binding(
        _json_object_output(loaded["github_pr"], label="GitHub PR artifact"),
        repository=repository["name_with_owner"],
        expected_branch=intent["expected_branch"],
        expected_head=delivery["head_oid"],
        expected_base=repository["default_branch"],
    )
    raw_checks = _github_checks_binding(
        _json_array_output(loaded["github_checks"], label="GitHub checks artifact")
    )
    raw_base = _github_ref_oid(
        _json_object_output(loaded["github_base_ref_capture"], label="GitHub base ref artifact"),
        expected_ref=repository["default_branch"],
    )
    expected_delivery = {**raw_pr, "remote_base_oid": raw_base, "checks": raw_checks}
    if delivery != expected_delivery or raw_base != raw_pr["merge_commit"]:
        raise GasCityOpsError("GitHub PR, checks, or merged ref artifact drifted")
    merged_at = _utc_timestamp(delivery["merged_at"], label="GitHub PR merged_at")
    if merged_at < created or merged_at > captured:
        raise GasCityOpsError("GitHub PR merge time is outside its controlled canary run")


def _validate_obsidian_evidence(
    value: Mapping[str, Any],
    lock: Mapping[str, Any],
    *,
    lock_root: Path,
) -> None:
    builds = value.get("builds")
    captured_at = _utc_timestamp(value.get("captured_at"), label="Obsidian captured_at")
    binding, _, _, authority_target = _full_live_authority_state(lock_root)
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "captured_at",
            "authority_receipt_sha256",
            "authority_target",
            "source_digest",
            "dolt_main_head",
            "bd_binary_sha256",
            "builds",
        }
        or value.get("schema_version") != OBSIDIAN_EVIDENCE_SCHEMA_VERSION
        or value.get("kind") != "obsidian-deterministic-projection"
        or value.get("status") != "pass"
        or value.get("authority_receipt_sha256") != binding["receipt_sha256"]
        or value.get("authority_target") != authority_target
        or captured_at
        < _utc_timestamp(binding["activated_at"], label="Obsidian authority activated_at")
        or not isinstance(value.get("source_digest"), str)
        or SHA256_RE.fullmatch(str(value["source_digest"])) is None
        or not isinstance(value.get("dolt_main_head"), str)
        or re.fullmatch(r"[0-9a-v]{20,128}", str(value["dolt_main_head"]).lower()) is None
        or value.get("bd_binary_sha256") != lock["tools"]["bd"]["binary_sha256"]
        or type(builds) is not list
        or len(builds) != 2
    ):
        raise GasCityOpsError("Obsidian evidence does not prove an exact deterministic rebuild")
    manifests: list[bytes] = []
    directories: set[str] = set()
    for number, record in enumerate(builds, start=1):
        if (
            type(record) is not dict
            or set(record) != {"directory", "manifest_path", "manifest_sha256"}
            or type(record.get("directory")) is not str
            or type(record.get("manifest_path")) is not str
            or type(record.get("manifest_sha256")) is not str
            or SHA256_RE.fullmatch(record["manifest_sha256"]) is None
        ):
            raise GasCityOpsError(f"Obsidian build {number} record is invalid")
        relative_directory = Path(record["directory"])
        relative_manifest = Path(record["manifest_path"])
        if (
            relative_directory.is_absolute()
            or relative_manifest.is_absolute()
            or ".." in relative_directory.parts
            or ".." in relative_manifest.parts
            or relative_directory.parts[:3] != ("runtime", "evidence", "obsidian")
            or relative_manifest != relative_directory / ".aegis-vault.json"
            or record["directory"] in directories
        ):
            raise GasCityOpsError(f"Obsidian build {number} path is unsafe")
        directories.add(record["directory"])
        manifest_bytes, manifest = _validated_obsidian_manifest(
            lock_root / relative_directory,
            expected_bd_sha256=lock["tools"]["bd"]["binary_sha256"],
        )
        if (
            _sha256(manifest_bytes) != record["manifest_sha256"]
            or manifest.get("source_digest") != value["source_digest"]
            or manifest.get("task_dolt_main_head") != value["dolt_main_head"]
        ):
            raise GasCityOpsError(f"Obsidian build {number} manifest drifted")
        manifests.append(manifest_bytes)
    if manifests[0] != manifests[1]:
        raise GasCityOpsError("Obsidian double-build manifests are no longer identical")


def _probe_from_artifacts(
    loaded: Mapping[str, bytes],
    *,
    prefix: str,
    expected: Mapping[str, str],
) -> None:
    if (
        _one_line_output(loaded[f"{prefix}_head"], label=f"{prefix} head") != expected["head"]
        or _one_line_output(loaded[f"{prefix}_branch"], label=f"{prefix} branch")
        != expected["branch"]
        or _sha256(loaded[f"{prefix}_status"]) != expected["status_sha256"]
        or _one_line_output(loaded[f"{prefix}_origin"], label=f"{prefix} origin")
        != expected["origin"]
        or _git_common_directory(
            Path(expected["path"]),
            _one_line_output(
                loaded[f"{prefix}_common_git_dir"], label=f"{prefix} common Git directory"
            ),
        ).as_posix()
        != expected["common_git_dir"]
    ):
        raise GasCityOpsError(f"{prefix} Git artifacts drifted")


def _validate_canary_evidence(
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    evidence_path: Path,
    evidence_records: Mapping[str, Mapping[str, str]],
) -> None:
    run_id = value.get("run_id")
    primary = value.get("primary")
    worktree = value.get("worktree")
    clone = value.get("verification_clone")
    bead = value.get("bead")
    artifacts = value.get("artifacts")
    expected_path = lock_root / "runtime" / "evidence" / "canary-runs" / str(run_id) / "canary.json"
    binding, _, history, authority_target = _full_live_authority_state(lock_root)
    probe_shape = {"path", "head", "branch", "origin", "common_git_dir", "status_sha256"}
    expected_artifacts = {
        "github_clone",
        "primary_before_head",
        "primary_before_branch",
        "primary_before_status",
        "primary_before_origin",
        "primary_before_common_git_dir",
        "primary_after_head",
        "primary_after_branch",
        "primary_after_status",
        "primary_after_origin",
        "primary_after_common_git_dir",
        "worktree_head",
        "worktree_branch",
        "worktree_status",
        "worktree_origin",
        "worktree_common_git_dir",
        "beads_final",
        "clone_checkout",
        "clone_head",
        "clone_status",
        "clone_fsck",
    }
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "captured_at",
            "run_id",
            "rig",
            "intent",
            "github_evidence",
            "authority",
            "authority_history",
            "authority_target",
            "primary",
            "worktree",
            "verification_clone",
            "bead",
            "artifacts",
        }
        or value.get("schema_version") != CANARY_EVIDENCE_SCHEMA_VERSION
        or value.get("kind") != "aegis-controlled-canary"
        or value.get("status") != "verified"
        or value.get("rig") != "aegis"
        or type(run_id) is not str
        or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or _canonical_path(evidence_path, must_exist=True, label="controlled canary evidence")
        != expected_path
        or value.get("authority") != binding
        or value.get("authority_history") != history
        or value.get("authority_target") != authority_target
        or type(primary) is not dict
        or set(primary) != probe_shape
        or any(type(primary.get(field)) is not str or not primary[field] for field in probe_shape)
        or type(worktree) is not dict
        or set(worktree) != probe_shape
        or type(clone) is not dict
        or set(clone) != {"path", "head", "status_sha256", "fsck_sha256"}
        or type(bead) is not dict
        or set(bead)
        != {
            "id",
            "start_assignee",
            "final_assignee",
            "start_status",
            "start_record_sha256",
            "final_status",
            "final_record_sha256",
            "branch",
            "worktree",
            "target",
            "pr_url",
        }
        or type(artifacts) is not dict
        or set(artifacts) != expected_artifacts
    ):
        raise GasCityOpsError("canary evidence is not an exact controlled Aegis receipt")
    intent, _ = _intent_reference(lock_root, value["intent"], run_id=run_id)
    captured = _utc_timestamp(value["captured_at"], label="controlled canary captured_at")
    created = _utc_timestamp(intent["created_at"], label="canary intent created_at")
    if captured < created or captured - created > CANARY_RUN_MAX_AGE:
        raise GasCityOpsError("controlled canary evidence was captured from a stale intent")
    github_record = evidence_records.get("github")
    if value.get("github_evidence") != github_record:
        raise GasCityOpsError("controlled canary did not bind the promoted GitHub receipt")
    github_path, _, github_value = _load_evidence_record(
        lock_root, github_record, label="controlled canary GitHub receipt"
    )
    _validate_github_evidence(github_value, lock_root=lock_root, evidence_path=github_path)
    if github_value["run_id"] != run_id or github_value["captured_at"] != value["captured_at"]:
        raise GasCityOpsError("controlled canary and GitHub receipts are from different runs")
    if (
        primary != intent["primary"]
        or worktree.get("branch") not in {intent["expected_branch"], "HEAD"}
        or worktree.get("origin") != primary.get("origin")
        or worktree.get("common_git_dir") != primary.get("common_git_dir")
        or worktree.get("head") != github_value["delivery"]["head_oid"]
        or worktree.get("status_sha256") != _sha256(b"")
        or bead.get("id") != intent["bead"]["id"]
        or bead.get("start_assignee") != intent["bead"]["assignee"]
        or CANARY_POLECAT_ASSIGNEE_RE.fullmatch(str(bead.get("start_assignee"))) is None
        or bead.get("final_assignee") != CANARY_REFINERY_ASSIGNEE
        or bead.get("branch") != intent["expected_branch"]
        or bead.get("worktree") != intent["bead"]["worktree"]
        or bead.get("target") != github_value["repository"]["default_branch"]
        or bead.get("pr_url") != github_value["delivery"]["url"]
        or bead.get("start_status") != "in_progress"
        or bead.get("start_record_sha256") != intent["bead"]["record_sha256"]
        or bead.get("final_status") != "closed"
        or clone.get("head") != github_value["delivery"]["merge_commit"]
        or clone.get("status_sha256") != _sha256(b"")
    ):
        raise GasCityOpsError("controlled canary Git, PR, or Bead identities disagree")
    primary_path = _canonical_path(Path(primary["path"]), must_exist=True, label="primary repo")
    _require_aegis_migration_target(
        primary_path,
        authority_target,
        label="controlled canary primary repository",
    )
    if primary.get("common_git_dir") != authority_target["git_common_dir"]:
        raise GasCityOpsError("controlled canary primary Git identity is not authority-bound")
    worktree_path = _canonical_path(
        Path(worktree["path"]), must_exist=True, label="canary worktree"
    )
    clone_path = _canonical_path(Path(clone["path"]), must_exist=True, label="verification clone")
    run_root = lock_root / "runtime" / "evidence" / "canary-runs" / run_id
    if (
        primary_path == worktree_path
        or _is_within(primary_path, worktree_path)
        or _is_within(worktree_path, primary_path)
        or clone_path != run_root / "verification-clone"
        or not clone_path.is_dir()
        or clone_path.is_symlink()
    ):
        raise GasCityOpsError("controlled canary paths do not prove isolation")
    loaded = {
        name: _load_canary_artifact(
            lock_root, record, run_id=run_id, label=f"controlled canary {name}"
        )
        for name, record in artifacts.items()
    }
    _probe_from_artifacts(loaded, prefix="primary_before", expected=primary)
    _probe_from_artifacts(loaded, prefix="primary_after", expected=primary)
    _probe_from_artifacts(loaded, prefix="worktree", expected=worktree)
    if (
        loaded["primary_before_status"] != loaded["primary_after_status"]
        or loaded["worktree_status"].strip()
        or not isinstance(loaded["github_clone"], bytes)
        or _one_line_output(loaded["clone_head"], label="verification clone head") != clone["head"]
        or loaded["clone_status"].strip()
        or _sha256(loaded["clone_status"]) != clone["status_sha256"]
        or _sha256(loaded["clone_fsck"]) != clone["fsck_sha256"]
    ):
        raise GasCityOpsError("controlled canary isolation or verification-clone artifacts drifted")
    final_record = _beads_record(
        loaded["beads_final"], bead_id=bead["id"], label="canary final Beads export"
    )
    final_binding = _canary_bead_binding(
        final_record,
        expected_status="closed",
        expected_branch=bead["branch"],
        expected_worktree=bead["worktree"],
        expected_target=bead["target"],
        expected_pr_url=bead["pr_url"],
    )
    if (
        final_binding["assignee"] != bead["final_assignee"]
        or final_binding["record_sha256"] != bead["final_record_sha256"]
    ):
        raise GasCityOpsError("controlled canary authoritative Bead artifact drifted")


def _validate_supervisor_running(
    value: Mapping[str, Any], *, environment: Mapping[str, str]
) -> None:
    expected_paths = _supervisor_socket_paths(environment)
    required = {
        "schema_version",
        "ok",
        "checked_paths",
        "pid",
        "running",
        "socket_path",
    }
    if (
        not required.issubset(value)
        or value.get("schema_version") != "1"
        or value.get("ok") is not True
        or value.get("running") is not True
        or type(value.get("pid")) is not int
        or value["pid"] <= 0
        or type(value.get("socket_path")) is not str
        or not value["socket_path"]
        or value.get("checked_paths") != expected_paths
        or value.get("socket_path") not in expected_paths
    ):
        raise GasCityOpsError("gc supervisor status does not prove a live exact-city supervisor")


def _soak_owner_directory(path: Path, *, label: str) -> Path:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GasCityOpsError(f"{label} is missing") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise GasCityOpsError(f"{label} must be one owner-only real directory")
    return path.resolve(strict=True)


def _validate_soak_session_receipt(
    value: Mapping[str, Any],
    *,
    provider: str,
    lock: Mapping[str, Any],
) -> dt.datetime:
    expected_model = lock["providers"][provider]["requested_model"]
    expected_effort = lock["providers"][provider].get("reasoning_effort")
    worker_image = lock["images"][f"{provider}_worker"]["image_id"]
    digest_fields = (
        "event_sha256",
        "transcript_sha256",
        "challenge_sha256",
        "run_id_sha256",
        "session_id_sha256",
        "git_broker_receipt_sha256",
        "preflight_receipt_sha256",
    )
    optional_digest = value.get("git_startup_receipt_sha256")
    integer_fields = (
        "container_init_host_pid",
        "supervisor_host_pid",
        "supervisor_starttime_ticks",
    )
    if (
        set(value) != HOST_MODEL_SESSION_RECEIPT_FIELDS
        or value.get("schema_version") != 1
        or value.get("kind") != "host-model-evidence-receipt"
        or value.get("status") != "verified"
        or value.get("phase") != "session"
        or value.get("provider") != provider
        or value.get("expected_model") != expected_model
        or value.get("observed_model") != expected_model
        or value.get("expected_effort") != expected_effort
        or value.get("observed_effort") != expected_effort
        or value.get("provider_exit_code") != 0
        or value.get("tool_free") is not False
        or value.get("container_image_id") != worker_image
        or value.get("container_boundary") != "isolated-worker"
        or value.get("model_source_phase") != "preflight"
        or value.get("model_attestation_scope") != HOST_MODEL_ATTESTATION_SCOPE
        or not isinstance(value.get("transcript_locator"), str)
        or not value["transcript_locator"].startswith("/home/worker/")
        or not isinstance(value.get("container_name"), str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value["container_name"]) is None
        or not isinstance(value.get("evidence_id"), str)
        or re.fullmatch(r"[0-9a-f]{32}", value["evidence_id"]) is None
        or type(value.get("run_generation")) is not int
        or value["run_generation"] < 1
        or not isinstance(value.get("git_broker_id"), str)
        or re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            value["git_broker_id"],
        )
        is None
        or not isinstance(value.get("git_source_starting_oid"), str)
        or GIT_OBJECT_RE.fullmatch(value["git_source_starting_oid"]) is None
        or not isinstance(value.get("git_authorized_ref"), str)
        or not value["git_authorized_ref"].startswith("refs/heads/")
        or GIT_REF_RE.fullmatch(value["git_authorized_ref"].removeprefix("refs/heads/")) is None
        or any(
            not isinstance(value.get(field), str) or SHA256_RE.fullmatch(value[field]) is None
            for field in digest_fields
        )
        or (
            optional_digest is not None
            and (
                not isinstance(optional_digest, str) or SHA256_RE.fullmatch(optional_digest) is None
            )
        )
        or any(type(value.get(field)) is not int or value[field] <= 0 for field in integer_fields)
        or type(value.get("supervisor_host_uid")) is not int
        or value["supervisor_host_uid"] != os.getuid()
        or type(value.get("supervisor_host_gid")) is not int
        or value["supervisor_host_gid"] != os.getgid()
    ):
        raise GasCityOpsError(f"soak {provider} session receipt is invalid")
    return _utc_timestamp(value.get("recorded_at"), label=f"soak {provider} session recorded_at")


def _fresh_soak_session_receipts(
    city: Path,
    lock: Mapping[str, Any],
    *,
    observed_at: dt.datetime,
) -> dict[str, dict[str, Any]]:
    root = _soak_owner_directory(
        city / "runtime" / "state" / "git-broker" / "rig-aegis",
        label="soak Aegis Git broker state root",
    )
    candidates: dict[str, list[tuple[dt.datetime, Path, bytes, Mapping[str, Any]]]] = {
        "claude": [],
        "codex": [],
    }
    for agent_path in sorted(root.iterdir(), key=lambda item: item.name):
        if SOAK_AGENT_RE.fullmatch(agent_path.name) is None:
            raise GasCityOpsError("soak Git broker state contains an unsafe agent name")
        agent = _soak_owner_directory(agent_path, label="soak Git broker agent state")
        for session_path in sorted(agent.iterdir(), key=lambda item: item.name):
            if SOAK_SESSION_RE.fullmatch(session_path.name) is None:
                raise GasCityOpsError("soak Git broker state contains an unsafe session name")
            session = _soak_owner_directory(session_path, label="soak Git broker session state")
            model_path = session / "model-evidence"
            if not model_path.exists() and not model_path.is_symlink():
                continue
            model = _soak_owner_directory(model_path, label="soak model evidence state")
            receipt_path = model / "session-receipt.json"
            if not receipt_path.exists() and not receipt_path.is_symlink():
                continue
            try:
                metadata = receipt_path.lstat()
            except OSError as exc:
                raise GasCityOpsError("soak session receipt cannot be inspected") from exc
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o400
                or metadata.st_nlink != 1
            ):
                raise GasCityOpsError("soak session receipt has unsafe file metadata")
            content = _regular_file_bytes(receipt_path, label="soak session receipt")
            value = _load_json_bytes(content, label="soak session receipt")
            if not isinstance(value, dict) or value.get("provider") not in candidates:
                raise GasCityOpsError("soak session receipt has an invalid provider")
            provider = str(value["provider"])
            recorded = _validate_soak_session_receipt(value, provider=provider, lock=lock)
            if recorded > observed_at:
                raise GasCityOpsError("soak session receipt is future-dated")
            age = int((observed_at - recorded).total_seconds())
            if age <= SOAK_MAX_SESSION_RECEIPT_AGE_SECONDS:
                candidates[provider].append((recorded, receipt_path, content, value))
    selected: dict[str, dict[str, Any]] = {}
    for provider, records in candidates.items():
        if not records:
            raise GasCityOpsError(f"soak lacks a fresh successful {provider} session receipt")
        recorded, receipt_path, content, value = max(
            records, key=lambda item: (item[0], item[1].as_posix())
        )
        selected[provider] = {
            "path": receipt_path.relative_to(city).as_posix(),
            "sha256": _sha256(content),
            "recorded_at": _format_utc(recorded),
            "age_seconds": int((observed_at - recorded).total_seconds()),
            "evidence_id": value["evidence_id"],
            "session_id_sha256": value["session_id_sha256"],
            "git_broker_id": value["git_broker_id"],
        }
    return selected


def _live_soak_checks(
    lock_path: Path,
    lock: Mapping[str, Any],
    *,
    target_repo: Path,
    vault: Path,
    source_root: Path,
    python_binary: Path,
    runner: Runner,
    environment: Mapping[str, str],
    observed_at: dt.datetime,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = lock_path
    city = path.parent
    binding, _, history, _ = _full_live_authority_state(city)
    provider_digests = _verified_provider_receipts(path, lock)
    model_records = {
        provider: {
            "path": str(lock["providers"][provider]["receipt_path"]),
            "sha256": digest,
        }
        for provider, digest in provider_digests.items()
    }
    session_records = _fresh_soak_session_receipts(city, lock, observed_at=observed_at)
    bd = city / "bin" / "bd"
    gc = city / "bin" / "gc"
    for name, binary in (("bd", bd), ("gc", gc)):
        observed = _sha256(_regular_file_bytes(binary, label=f"soak {name} binary"))
        if observed != lock["tools"][name]["binary_sha256"]:
            raise GasCityOpsError(f"soak {name} binary does not match the runtime lock")
    repo = _canonical_path(target_repo, must_exist=True, label="soak target repository")
    from aegis_foundation import gas_city_authority

    report = gas_city_authority.verify_authority_chain(
        city,
        rig=LIVE_AUTHORITY_IDENTITY["rig"],
        beads_prefix=LIVE_AUTHORITY_IDENTITY["beads_prefix"],
        database=LIVE_AUTHORITY_IDENTITY["database"],
    )
    expected_target = report.generation_records[0]["baseline_evidence"]["migration"][
        "target_directory"
    ]
    if repo.as_posix() != expected_target:
        raise GasCityOpsError("soak target is not the authority-bound migration target")
    head_command = (
        bd.as_posix(),
        "--json",
        "--readonly",
        "-C",
        repo.as_posix(),
        "sql",
        "SELECT HASHOF('main') AS head;",
    )
    export_command = (
        bd.as_posix(),
        "--readonly",
        "-C",
        repo.as_posix(),
        "export",
        "--all",
    )
    head_before_output = _checked(
        head_command, cwd=repo, environment=environment, runner=runner
    ).stdout
    first_export = _checked(
        export_command, cwd=repo, environment=environment, runner=runner
    ).stdout.encode("utf-8")
    second_export = _checked(
        export_command, cwd=repo, environment=environment, runner=runner
    ).stdout.encode("utf-8")
    head_after_output = _checked(
        head_command, cwd=repo, environment=environment, runner=runner
    ).stdout
    head_before = _head_from_json(head_before_output, label="soak Beads head before")
    head_after = _head_from_json(head_after_output, label="soak Beads head after")
    first_canonical = _canonical_jsonl(
        first_export.decode("utf-8"), label="soak first Beads export"
    )
    second_canonical = _canonical_jsonl(
        second_export.decode("utf-8"), label="soak second Beads export"
    )
    exported_records = _jsonl_records(first_export, label="soak Beads export")
    if (
        not exported_records
        or any(
            type(record.get("id")) is not str
            or not record["id"].startswith(LIVE_AUTHORITY_IDENTITY["beads_prefix"] + "-")
            for record in exported_records
        )
        or head_before != head_after
        or first_canonical != second_canonical
    ):
        raise GasCityOpsError("live Beads export changed or escaped the exact Aegis identity")
    vault_path = _canonical_path(vault, must_exist=True, label="soak Obsidian vault")
    if not _is_within(vault_path, city / "runtime" / "evidence" / "obsidian"):
        raise GasCityOpsError("soak Obsidian vault is outside runtime evidence")
    manifest_bytes, manifest = _validated_obsidian_manifest(
        vault_path,
        expected_bd_sha256=lock["tools"]["bd"]["binary_sha256"],
    )
    if manifest["task_dolt_main_head"] != head_after:
        raise GasCityOpsError("Obsidian projection is not at the live Beads head")
    source = _canonical_path(source_root, must_exist=True, label="Aegis source root")
    python = _canonical_path(python_binary, must_exist=True, label="Python binary")
    check_output = _checked(
        (
            python.as_posix(),
            "-m",
            "aegis_foundation.cli",
            "--source-root",
            source.as_posix(),
            "vault",
            "check",
            "--target-dir",
            repo.as_posix(),
            "--output",
            vault_path.as_posix(),
            "--bd-executable",
            bd.as_posix(),
            "--expected-bd-sha256",
            lock["tools"]["bd"]["binary_sha256"],
        ),
        cwd=source,
        environment=environment,
        runner=runner,
    ).stdout
    projection_check = _strict_json_object(check_output, label="live Obsidian check")
    if (
        projection_check.get("ok") is not True
        or projection_check.get("fresh") is not True
        or projection_check.get("authority") != "derived-read-only"
        or projection_check.get("source_digest") != manifest["source_digest"]
    ):
        raise GasCityOpsError("live Obsidian projection check failed or is stale")
    supervisor_text = _checked(
        (gc.as_posix(), "--city", city.as_posix(), "supervisor", "status", "--json"),
        cwd=city,
        environment=environment,
        runner=runner,
    ).stdout
    supervisor = _strict_json_object(supervisor_text, label="soak supervisor status")
    _validate_supervisor_running(supervisor, environment=environment)
    manifest_relative = manifest_path = vault_path / ".aegis-vault.json"
    manifest_relative = manifest_path.relative_to(city).as_posix()
    checks = {
        "models": {
            "promotion_receipts": model_records,
            "latest_sessions": session_records,
        },
        "beads": {
            "target_directory": repo.as_posix(),
            "dolt_main_head": head_after,
            "canonical_export_sha256": _sha256(first_canonical),
            "record_count": len(exported_records),
        },
        "reconciliation": {
            "head_before": head_before,
            "head_after": head_after,
            "first_raw_export_sha256": _sha256(first_export),
            "second_raw_export_sha256": _sha256(second_export),
            "canonical_export_sha256": _sha256(first_canonical),
        },
        "projection": {
            "directory": vault_path.relative_to(city).as_posix(),
            "manifest_path": manifest_relative,
            "manifest_sha256": _sha256(manifest_bytes),
            "source_digest": manifest["source_digest"],
            "dolt_main_head": manifest["task_dolt_main_head"],
        },
        "supervisor": {
            "gc_binary_sha256": lock["tools"]["gc"]["binary_sha256"],
            "pid": supervisor["pid"],
            "socket_path": supervisor["socket_path"],
            "checked_paths": list(supervisor["checked_paths"]),
            "status_sha256": _sha256(supervisor_text.encode("utf-8")),
        },
        "authority": {
            "receipt_sha256": binding["receipt_sha256"],
            "history_record_sha256": history["current_record_sha256"],
        },
    }
    return binding, checks


def _canonical_soak_line(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _append_soak_observation(path: Path, value: Mapping[str, Any]) -> tuple[int, str]:
    _make_private_parents(path.parent)
    lock_path = path.with_suffix(path.suffix + ".lock")
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        if path.exists() or path.is_symlink():
            content = _regular_file_bytes(path, label="soak observations")
            if stat.S_IMODE(path.stat().st_mode) != 0o600:
                raise GasCityOpsError("soak observations permissions must be exactly 0600")
            records = _jsonl_records(content, label="soak observations")
            if content != b"".join(_canonical_soak_line(record) for record in records):
                raise GasCityOpsError("soak observations must use canonical append-only JSONL")
        else:
            records = []
        previous = None if not records else _sha256(_canonical_soak_line(records[-1]))
        if value.get("previous_observation_sha256") != previous:
            raise GasCityOpsError("soak observation previous-record binding is invalid")
        line = _canonical_soak_line(value)
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        output_fd = os.open(
            path,
            os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | no_follow,
            0o600,
        )
        try:
            os.fchmod(output_fd, 0o600)
            os.write(output_fd, line)
            os.fsync(output_fd)
        finally:
            os.close(output_fd)
        return len(records) + 1, _sha256(line)
    except OSError as exc:
        raise GasCityOpsError("cannot append soak observation") from exc
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def capture_soak_observation(
    lock_path: Path,
    *,
    target_repo: Path,
    vault: Path,
    observations_path: Path,
    source_root: Path,
    python_binary: Path = Path(sys.executable),
    runner: Runner = _default_runner,
    environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Append one observation derived only from live production probes."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(path, require_observed_models=True)
    if lock["status"] != "canary_passed_soaking":
        raise GasCityOpsError("soak observations require an actively soaking canary")
    destination = _safe_evidence_output(
        path.parent, observations_path, label="soak observations output"
    )
    expected_root = path.parent / "runtime" / "evidence" / "soak"
    if not _is_within(destination, expected_root) or destination == expected_root:
        raise GasCityOpsError("soak observations must live beneath runtime/evidence/soak")
    env = dict(os.environ if environment is None else environment)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    observed = clock()
    observed_at = _format_utc(observed)
    authority, checks = _live_soak_checks(
        path,
        lock,
        target_repo=target_repo,
        vault=vault,
        source_root=source_root,
        python_binary=python_binary,
        runner=runner,
        environment=env,
        observed_at=observed,
    )
    existing: list[dict[str, Any]] = []
    if destination.exists():
        existing = _jsonl_records(
            _regular_file_bytes(destination, label="soak observations"),
            label="soak observations",
        )
    previous = None if not existing else _sha256(_canonical_soak_line(existing[-1]))
    if existing and _utc_timestamp(observed_at, label="soak observed_at") <= _utc_timestamp(
        existing[-1].get("observed_at"), label="previous soak observed_at"
    ):
        raise GasCityOpsError("soak observation time must strictly increase")
    value = {
        "schema_version": 3,
        "observed_at": observed_at,
        "status": "verified",
        "previous_observation_sha256": previous,
        "authority": authority,
        "checks": checks,
    }
    count, digest = _append_soak_observation(destination, value)
    return {
        **value,
        "observations_path": destination.as_posix(),
        "observation_number": count,
        "observation_sha256": digest,
    }


def _validate_soak_observations(
    content: bytes,
    *,
    started: dt.datetime,
    ended: dt.datetime,
    expected_authority: Mapping[str, Any],
    lock_root: Path,
) -> tuple[int, int]:
    records = _jsonl_records(content, label="soak observations")
    if len(records) < 2:
        raise GasCityOpsError("soak requires at least two continuous observations")
    if content != b"".join(_canonical_soak_line(record) for record in records):
        raise GasCityOpsError("soak observations are not canonical append-only JSONL")
    for number, record in enumerate(records, start=1):
        if (
            set(record)
            != {
                "schema_version",
                "observed_at",
                "status",
                "previous_observation_sha256",
                "checks",
                "authority",
            }
            or record.get("schema_version") != 3
            or record.get("status") != "verified"
            or type(record.get("checks")) is not dict
            or set(record["checks"]) != SOAK_REQUIRED_CHECKS
        ):
            raise GasCityOpsError(f"soak observation {number} is not a chained live-probe record")
    raw_lock = _load_json_bytes(
        _regular_file_bytes(lock_root / "runtime-lock.json", label="soak runtime lock"),
        label="soak runtime lock",
    )
    if type(raw_lock) is not dict:
        raise GasCityOpsError("soak runtime lock is invalid")
    expected_bd_sha256 = raw_lock["tools"]["bd"]["binary_sha256"]
    expected_history_sha256 = _full_live_authority_state(lock_root)[2]["current_record_sha256"]
    times: list[dt.datetime] = []
    previous_digest: str | None = None
    distinct_sessions: dict[str, set[str]] = {"claude": set(), "codex": set()}
    for number, record in enumerate(records, start=1):
        checks = record.get("checks")
        if (
            set(record)
            != {
                "schema_version",
                "observed_at",
                "status",
                "previous_observation_sha256",
                "checks",
                "authority",
            }
            or record.get("schema_version") != 3
            or record.get("status") != "verified"
            or record.get("previous_observation_sha256") != previous_digest
            or record.get("authority") != dict(expected_authority)
            or not isinstance(checks, dict)
            or set(checks) != SOAK_REQUIRED_CHECKS
        ):
            raise GasCityOpsError(f"soak observation {number} is not a chained live-probe record")
        models = checks["models"]
        beads = checks["beads"]
        reconciliation = checks["reconciliation"]
        projection = checks["projection"]
        supervisor = checks["supervisor"]
        authority = checks["authority"]
        observed = _utc_timestamp(
            record.get("observed_at"),
            label=f"soak observation {number} observed_at",
        )
        promotion_receipts = models.get("promotion_receipts") if type(models) is dict else None
        latest_sessions = models.get("latest_sessions") if type(models) is dict else None
        if (
            type(models) is not dict
            or set(models) != {"promotion_receipts", "latest_sessions"}
            or type(promotion_receipts) is not dict
            or set(promotion_receipts) != {"claude", "codex"}
            or type(latest_sessions) is not dict
            or set(latest_sessions) != {"claude", "codex"}
        ):
            raise GasCityOpsError(f"soak observation {number} model proof is invalid")
        for provider, artifact in promotion_receipts.items():
            if (
                type(artifact) is not dict
                or set(artifact) != {"path", "sha256"}
                or type(artifact.get("path")) is not str
                or type(artifact.get("sha256")) is not str
                or SHA256_RE.fullmatch(artifact["sha256"]) is None
            ):
                raise GasCityOpsError(
                    f"soak observation {number} {provider} receipt proof is invalid"
                )
            relative = Path(artifact["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise GasCityOpsError(f"soak observation {number} model path is unsafe")
            receipt_path = lock_root / relative
            if (
                _sha256(_regular_file_bytes(receipt_path, label=f"soak {provider} receipt"))
                != artifact["sha256"]
            ):
                raise GasCityOpsError(f"soak observation {number} model receipt drifted")
        for provider, artifact in latest_sessions.items():
            if (
                type(artifact) is not dict
                or set(artifact)
                != {
                    "path",
                    "sha256",
                    "recorded_at",
                    "age_seconds",
                    "evidence_id",
                    "session_id_sha256",
                    "git_broker_id",
                }
                or type(artifact.get("path")) is not str
                or type(artifact.get("sha256")) is not str
                or SHA256_RE.fullmatch(artifact["sha256"]) is None
                or type(artifact.get("age_seconds")) is not int
                or artifact["age_seconds"] < 0
                or artifact["age_seconds"] > SOAK_MAX_SESSION_RECEIPT_AGE_SECONDS
            ):
                raise GasCityOpsError(
                    f"soak observation {number} {provider} session proof is invalid"
                )
            relative = Path(artifact["path"])
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or len(relative.parts) != 8
                or relative.parts[:4] != ("runtime", "state", "git-broker", "rig-aegis")
                or SOAK_AGENT_RE.fullmatch(relative.parts[4]) is None
                or SOAK_SESSION_RE.fullmatch(relative.parts[5]) is None
                or relative.parts[6:] != ("model-evidence", "session-receipt.json")
            ):
                raise GasCityOpsError(
                    f"soak observation {number} {provider} session path is unsafe"
                )
            session_path = lock_root / relative
            session_content = _regular_file_bytes(
                session_path, label=f"soak {provider} host session receipt"
            )
            if _sha256(session_content) != artifact["sha256"]:
                raise GasCityOpsError(
                    f"soak observation {number} {provider} session receipt drifted"
                )
            session_value = _load_json_bytes(
                session_content, label=f"soak {provider} host session receipt"
            )
            if not isinstance(session_value, dict):
                raise GasCityOpsError(
                    f"soak observation {number} {provider} session receipt is invalid"
                )
            recorded = _validate_soak_session_receipt(
                session_value, provider=provider, lock=raw_lock
            )
            age = int((observed - recorded).total_seconds())
            if (
                age != artifact["age_seconds"]
                or _format_utc(recorded) != artifact.get("recorded_at")
                or session_value.get("evidence_id") != artifact.get("evidence_id")
                or session_value.get("session_id_sha256") != artifact.get("session_id_sha256")
                or session_value.get("git_broker_id") != artifact.get("git_broker_id")
            ):
                raise GasCityOpsError(
                    f"soak observation {number} {provider} session binding drifted"
                )
            distinct_sessions[provider].add(artifact["sha256"])
        if (
            type(beads) is not dict
            or set(beads)
            != {
                "target_directory",
                "dolt_main_head",
                "canonical_export_sha256",
                "record_count",
            }
            or type(beads.get("target_directory")) is not str
            or not Path(beads["target_directory"]).is_absolute()
            or type(beads.get("dolt_main_head")) is not str
            or re.fullmatch(r"[0-9a-v]{20,64}", beads["dolt_main_head"].lower()) is None
            or type(beads.get("canonical_export_sha256")) is not str
            or SHA256_RE.fullmatch(beads["canonical_export_sha256"]) is None
            or type(beads.get("record_count")) is not int
            or beads["record_count"] < 1
            or type(reconciliation) is not dict
            or set(reconciliation)
            != {
                "head_before",
                "head_after",
                "first_raw_export_sha256",
                "second_raw_export_sha256",
                "canonical_export_sha256",
            }
            or reconciliation.get("head_before") != beads["dolt_main_head"]
            or reconciliation.get("head_after") != beads["dolt_main_head"]
            or reconciliation.get("canonical_export_sha256") != beads["canonical_export_sha256"]
            or any(
                type(reconciliation.get(field)) is not str
                or SHA256_RE.fullmatch(reconciliation[field]) is None
                for field in (
                    "first_raw_export_sha256",
                    "second_raw_export_sha256",
                    "canonical_export_sha256",
                )
            )
        ):
            raise GasCityOpsError(f"soak observation {number} Beads proof is invalid")
        if (
            type(projection) is not dict
            or set(projection)
            != {
                "directory",
                "manifest_path",
                "manifest_sha256",
                "source_digest",
                "dolt_main_head",
            }
            or type(projection.get("directory")) is not str
            or type(projection.get("manifest_path")) is not str
            or Path(projection["directory"]).is_absolute()
            or Path(projection["manifest_path"]).is_absolute()
            or ".." in Path(projection["directory"]).parts
            or ".." in Path(projection["manifest_path"]).parts
            or Path(projection["manifest_path"])
            != Path(projection["directory"]) / ".aegis-vault.json"
            or type(projection.get("manifest_sha256")) is not str
            or SHA256_RE.fullmatch(projection["manifest_sha256"]) is None
            or projection.get("dolt_main_head") != beads["dolt_main_head"]
            or type(projection.get("source_digest")) is not str
            or SHA256_RE.fullmatch(projection["source_digest"]) is None
        ):
            raise GasCityOpsError(f"soak observation {number} projection proof is invalid")
        manifest_bytes, manifest = _validated_obsidian_manifest(
            lock_root / projection["directory"],
            expected_bd_sha256=str(expected_bd_sha256),
        )
        if (
            _sha256(manifest_bytes) != projection["manifest_sha256"]
            or manifest.get("source_digest") != projection["source_digest"]
            or manifest.get("task_dolt_main_head") != projection["dolt_main_head"]
        ):
            raise GasCityOpsError(f"soak observation {number} projection drifted")
        if (
            type(supervisor) is not dict
            or set(supervisor)
            != {
                "gc_binary_sha256",
                "pid",
                "socket_path",
                "checked_paths",
                "status_sha256",
            }
            or type(supervisor.get("gc_binary_sha256")) is not str
            or SHA256_RE.fullmatch(supervisor["gc_binary_sha256"]) is None
            or type(supervisor.get("pid")) is not int
            or supervisor["pid"] <= 0
            or type(supervisor.get("socket_path")) is not str
            or type(supervisor.get("checked_paths")) is not list
            or len(supervisor["checked_paths"]) != 2
            or len(set(supervisor["checked_paths"])) != 2
            or any(
                type(path) is not str or not Path(path).is_absolute()
                for path in supervisor["checked_paths"]
            )
            or supervisor["socket_path"] not in supervisor["checked_paths"]
            or not supervisor["checked_paths"][0].endswith("/gc/supervisor.sock")
            or not supervisor["checked_paths"][1].endswith("/.gc/supervisor.sock")
            or type(supervisor.get("status_sha256")) is not str
            or SHA256_RE.fullmatch(supervisor["status_sha256"]) is None
            or type(authority) is not dict
            or authority
            != {
                "receipt_sha256": expected_authority["receipt_sha256"],
                "history_record_sha256": expected_history_sha256,
            }
        ):
            raise GasCityOpsError(f"soak observation {number} runtime proof is invalid")
        if times and observed <= times[-1]:
            raise GasCityOpsError("soak observation timestamps must be strictly increasing")
        times.append(observed)
        previous_digest = _sha256(_canonical_soak_line(record))
    for provider, digests in distinct_sessions.items():
        if len(digests) < SOAK_MIN_DISTINCT_SESSION_RECEIPTS:
            raise GasCityOpsError(
                f"soak requires at least {SOAK_MIN_DISTINCT_SESSION_RECEIPTS} "
                f"distinct successful {provider} sessions"
            )
    if times[0] < started or times[-1] > ended:
        raise GasCityOpsError("soak observations fall outside the recorded soak interval")
    if (times[0] - started).total_seconds() > SOAK_BOUNDARY_TOLERANCE_SECONDS:
        raise GasCityOpsError("soak observations do not begin at the soak boundary")
    if (ended - times[-1]).total_seconds() > SOAK_BOUNDARY_TOLERANCE_SECONDS:
        raise GasCityOpsError("soak observations do not reach the soak boundary")
    gaps = [int((right - left).total_seconds()) for left, right in zip(times, times[1:])]
    maximum_gap = max(gaps, default=0)
    if maximum_gap > SOAK_MAX_OBSERVATION_GAP_SECONDS:
        raise GasCityOpsError("soak observations contain a monitoring gap longer than one hour")
    return len(records), maximum_gap


def _validate_soak_evidence(
    path: Path,
    value: Mapping[str, Any],
    *,
    lock_root: Path,
    canary_manifest_sha256: str,
    deep: bool,
) -> None:
    started = _utc_timestamp(value.get("started_at"), label="soak started_at")
    ended = _utc_timestamp(value.get("ended_at"), label="soak ended_at")
    duration = int((ended - started).total_seconds())
    live_authority, _ = _live_authority_binding(lock_root)
    if (
        set(value)
        != {
            "schema_version",
            "kind",
            "status",
            "started_at",
            "ended_at",
            "duration_seconds",
            "continuous",
            "anomalies",
            "runtime_lock_sha256",
            "canary_manifest_sha256",
            "authority",
            "start_receipt_path",
            "start_receipt_sha256",
            "observations_path",
            "observations_sha256",
            "observation_count",
            "maximum_gap_seconds",
        }
        or value.get("schema_version") != 1
        or value.get("kind") != "gas-city-soak"
        or value.get("status") != "pass"
        or duration < SOAK_MINIMUM_SECONDS
        or value.get("duration_seconds") != duration
        or value.get("canary_manifest_sha256") != canary_manifest_sha256
        or value.get("anomalies") != 0
        or value.get("continuous") is not True
        or value.get("authority") != live_authority
        or not isinstance(value.get("runtime_lock_sha256"), str)
        or SHA256_RE.fullmatch(str(value["runtime_lock_sha256"])) is None
        or not isinstance(value.get("start_receipt_sha256"), str)
        or SHA256_RE.fullmatch(str(value["start_receipt_sha256"])) is None
        or not isinstance(value.get("observations_sha256"), str)
        or SHA256_RE.fullmatch(str(value["observations_sha256"])) is None
    ):
        raise GasCityOpsError("soak evidence does not prove a continuous minimum 24-hour soak")
    if not deep:
        return
    for field, expected_digest in (
        ("start_receipt_path", value["start_receipt_sha256"]),
        ("observations_path", value["observations_sha256"]),
    ):
        raw = value.get(field)
        if not isinstance(raw, str) or Path(raw).is_absolute() or ".." in Path(raw).parts:
            raise GasCityOpsError(f"soak evidence {field} is unsafe")
        artifact_path = _canonical_path(lock_root / raw, must_exist=True, label=field)
        if not _is_within(artifact_path, lock_root):
            raise GasCityOpsError(f"soak evidence {field} escaped the runtime-lock directory")
        artifact = _regular_file_bytes(artifact_path, label=field)
        if _sha256(artifact) != expected_digest:
            raise GasCityOpsError(f"soak evidence {field} digest mismatch")
        if field == "observations_path":
            count, maximum_gap = _validate_soak_observations(
                artifact,
                started=started,
                ended=ended,
                expected_authority=live_authority,
                lock_root=lock_root,
            )
            if (
                value.get("observation_count") != count
                or value.get("maximum_gap_seconds") != maximum_gap
            ):
                raise GasCityOpsError("soak observation counts do not match the receipt")
        else:
            start_value = _load_json_bytes(artifact, label="soak start receipt")
            if (
                not isinstance(start_value, dict)
                or start_value.get("schema_version") != 1
                or start_value.get("kind") != "gas-city-soak-start"
                or start_value.get("status") != "running"
                or start_value.get("started_at") != value.get("started_at")
                or start_value.get("canary_manifest_sha256") != canary_manifest_sha256
                or start_value.get("runtime_lock_sha256") != value.get("runtime_lock_sha256")
                or start_value.get("authority") != live_authority
            ):
                raise GasCityOpsError("soak start receipt does not match the finish receipt")


def _validate_promotion_evidence(
    kind: str,
    path: Path,
    value: Mapping[str, Any],
    *,
    lock: Mapping[str, Any],
    lock_root: Path,
    canary_manifest_sha256: str,
    deep: bool,
    evidence_records: Mapping[str, Mapping[str, str]],
    snapshot_source_bytes: bytes | None,
) -> None:
    if kind == "backup":
        verified = verify_cold_dolt_backup(path, deep=deep)
        if verified["dolt_binary_sha256"] != lock["tools"]["dolt"]["binary_sha256"]:
            raise GasCityOpsError("cold backup was not captured with the locked Dolt binary")
    elif kind == "migration":
        _validate_migration_evidence(
            path,
            value,
            lock_root=lock_root,
            deep=deep,
            source_bytes=snapshot_source_bytes,
        )
    elif kind == "recovery":
        _validate_recovery_evidence(value, lock_root=lock_root, lock=lock)
    elif kind == "authority":
        _validated_authority_evidence(
            value,
            lock_root=lock_root,
            evidence_records=evidence_records,
        )
    elif kind == "provider":
        _validate_provider_evidence(value, lock, lock_root=lock_root)
    elif kind == "github":
        _validate_github_evidence(value, lock_root=lock_root, evidence_path=path)
    elif kind == "obsidian":
        _validate_obsidian_evidence(value, lock, lock_root=lock_root)
    elif kind == "canary":
        _validate_canary_evidence(
            value,
            lock_root=lock_root,
            evidence_path=path,
            evidence_records=evidence_records,
        )
    elif kind == "soak":
        _validate_soak_evidence(
            path,
            value,
            lock_root=lock_root,
            canary_manifest_sha256=canary_manifest_sha256,
            deep=deep,
        )
    else:  # pragma: no cover - caller set validation is exhaustive.
        raise GasCityOpsError(f"unsupported promotion evidence kind: {kind}")


def _promotion_record_shape(record: Any, *, label: str) -> None:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise GasCityOpsError(f"runtime lock {label} must contain exactly path and sha256")
    raw_path = record.get("path")
    digest = record.get("sha256")
    if (
        not isinstance(raw_path, str)
        or not raw_path
        or Path(raw_path).is_absolute()
        or ".." in Path(raw_path).parts
        or (
            digest is not None
            and (not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None)
        )
    ):
        raise GasCityOpsError(f"runtime lock {label} path or digest is invalid")


def _validate_promotion_manifest(
    lock_path: Path,
    lock: Mapping[str, Any],
    *,
    stage: str,
    deep: bool,
) -> dict[str, Any]:
    record = lock["promotion"][stage]
    path, _, value = _load_evidence_record(
        lock_path.parent,
        record,
        label=f"{stage} promotion manifest",
    )
    expected_kind = f"gas-city-{stage}-promotion"
    expected_evidence = (
        set(CANARY_EVIDENCE_KINDS) if stage == "canary" else set(PRODUCTION_EVIDENCE_KINDS)
    )
    evidence = value.get("evidence")
    provider_receipts = value.get("provider_receipts")
    locked_images = {
        name: image_record["image_id"] for name, image_record in lock["images"].items()
    }
    expected_provider_receipts = {
        name: provider["receipt_sha256"] for name, provider in lock["providers"].items()
    }
    if (
        value.get("schema_version") != PROMOTION_RECEIPT_SCHEMA_VERSION
        or value.get("kind") != expected_kind
        or value.get("status") != "pass"
        or not isinstance(value.get("source_lock_sha256"), str)
        or SHA256_RE.fullmatch(str(value["source_lock_sha256"])) is None
        or value.get("images") != locked_images
        or provider_receipts != expected_provider_receipts
        or not isinstance(evidence, dict)
        or set(evidence) != expected_evidence
    ):
        raise GasCityOpsError(f"{stage} promotion manifest is invalid")
    _utc_timestamp(value.get("promoted_at"), label=f"{stage} promoted_at")
    canary_digest = str(lock["promotion"]["canary"]["sha256"])
    if stage == "production" and value.get("canary_manifest_sha256") != canary_digest:
        raise GasCityOpsError("production manifest is not bound to the canary manifest")
    authority_path, _, authority_value = _load_evidence_record(
        lock_path.parent,
        evidence["authority"],
        label="authority promotion evidence",
    )
    del authority_path
    _, snapshot_source_bytes = _validated_authority_evidence(
        authority_value,
        lock_root=lock_path.parent,
        evidence_records=evidence,
    )
    for kind, evidence_record in evidence.items():
        evidence_path, _, evidence_value = _load_evidence_record(
            lock_path.parent,
            evidence_record,
            label=f"{kind} promotion evidence",
        )
        _validate_promotion_evidence(
            kind,
            evidence_path,
            evidence_value,
            lock=lock,
            lock_root=lock_path.parent,
            canary_manifest_sha256=canary_digest,
            deep=deep,
            evidence_records=evidence,
            snapshot_source_bytes=snapshot_source_bytes,
        )
    return value


def _validate_runtime_promotion_records(lock_path: Path, lock: Mapping[str, Any]) -> None:
    promotion = lock.get("promotion")
    if not isinstance(promotion, dict) or set(promotion) != {"canary", "production"}:
        raise GasCityOpsError("runtime lock promotion records are invalid")
    for stage in ("canary", "production"):
        _promotion_record_shape(promotion[stage], label=f"promotion.{stage}")
    status = lock["status"]
    canary_digest = promotion["canary"]["sha256"]
    production_digest = promotion["production"]["sha256"]
    if status in {"staged_pending_provisioning", "provisioned_pending_canary"}:
        if canary_digest is not None or production_digest is not None:
            raise GasCityOpsError("pre-canary runtime lock contains promoted evidence")
        return
    if not isinstance(canary_digest, str):
        raise GasCityOpsError("canary runtime lock lacks a canary promotion manifest")
    _validate_promotion_manifest(lock_path, lock, stage="canary", deep=False)
    if status == "canary_passed_soaking":
        if production_digest is not None:
            raise GasCityOpsError("soaking runtime lock contains production evidence")
        return
    if not isinstance(production_digest, str):
        raise GasCityOpsError("production runtime lock lacks production promotion evidence")
    _validate_promotion_manifest(lock_path, lock, stage="production", deep=False)


def _evidence_record_for_path(lock_root: Path, path: Path, *, label: str) -> dict[str, str]:
    relative = _relative_evidence_path(path, lock_root, label=label)
    content = _regular_file_bytes(lock_root / relative, label=label)
    value = _load_json_bytes(content, label=label)
    if not isinstance(value, dict):
        raise GasCityOpsError(f"{label} must contain one JSON object")
    return {"path": relative, "sha256": _sha256(content)}


def _write_or_reuse_promotion_manifest(
    path: Path,
    core: Mapping[str, Any],
    *,
    clock: Callable[[], dt.datetime],
) -> tuple[bytes, str]:
    if path.exists() or path.is_symlink():
        content = _regular_file_bytes(path, label="existing promotion manifest")
        value = _load_json_bytes(content, label="existing promotion manifest")
        if not isinstance(value, dict):
            raise GasCityOpsError("existing promotion manifest must contain one object")
        promoted_at = value.get("promoted_at")
        _utc_timestamp(promoted_at, label="existing promotion promoted_at")
        without_time = dict(value)
        without_time.pop("promoted_at", None)
        if without_time != dict(core):
            raise GasCityOpsError("existing append-only promotion manifest proves different inputs")
        return content, _sha256(content)
    value = {**core, "promoted_at": _format_utc(clock())}
    return _write_append_only_json(path, value)


def promote_canary_runtime(
    lock_path: Path,
    evidence_paths: Mapping[str, Path],
    *,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Bind all pre-soak evidence and advance the runtime to controlled soaking.

    The clock hook is test-only.  Production CLI callers always use real UTC.
    """

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_bytes = _regular_file_bytes(path, label="runtime lock")
    lock = load_runtime_lock(path)
    if lock["status"] == "canary_passed_soaking":
        _validate_promotion_manifest(path, lock, stage="canary", deep=True)
        return {"status": "already_canary_passed_soaking"}
    if lock["status"] != "provisioned_pending_canary":
        raise GasCityOpsError("canary promotion requires a provisioned runtime lock")
    if set(evidence_paths) != set(CANARY_EVIDENCE_KINDS):
        raise GasCityOpsError("canary promotion requires the exact pre-soak evidence set")

    provider_receipts = _verified_provider_receipts(path, lock)
    candidate = copy.deepcopy(lock)
    for provider, digest in provider_receipts.items():
        candidate["providers"][provider]["observed_model"] = candidate["providers"][provider][
            "requested_model"
        ]
        candidate["providers"][provider]["receipt_sha256"] = digest

    evidence: dict[str, dict[str, str]] = {}
    for kind in CANARY_EVIDENCE_KINDS:
        evidence[kind] = _evidence_record_for_path(
            path.parent,
            evidence_paths[kind],
            label=f"{kind} promotion evidence",
        )
    _, _, authority_value = _load_evidence_record(
        path.parent,
        evidence["authority"],
        label="authority promotion evidence",
    )
    _, snapshot_source_bytes = _validated_authority_evidence(
        authority_value,
        lock_root=path.parent,
        evidence_records=evidence,
    )
    for kind in CANARY_EVIDENCE_KINDS:
        record = evidence[kind]
        evidence_path, _, evidence_value = _load_evidence_record(
            path.parent,
            record,
            label=f"{kind} promotion evidence",
        )
        _validate_promotion_evidence(
            kind,
            evidence_path,
            evidence_value,
            lock=candidate,
            lock_root=path.parent,
            canary_manifest_sha256="pending",
            deep=True,
            evidence_records=evidence,
            snapshot_source_bytes=snapshot_source_bytes,
        )

    image_ids = {name: record["image_id"] for name, record in candidate["images"].items()}
    core = {
        "schema_version": PROMOTION_RECEIPT_SCHEMA_VERSION,
        "kind": "gas-city-canary-promotion",
        "status": "pass",
        "source_lock_sha256": _sha256(lock_bytes),
        "images": image_ids,
        "provider_receipts": provider_receipts,
        "evidence": evidence,
    }
    manifest_path = path.parent / str(candidate["promotion"]["canary"]["path"])
    _, manifest_digest = _write_or_reuse_promotion_manifest(
        manifest_path,
        core,
        clock=clock,
    )
    candidate["promotion"]["canary"]["sha256"] = manifest_digest
    candidate["status"] = "canary_passed_soaking"
    promoted = _replace_runtime_lock(
        path,
        expected_sha256=_sha256(lock_bytes),
        candidate=candidate,
    )
    _validate_promotion_manifest(path, promoted, stage="canary", deep=True)
    return {
        "status": "canary_passed_soaking",
        "canary_manifest_path": manifest_path.as_posix(),
        "canary_manifest_sha256": manifest_digest,
        "provider_receipts": provider_receipts,
        "runtime_lock_sha256": _sha256(_regular_file_bytes(path, label="runtime lock")),
    }


def _safe_evidence_output(lock_root: Path, output_path: Path, *, label: str) -> Path:
    destination = _canonical_path(output_path, must_exist=False, label=label)
    if not _is_within(destination, lock_root):
        raise GasCityOpsError(f"{label} must live beneath the runtime-lock directory")
    return destination


def start_soak(
    lock_path: Path,
    output_path: Path,
    *,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Create the immutable start boundary for the production soak."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(path, require_observed_models=True)
    if lock["status"] != "canary_passed_soaking":
        raise GasCityOpsError("soak may start only after canary promotion")
    destination = _safe_evidence_output(path.parent, output_path, label="soak start output")
    lock_bytes = _regular_file_bytes(path, label="runtime lock")
    authority_binding, _ = _live_authority_binding(path.parent)
    receipt = {
        "schema_version": 1,
        "kind": "gas-city-soak-start",
        "status": "running",
        "started_at": _format_utc(clock()),
        "runtime_lock_sha256": _sha256(lock_bytes),
        "canary_manifest_sha256": lock["promotion"]["canary"]["sha256"],
        "authority": authority_binding,
    }
    _, digest = _write_append_only_json(destination, receipt)
    return {
        **receipt,
        "receipt_path": destination.as_posix(),
        "receipt_sha256": digest,
    }


def finish_soak(
    lock_path: Path,
    start_receipt_path: Path,
    observations_path: Path,
    output_path: Path,
    *,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Finish a continuously observed soak after at least 24 real hours.

    ``clock`` is deliberately injectable only at the Python boundary for unit
    tests.  There is no CLI flag that can shorten or override the production
    interval.
    """

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock = load_runtime_lock(path, require_observed_models=True)
    if lock["status"] != "canary_passed_soaking":
        raise GasCityOpsError("soak may finish only while the canary is soaking")
    start_relative = _relative_evidence_path(
        start_receipt_path,
        path.parent,
        label="soak start receipt",
    )
    observations_relative = _relative_evidence_path(
        observations_path,
        path.parent,
        label="soak observations",
    )
    destination = _safe_evidence_output(path.parent, output_path, label="soak finish output")
    start_bytes = _regular_file_bytes(path.parent / start_relative, label="soak start receipt")
    if stat.S_IMODE((path.parent / start_relative).stat().st_mode) & 0o077:
        raise GasCityOpsError("soak start receipt must be owner-only")
    start = _load_json_bytes(start_bytes, label="soak start receipt")
    authority_binding, _ = _live_authority_binding(path.parent)
    if (
        not isinstance(start, dict)
        or start.get("schema_version") != 1
        or start.get("kind") != "gas-city-soak-start"
        or start.get("status") != "running"
        or start.get("canary_manifest_sha256") != lock["promotion"]["canary"]["sha256"]
        or start.get("runtime_lock_sha256")
        != _sha256(_regular_file_bytes(path, label="runtime lock"))
        or start.get("authority") != authority_binding
    ):
        raise GasCityOpsError("soak start receipt does not match the current canary")
    started = _utc_timestamp(start.get("started_at"), label="soak started_at")
    ended = clock()
    if ended.tzinfo is None or ended.utcoffset() != dt.timedelta(0):
        raise GasCityOpsError("clock returned a non-UTC time")
    ended = ended.replace(microsecond=0)
    duration = int((ended - started).total_seconds())
    if duration < SOAK_MINIMUM_SECONDS:
        raise GasCityOpsError("production soak has not reached the required 24 hours")
    observation_bytes, _ = _stable_read(
        path.parent / observations_relative,
        label="soak observations",
    )
    if stat.S_IMODE((path.parent / observations_relative).stat().st_mode) & 0o077:
        raise GasCityOpsError("soak observations must be owner-only")
    count, maximum_gap = _validate_soak_observations(
        observation_bytes,
        started=started,
        ended=ended,
        expected_authority=authority_binding,
        lock_root=path.parent,
    )
    receipt = {
        "schema_version": 1,
        "kind": "gas-city-soak",
        "status": "pass",
        "started_at": _format_utc(started),
        "ended_at": _format_utc(ended),
        "duration_seconds": duration,
        "continuous": True,
        "anomalies": 0,
        "runtime_lock_sha256": start["runtime_lock_sha256"],
        "canary_manifest_sha256": lock["promotion"]["canary"]["sha256"],
        "authority": authority_binding,
        "start_receipt_path": start_relative,
        "start_receipt_sha256": _sha256(start_bytes),
        "observations_path": observations_relative,
        "observations_sha256": _sha256(observation_bytes),
        "observation_count": count,
        "maximum_gap_seconds": maximum_gap,
    }
    _, digest = _write_append_only_json(destination, receipt)
    return {
        **receipt,
        "receipt_path": destination.as_posix(),
        "receipt_sha256": digest,
    }


def promote_runtime_production(
    lock_path: Path,
    soak_evidence_path: Path,
    *,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Re-verify every gate and atomically promote a soaked canary to production."""

    path = _canonical_path(lock_path, must_exist=True, label="runtime lock")
    lock_bytes = _regular_file_bytes(path, label="runtime lock")
    lock = load_runtime_lock(path, require_observed_models=True)
    if lock["status"] == "production":
        _validate_promotion_manifest(path, lock, stage="production", deep=True)
        return {"status": "already_production"}
    if lock["status"] != "canary_passed_soaking":
        raise GasCityOpsError("production promotion requires a successfully soaking canary")
    canary = _validate_promotion_manifest(path, lock, stage="canary", deep=True)
    evidence = copy.deepcopy(canary["evidence"])
    soak_record = _evidence_record_for_path(
        path.parent,
        soak_evidence_path,
        label="soak promotion evidence",
    )
    evidence["soak"] = soak_record
    _, _, authority_value = _load_evidence_record(
        path.parent,
        evidence["authority"],
        label="authority promotion evidence",
    )
    _, snapshot_source_bytes = _validated_authority_evidence(
        authority_value,
        lock_root=path.parent,
        evidence_records=evidence,
    )
    soak_path, _, soak_value = _load_evidence_record(
        path.parent,
        soak_record,
        label="soak promotion evidence",
    )
    _validate_promotion_evidence(
        "soak",
        soak_path,
        soak_value,
        lock=lock,
        lock_root=path.parent,
        canary_manifest_sha256=lock["promotion"]["canary"]["sha256"],
        deep=True,
        evidence_records=evidence,
        snapshot_source_bytes=snapshot_source_bytes,
    )
    if soak_value.get("runtime_lock_sha256") != _sha256(lock_bytes):
        raise GasCityOpsError("soak was not observed against the current pre-production lock")
    core = {
        "schema_version": PROMOTION_RECEIPT_SCHEMA_VERSION,
        "kind": "gas-city-production-promotion",
        "status": "pass",
        "source_lock_sha256": _sha256(lock_bytes),
        "canary_manifest_sha256": lock["promotion"]["canary"]["sha256"],
        "images": {name: record["image_id"] for name, record in lock["images"].items()},
        "provider_receipts": {
            name: record["receipt_sha256"] for name, record in lock["providers"].items()
        },
        "evidence": evidence,
    }
    manifest_path = path.parent / str(lock["promotion"]["production"]["path"])
    _, manifest_digest = _write_or_reuse_promotion_manifest(
        manifest_path,
        core,
        clock=clock,
    )
    candidate = copy.deepcopy(lock)
    candidate["promotion"]["production"]["sha256"] = manifest_digest
    candidate["status"] = "production"
    promoted = _replace_runtime_lock(
        path,
        expected_sha256=_sha256(lock_bytes),
        candidate=candidate,
    )
    _validate_promotion_manifest(path, promoted, stage="production", deep=True)
    return {
        "status": "production",
        "production_manifest_path": manifest_path.as_posix(),
        "production_manifest_sha256": manifest_digest,
        "runtime_lock_sha256": _sha256(_regular_file_bytes(path, label="runtime lock")),
    }


def _jsonl_records(content: bytes, *, label: str) -> list[dict[str, Any]]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise GasCityOpsError(f"{label} is not valid UTF-8") from exc
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            raise GasCityOpsError(f"{label}:{number}: blank JSONL line")
        value = _load_json_bytes(line.encode("utf-8"), label=f"{label}:{number}")
        if not isinstance(value, dict):
            raise GasCityOpsError(f"{label}:{number}: record must be an object")
        records.append(value)
    return records


def verify_model_transcript(
    provider: str,
    transcript_path: Path,
    *,
    expected_model: str,
    expected_effort: str | None = None,
) -> dict[str, Any]:
    """Create an exact, fail-closed model receipt from one provider transcript."""

    path = _canonical_path(transcript_path, must_exist=True, label="provider transcript")
    content = _regular_file_bytes(path, label="provider transcript")
    records = _jsonl_records(content, label="provider transcript")
    if provider not in {"claude", "codex"}:
        raise GasCityOpsError("provider must be claude or codex")

    observations: list[dict[str, str]] = []
    if provider == "claude":
        for number, record in enumerate(records, start=1):
            if record.get("subtype") == "model_refusal_fallback":
                raise GasCityOpsError(f"Claude fallback event observed at transcript line {number}")
            if record.get("type") != "assistant":
                continue
            message = record.get("message")
            if not isinstance(message, Mapping) or not isinstance(message.get("model"), str):
                raise GasCityOpsError(
                    f"Claude assistant event at transcript line {number} lacks a model"
                )
            model = str(message["model"])
            if model != expected_model:
                raise GasCityOpsError(f"Claude model mismatch at transcript line {number}: {model}")
            observations.append({"model": model})
    else:
        if expected_effort is None:
            raise GasCityOpsError("Codex verification requires expected_effort")
        for number, record in enumerate(records, start=1):
            if record.get("type") != "turn_context":
                continue
            payload = record.get("payload")
            if not isinstance(payload, Mapping) or not isinstance(payload.get("model"), str):
                raise GasCityOpsError(f"Codex turn_context at line {number} lacks a model")
            model = str(payload["model"])
            collaboration = payload.get("collaboration_mode")
            settings = collaboration.get("settings") if isinstance(collaboration, Mapping) else None
            effort = payload.get("effort") or payload.get("reasoning_effort")
            if effort is None and isinstance(settings, Mapping):
                effort = settings.get("reasoning_effort")
            if model != expected_model or effort != expected_effort:
                raise GasCityOpsError(
                    f"Codex receipt mismatch at line {number}: model={model!r}, effort={effort!r}"
                )
            observations.append({"model": model, "reasoning_effort": str(effort)})

    if not observations:
        raise GasCityOpsError(f"{provider} transcript contains no verifiable model observations")
    return {
        "schema_version": 1,
        "status": "verified",
        "provider": provider,
        "requested_model": expected_model,
        "observed_model": expected_model,
        "expected_model": expected_model,
        "expected_effort": expected_effort,
        "reasoning_effort": expected_effort,
        "observed_effort": expected_effort,
        "observations": len(observations),
        "transcript_sha256": _sha256(content),
        "observation_sha256": _sha256(
            (json.dumps(observations, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        ),
    }


def _canonical_jsonl(content: str, *, label: str) -> bytes:
    """Use the migration authority's exact Beads export canonicalization."""

    try:
        return taskmaster_beads._canonical_operational_export(
            content.encode("utf-8"),
            step=label,
        )
    except taskmaster_beads.OperationalMigrationError as exc:
        raise GasCityOpsError(f"{label} is invalid: {exc}") from exc


def _head_from_json(text: str, *, label: str) -> str:
    value = _load_json_bytes(text.encode("utf-8"), label=label)

    def walk(item: Any) -> str | None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key).lower() in {"head", "dolt_hashof('main')", 'dolt_hashof("main")'}:
                    if isinstance(child, str) and re.fullmatch(r"[0-9a-v]{20,64}", child.lower()):
                        return child
                found = walk(child)
                if found:
                    return found
        elif isinstance(item, list):
            for child in item:
                found = walk(child)
                if found:
                    return found
        return None

    result = walk(value)
    if result is None:
        raise GasCityOpsError(f"{label} does not contain a Dolt main head")
    return result


def _endpoint_environment(
    base: Mapping[str, str], endpoint: DoltEndpoint, password: str
) -> dict[str, str]:
    """Return an explicit Beads server environment for one scoped endpoint."""

    environment = dict(base)
    environment.update(
        {
            "BEADS_DOLT_SERVER_HOST": endpoint.host,
            "BEADS_DOLT_SERVER_PORT": str(endpoint.port),
            "BEADS_DOLT_SERVER_USER": endpoint.user,
            "BEADS_DOLT_SERVER_DATABASE": endpoint.database,
            "BD_BACKUP_ENABLED": "false",
            "BEADS_DOLT_PASSWORD": password,
        }
    )
    return environment


def _loopback_host(host: str) -> str:
    normalized = host.strip().lower().strip("[]")
    if normalized in {"localhost", "127.0.0.1", "::1"}:
        return "loopback"
    return normalized


def _docker_endpoint_binding(network_settings: Mapping[str, Any], endpoint: DoltEndpoint) -> bool:
    ports = network_settings.get("Ports")
    published = ports.get("3306/tcp") if type(ports) is dict else None
    return type(published) is list and any(
        type(binding) is dict
        and binding.get("HostPort") == str(endpoint.port)
        and _loopback_host(str(binding.get("HostIp", ""))) == "loopback"
        for binding in published
    )


def _docker_hardened_publisher(value: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    host = value.get("HostConfig")
    if type(host) is not dict:
        raise GasCityOpsError(f"{label} has no Docker host-security configuration")
    cap_drop = host.get("CapDrop")
    security_options = host.get("SecurityOpt")
    if (
        host.get("ReadonlyRootfs") is not True
        or cap_drop != ["ALL"]
        or type(security_options) is not list
        or "no-new-privileges:true" not in security_options
    ):
        raise GasCityOpsError(f"{label} must be read-only, capability-free, and no-new-privileges")
    return {
        "read_only_rootfs": True,
        "cap_drop": ["ALL"],
        "no_new_privileges": True,
    }


def _docker_dolt_server_identity(
    docker_binary: Path,
    container_name: str,
    endpoint: DoltEndpoint,
    *,
    runner: Runner,
    environment: Mapping[str, str],
    cwd: Path,
    expected_image_id: str,
    expected_relay_image_id: str | None = None,
    allow_relay: bool = False,
) -> dict[str, Any]:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", container_name) is None:
        raise GasCityOpsError("Dolt container name is invalid")
    if _loopback_host(endpoint.host) != "loopback":
        raise GasCityOpsError("restore drill endpoints must use the local loopback interface")
    docker = _canonical_path(docker_binary, must_exist=True, label="Docker binary")
    docker_bytes = _regular_file_bytes(docker, label="Docker binary")
    result = _checked(
        (docker.as_posix(), "inspect", "--type", "container", container_name),
        cwd=cwd,
        environment=environment,
        runner=runner,
    )
    inspected = _load_json_bytes(result.stdout.encode("utf-8"), label="Docker container inspect")
    if type(inspected) is not list or len(inspected) != 1 or type(inspected[0]) is not dict:
        raise GasCityOpsError("Docker container inspect did not return one container")
    value = inspected[0]
    container_id = value.get("Id")
    image_id = value.get("Image")
    observed_name = str(value.get("Name", "")).removeprefix("/")
    state = value.get("State")
    mounts = value.get("Mounts")
    network = value.get("NetworkSettings")
    if (
        type(container_id) is not str
        or re.fullmatch(r"[0-9a-f]{64}", container_id) is None
        or type(image_id) is not str
        or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", image_id) is None
        or observed_name != container_name
        or type(state) is not dict
        or state.get("Running") is not True
        or type(mounts) is not list
        or type(network) is not dict
    ):
        raise GasCityOpsError("Docker container identity is incomplete or not running")
    normalized_expected_image = expected_image_id.removeprefix("sha256:")
    normalized_image = image_id.removeprefix("sha256:")
    if (
        re.fullmatch(r"[0-9a-f]{64}", normalized_expected_image) is None
        or normalized_image != normalized_expected_image
    ):
        raise GasCityOpsError("Dolt container image does not match the runtime lock")
    matching_mounts = [
        mount
        for mount in mounts
        if type(mount) is dict and mount.get("Destination") == DOLT_DATA_MOUNT_DESTINATION
    ]
    if len(matching_mounts) != 1:
        raise GasCityOpsError("Dolt container does not have one exact data mount")
    mount = matching_mounts[0]
    mount_type = mount.get("Type")
    mount_source = mount.get("Source")
    mount_name = mount.get("Name") if mount_type == "volume" else None
    if (
        mount_type not in {"bind", "volume"}
        or type(mount_source) is not str
        or not Path(mount_source).is_absolute()
        or (
            mount_type == "volume"
            and (
                type(mount_name) is not str
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", mount_name) is None
            )
        )
    ):
        raise GasCityOpsError("Dolt container data-mount identity is invalid")
    matching_backup_mounts = [
        candidate
        for candidate in mounts
        if type(candidate) is dict
        and candidate.get("Type") == "bind"
        and type(candidate.get("Source")) is str
        and Path(candidate["Source"]).is_absolute()
        and candidate.get("Destination") == candidate.get("Source")
        and candidate.get("Destination") != DOLT_DATA_MOUNT_DESTINATION
    ]
    if len(matching_backup_mounts) != 1:
        raise GasCityOpsError("Dolt container does not have one exact backup mount")
    backup_mount = matching_backup_mounts[0]
    backup_source = backup_mount.get("Source")
    backup_destination = backup_mount.get("Destination")
    backup_rw = backup_mount.get("RW")
    if (
        backup_mount.get("Type") != "bind"
        or type(backup_source) is not str
        or not Path(backup_source).is_absolute()
        or backup_destination != backup_source
        or type(backup_rw) is not bool
    ):
        raise GasCityOpsError("Dolt container backup-mount identity is invalid")
    endpoint_record = {"host": "loopback", "port": endpoint.port}
    if _docker_endpoint_binding(network, endpoint):
        publisher = {
            "mode": "direct",
            "container_name": container_name,
            "container_id": container_id,
            "image_id": normalized_image,
            "published_endpoint": endpoint_record,
            "target_container_id": container_id,
            "target_service": None,
            "shared_networks": [],
            **_docker_hardened_publisher(value, label="Dolt endpoint publisher"),
            "command": None,
        }
    else:
        if not allow_relay:
            raise GasCityOpsError(
                "Dolt endpoint is not published directly by the inspected container"
            )
        if not container_name.startswith("gas-city-") or not container_name.endswith("-dolt"):
            raise GasCityOpsError("relay-backed Dolt container name is not canonical")
        relay_name = f"{container_name}-loopback"
        relay_result = _checked(
            (docker.as_posix(), "inspect", "--type", "container", relay_name),
            cwd=cwd,
            environment=environment,
            runner=runner,
        )
        relay_inspected = _load_json_bytes(
            relay_result.stdout.encode("utf-8"),
            label="Docker loopback relay inspect",
        )
        if (
            type(relay_inspected) is not list
            or len(relay_inspected) != 1
            or type(relay_inspected[0]) is not dict
        ):
            raise GasCityOpsError("Docker relay inspect did not return one container")
        relay = relay_inspected[0]
        relay_id = relay.get("Id")
        relay_image = relay.get("Image")
        relay_state = relay.get("State")
        relay_network = relay.get("NetworkSettings")
        relay_config = relay.get("Config")
        normalized_expected_relay = (expected_relay_image_id or "").removeprefix("sha256:")
        normalized_relay_image = (
            relay_image.removeprefix("sha256:") if type(relay_image) is str else ""
        )
        target_service = container_name.removeprefix("gas-city-")
        rig = target_service.removesuffix("-dolt")
        expected_network = f"gas-city-{rig}-control"
        source_networks = network.get("Networks")
        relay_networks = relay_network.get("Networks") if type(relay_network) is dict else None
        shared_networks = sorted(set(source_networks or {}).intersection(set(relay_networks or {})))
        expected_command = [
            "/usr/bin/socat",
            "TCP4-LISTEN:3306,reuseaddr,fork,nodelay",
            f"TCP4:{target_service}:3306,nodelay",
        ]
        if (
            type(relay_id) is not str
            or re.fullmatch(r"[0-9a-f]{64}", relay_id) is None
            or re.fullmatch(r"[0-9a-f]{64}", normalized_expected_relay) is None
            or normalized_relay_image != normalized_expected_relay
            or str(relay.get("Name", "")).removeprefix("/") != relay_name
            or type(relay_state) is not dict
            or relay_state.get("Running") is not True
            or type(relay_network) is not dict
            or not _docker_endpoint_binding(relay_network, endpoint)
            or type(relay_config) is not dict
            or relay_config.get("Cmd") != expected_command
            or shared_networks != [expected_network]
            or any(
                type(mount) is dict and mount.get("Destination") == DOLT_DATA_MOUNT_DESTINATION
                for mount in relay.get("Mounts", [])
            )
        ):
            raise GasCityOpsError("Dolt endpoint relay is not the exact locked loopback path")
        publisher = {
            "mode": "relay",
            "container_name": relay_name,
            "container_id": relay_id,
            "image_id": normalized_relay_image,
            "published_endpoint": endpoint_record,
            "target_container_id": container_id,
            "target_service": target_service,
            "shared_networks": shared_networks,
            **_docker_hardened_publisher(relay, label="Dolt loopback relay"),
            "command": expected_command,
        }
    return {
        "container_name": container_name,
        "container_id": container_id,
        "image_id": normalized_image,
        "running": True,
        "published_endpoint": endpoint_record,
        "endpoint_publisher": publisher,
        "data_mount": {
            "type": mount_type,
            "source": mount_source,
            "name": mount_name,
            "destination": DOLT_DATA_MOUNT_DESTINATION,
        },
        "backup_mount": {
            "type": "bind",
            "source": backup_source,
            "name": None,
            "destination": backup_destination,
            "read_write": backup_rw,
        },
        "docker_binary_sha256": _sha256(docker_bytes),
    }


def _native_backup_manifest_bytes(entries: Sequence[Mapping[str, Any]]) -> bytes:
    return (
        json.dumps(
            {
                "schema_version": NATIVE_BACKUP_MANIFEST_SCHEMA_VERSION,
                "kind": "dolt-native-backup-file-manifest",
                "entries": list(entries),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def native_backup_restore_drill(
    source_repo: Path,
    restore_repo: Path,
    backup_dir: Path,
    *,
    lock_path: Path,
    locked_toolchain: Mapping[str, Any],
    source_endpoint: DoltEndpoint,
    restore_endpoint: DoltEndpoint,
    bd_binary: Path,
    docker_binary: Path,
    source_container: str,
    restore_container: str,
    source_password: str,
    restore_password: str,
    runner: Runner = _default_runner,
    base_environment: Mapping[str, str] | None = None,
    clock: Callable[[], dt.datetime] = _utc_now,
) -> dict[str, Any]:
    """Sync a Dolt-native backup and prove it on a separate server/database.

    The restore endpoint is required to use a different running container and
    data mount from the source. A second database or a differently spelled
    loopback address on the source server does not prove recovery from server
    or volume loss.
    Passwords are injected only through ``BEADS_DOLT_PASSWORD`` and are
    redacted from bounded command failures.
    """

    source_endpoint.validate(label="source endpoint")
    restore_endpoint.validate(label="restore endpoint")
    if (
        source_endpoint.host == restore_endpoint.host
        and source_endpoint.port == restore_endpoint.port
    ):
        raise GasCityOpsError("restore endpoint must use a distinct server from the source")
    source = _canonical_path(source_repo, must_exist=True, label="source repository")
    restore = _canonical_path(restore_repo, must_exist=True, label="restore repository")
    backup = _canonical_path(backup_dir, must_exist=False, label="backup directory")
    binary = _canonical_path(bd_binary, must_exist=True, label="bd binary")
    _regular_file_bytes(binary, label="bd binary")
    toolchain = validate_locked_operation_toolchain_evidence(lock_path, locked_toolchain)
    runtime_lock = load_runtime_lock(lock_path, _validate_promotions=False)
    if binary.as_posix() != toolchain["tools"]["bd"]["path"]:
        raise GasCityOpsError("restore drill must use the lock-bound city/bin/bd")
    if source == restore or any(
        _is_within(left, right) or _is_within(right, left)
        for left, right in ((source, restore), (backup, source), (backup, restore))
    ):
        raise GasCityOpsError("source, restore, and backup paths must be disjoint")
    if not (source / ".beads").is_dir():
        raise GasCityOpsError("source repository is not initialized for Beads")
    if (restore / ".beads").exists() or (restore / ".beads").is_symlink():
        raise GasCityOpsError("restore repository must not already contain .beads")
    if not source_password or not restore_password:
        raise GasCityOpsError("both Dolt endpoint passwords are required")

    base = dict(os.environ if base_environment is None else base_environment)
    source_env = _endpoint_environment(base, source_endpoint, source_password)
    restore_env = _endpoint_environment(base, restore_endpoint, restore_password)
    secrets = (source_password, restore_password)
    bd = binary.as_posix()
    source_server = _docker_dolt_server_identity(
        docker_binary,
        source_container,
        source_endpoint,
        runner=runner,
        environment=base,
        cwd=source,
        expected_image_id=runtime_lock["images"]["dolt_server"]["image_id"],
        expected_relay_image_id=runtime_lock["images"]["egress_proxy"]["image_id"],
        allow_relay=True,
    )
    restore_server = _docker_dolt_server_identity(
        docker_binary,
        restore_container,
        restore_endpoint,
        runner=runner,
        environment=base,
        cwd=restore,
        expected_image_id=runtime_lock["images"]["dolt_server"]["image_id"],
        allow_relay=False,
    )
    if source_server["container_id"] == restore_server["container_id"]:
        raise GasCityOpsError("restore drill containers must be distinct")
    source_mount = source_server["data_mount"]
    restore_mount = restore_server["data_mount"]
    if (
        source_mount["type"],
        source_mount["source"],
        source_mount["name"],
    ) == (
        restore_mount["type"],
        restore_mount["source"],
        restore_mount["name"],
    ):
        raise GasCityOpsError("restore drill data mounts must be distinct")
    source_backup_mount = source_server["backup_mount"]
    restore_backup_mount = restore_server["backup_mount"]
    backup_mount_root = _canonical_path(
        Path(source_backup_mount["source"]),
        must_exist=True,
        label="native backup mount root",
    )
    if (
        source_backup_mount["type"] != "bind"
        or restore_backup_mount["type"] != "bind"
        or source_backup_mount["source"] != restore_backup_mount["source"]
        or source_backup_mount["destination"] != source_backup_mount["source"]
        or restore_backup_mount["destination"] != restore_backup_mount["source"]
        or source_backup_mount["read_write"] is not True
        or restore_backup_mount["read_write"] is not False
        or not _is_within(backup, backup_mount_root)
        or backup == backup_mount_root
    ):
        raise GasCityOpsError(
            "restore drill requires one shared source-writable, restore-read-only backup mount"
        )
    try:
        backup_relative = backup.relative_to(backup_mount_root)
    except ValueError as exc:  # pragma: no cover - guarded by _is_within.
        raise GasCityOpsError("native backup path escaped its shared mount") from exc
    server_backup = Path(source_backup_mount["destination"]) / backup_relative

    _checked(
        (
            bd,
            "--json",
            "-C",
            source.as_posix(),
            "backup",
            "init",
            server_backup.as_posix(),
        ),
        cwd=source,
        environment=source_env,
        runner=runner,
        secrets=secrets,
    )
    _checked(
        (bd, "--json", "-C", source.as_posix(), "backup", "sync"),
        cwd=source,
        environment=source_env,
        runner=runner,
        secrets=secrets,
    )
    backup_entries = _file_tree_manifest(backup, label="Dolt native backup")
    backup_manifest_bytes = _native_backup_manifest_bytes(backup_entries)
    backup_manifest_path = backup.parent / f"{backup.name}{NATIVE_BACKUP_MANIFEST_SUFFIX}"
    _atomic_write(
        backup_manifest_path,
        backup_manifest_bytes,
        mode=0o600,
        exclusive=True,
    )
    captured_at = _format_utc(clock())
    status = _checked(
        (bd, "--json", "-C", source.as_posix(), "backup", "status"),
        cwd=source,
        environment=source_env,
        runner=runner,
        secrets=secrets,
    )
    source_head_result = _checked(
        (
            bd,
            "--json",
            "--readonly",
            "-C",
            source.as_posix(),
            "sql",
            "SELECT DOLT_HASHOF('main') AS head",
        ),
        cwd=source,
        environment=source_env,
        runner=runner,
        secrets=secrets,
    )
    source_export = _checked(
        (bd, "--readonly", "-C", source.as_posix(), "export", "--all"),
        cwd=source,
        environment=source_env,
        runner=runner,
        secrets=secrets,
    )

    _checked(
        (
            bd,
            "--json",
            "init",
            "--server",
            "--external",
            "--server-host",
            restore_endpoint.host,
            "--server-port",
            str(restore_endpoint.port),
            "--server-user",
            restore_endpoint.user,
            "--database",
            restore_endpoint.database,
            "--prefix",
            "restore",
            "--skip-agents",
            "--skip-hooks",
            "--non-interactive",
        ),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )
    empty_head_result = _checked(
        (
            bd,
            "--json",
            "--readonly",
            "-C",
            restore.as_posix(),
            "sql",
            "SELECT DOLT_HASHOF('main') AS head",
        ),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )
    empty_export = _checked(
        (bd, "--readonly", "-C", restore.as_posix(), "export", "--all"),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )
    empty_canonical = _canonical_jsonl(
        empty_export.stdout,
        label="empty restore-target Beads export",
    )
    if empty_canonical:
        raise GasCityOpsError("restore target database is not empty before restore")
    empty_head = _head_from_json(empty_head_result.stdout, label="empty restore Dolt head")
    _checked(
        (
            bd,
            "--json",
            "-C",
            restore.as_posix(),
            "backup",
            "restore",
            server_backup.as_posix(),
            "--force",
        ),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )
    restored_head_result = _checked(
        (
            bd,
            "--json",
            "--readonly",
            "-C",
            restore.as_posix(),
            "sql",
            "SELECT DOLT_HASHOF('main') AS head",
        ),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )
    restored_export = _checked(
        (bd, "--readonly", "-C", restore.as_posix(), "export", "--all"),
        cwd=restore,
        environment=restore_env,
        runner=runner,
        secrets=secrets,
    )

    source_head = _head_from_json(source_head_result.stdout, label="source Dolt head")
    restored_head = _head_from_json(restored_head_result.stdout, label="restored Dolt head")
    source_canonical = _canonical_jsonl(source_export.stdout, label="source Beads export")
    restored_canonical = _canonical_jsonl(restored_export.stdout, label="restored Beads export")
    if source_head != restored_head:
        raise GasCityOpsError(
            f"native restore Dolt head mismatch: source={source_head}, restored={restored_head}"
        )
    if source_canonical != restored_canonical:
        raise GasCityOpsError("native restore canonical Beads export mismatch")
    status_value = _load_json_bytes(status.stdout.encode("utf-8"), label="backup status")
    verified_at = _format_utc(clock())
    if _utc_timestamp(verified_at, label="recovery verified_at") < _utc_timestamp(
        captured_at,
        label="recovery captured_at",
    ):
        raise GasCityOpsError("recovery clock moved backwards during restore verification")
    return {
        "schema_version": NATIVE_RESTORE_SCHEMA_VERSION,
        "kind": "dolt-native-restore-drill",
        "status": "pass",
        "captured_at": captured_at,
        "verified_at": verified_at,
        "backup_path": backup.as_posix(),
        "backup_server_path": server_backup.as_posix(),
        "backup_manifest_path": backup_manifest_path.as_posix(),
        "backup_manifest_sha256": _sha256(backup_manifest_bytes),
        "source_endpoint": dataclasses.asdict(source_endpoint),
        "restore_endpoint": dataclasses.asdict(restore_endpoint),
        "source_server": source_server,
        "restore_server": restore_server,
        "restore_preflight": {
            "empty_issue_count": 0,
            "empty_export_sha256": _sha256(empty_canonical),
            "dolt_head": empty_head,
        },
        "dolt_head": source_head,
        "canonical_export_sha256": _sha256(source_canonical),
        "backup_status": status_value,
        "locked_toolchain": toolchain,
        "secrets_included": False,
    }
