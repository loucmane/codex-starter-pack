#!/usr/bin/env python3
"""Launch one provider and fail closed unless its transcript proves the model."""

from __future__ import annotations

import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import tomllib
import types
from typing import Any, Mapping


TASK_AUTHORITY_RUNTIME_PATH = Path("/opt/gas-city/task-authority.py")
AEGIS_POLECAT_STARTUP_PATH = Path("/opt/gas-city/aegis-polecat-startup.py")
AEGIS_RUNTIME_ARTIFACT_PATH = Path("/opt/gas-city/aegis-runtime.whl")
AEGIS_RUNTIME_SHIM_PATH = Path("/opt/gas-city/aegis-runtime-shim.py")
AEGIS_POLECAT_STARTUP_RECEIPT_PATH = Path(
    "/run/gas-city/aegis-startup-receipt.json"
)
AEGIS_GIT_BROKER_RECEIPT_PATH = Path("/run/gas-city-trusted/git-broker.json")
AEGIS_PRIVATE_GIT_DIR = Path("/run/gas-city-git/private.git")
AEGIS_POLECAT_STARTUP_MAX_BYTES = 1024 * 1024
AEGIS_RUNTIME_ARTIFACT_MAX_BYTES = 32 * 1024 * 1024
AEGIS_RUNTIME_SHIM_MAX_BYTES = 256 * 1024
AEGIS_POLECAT_STARTUP_NO_WORK_EXIT = 75
AEGIS_POLECAT_TEMPLATE = "aegis/gastown.polecat"
AEGIS_LOCAL_LAUNCHER_REL = Path(".aegis/bin/aegis")
AEGIS_LOCAL_LAUNCHER_CONTENT = (
    b"#!/bin/sh\n"
    b"set -eu\n"
    b'exec /usr/bin/python3 -I /opt/gas-city/aegis-runtime-shim.py "$@"\n'
)
TASK_AUTHORITY_RUNTIME_UID = 0
TASK_AUTHORITY_RUNTIME_MODE = 0o444
TASK_AUTHORITY_RECEIPT_PATH = Path("/run/gas-city/authority/aegis.json")
TASK_AUTHORITY_REQUIRED_GENERATION = 2
TASK_AUTHORITY_MAX_RUNTIME_BYTES = 512 * 1024
TASK_AUTHORITY_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID_RE = re.compile(r"[0-9a-f]{40}\Z")
AEGIS_BEAD_ID_RE = re.compile(r"ags-[A-Za-z0-9][A-Za-z0-9._-]{0,126}\Z")
MAX_SECRET_BYTES = 64 * 1024
MAX_PROVIDER_CREDENTIAL_BYTES = 1024 * 1024
WORKER_HOME_PATH = Path("/home/worker")
PROVIDER_HOME_PATH = Path("/run/gas-city/provider-home")
PROVIDER_CONFIG_PATH = Path("/run/gas-city/provider-config")
PROVIDER_SESSION_PATH = Path("/run/gas-city/provider-session")
PROVIDER_SYNC_RECEIPT_PATH = Path("/run/gas-city/provider-auth-sync.json")
MODEL_RECEIPT_PATH = Path("/run/gas-city/model-receipt.json")
MODEL_EVIDENCE_SOCKET_PATH = Path(
    "/run/gas-city-trusted/model-evidence.sock"
)
MODEL_EVIDENCE_MAX_BYTES = 1024 * 1024
CODEX_PREFLIGHT_MODEL_CATALOG_PATH = Path(
    "/opt/gas-city/codex-preflight-models.json"
)
CODEX_PREFLIGHT_MODEL_CATALOG_SHA256 = (
    "1487260f5deb22b5da6c3d306ae06444fc207b69881440dcc010cacb029f419c"
)
CODEX_PREFLIGHT_FEATURES_DISABLED = (
    "apps",
    "auth_elicitation",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "code_mode_host",
    "computer_use",
    "default_mode_request_user_input",
    "fast_mode",
    "goals",
    "guardian_approval",
    "hooks",
    "image_generation",
    "in_app_browser",
    "mentions_v2",
    "multi_agent",
    "personality",
    "plugin_sharing",
    "plugins",
    "remote_compaction_v2",
    "remote_plugin",
    "shell_snapshot",
    "shell_tool",
    "skill_mcp_dependency_install",
    "tool_call_mcp_elicitation",
    "tool_suggest",
    "unified_exec",
    "workspace_dependencies",
)
CODEX_PREFLIGHT_ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}
CODEX_SERVER_MODEL_MATCH_RE = re.compile(
    rb"codex_core::session:\s+server reported model "
    rb"([A-Za-z0-9][A-Za-z0-9._-]{0,127}) \(matches requested model\)"
)
PASSWORD_SECRET_PATH = Path("/run/secrets/beads_password")
AEGIS_PASSWORD_SECRET_PATH = Path("/run/secrets/aegis_beads_password")
GITHUB_SECRET_PATH = Path("/run/secrets/github_token")
GITHUB_DELIVERY_RECEIPT_PATH = Path(
    "/run/gas-city-trusted/github-delivery-receipt.json"
)
GITHUB_DELIVERY_REPOSITORY = "loucmane/codex-starter-pack"
GITHUB_DELIVERY_PERMISSIONS = {
    "contents": "write",
    "metadata": "read",
    "pull_requests": "write",
}
GITHUB_REQUIRED_DEFAULT_RULES = {
    "deletion",
    "non_fast_forward",
    "pull_request",
    "required_status_checks",
}
HOST_CITY_CONFIG_PATH = Path("/run/gas-city/host-city.toml")
IMAGE_WORKER_CITY_CONFIG_PATH = Path("/opt/gas-city/city.worker.toml")
HQ_CONFIG_OVERLAY_PATH = Path("/run/gas-city/hq-config.yaml")
AEGIS_CONFIG_OVERLAY_PATH = Path("/run/gas-city/aegis-config.yaml")
AEGIS_METADATA_OVERLAY_PATH = Path("/run/gas-city/aegis-metadata.json")
WORKER_BOUNDARY_RECEIPT_PATH = Path("/run/gas-city/worker-boundary.json")
DOLT_CREDENTIALS_PATH = Path("/home/worker/.config/beads/credentials")
MAX_CITY_CONFIG_BYTES = 512 * 1024
MAX_BEADS_BOUNDARY_BYTES = 64 * 1024
IMAGE_ROOT_UID = 0
DOLT_PASSWORD_RE = re.compile(r"[A-Za-z0-9._~!@%+=:-]{32,128}\Z")
SAFE_PROJECT_ID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
PROVIDER_LAYOUTS = {
    "codex": {
        "stable_credential": "auth.json",
        "home_directory": ".codex",
        "home_credential": "auth.json",
        "overlays": ("sessions", "log", "shell_snapshots"),
        "transcript": "sessions",
    },
    "claude": {
        "stable_credential": "credentials.json",
        "home_directory": ".claude",
        "home_credential": ".credentials.json",
        "overlays": ("projects", "debug", "todos"),
        "transcript": "projects",
    },
}
AEGIS_RUNTIME_IDENTITY = {
    "GC_CITY_ROOT": "/home/loucmane/gas-city",
    "GC_RIG": "aegis",
    "GC_RIG_ROOT": "/home/loucmane/codex",
    "GC_BEADS_PREFIX": "ags",
    "GC_DOLT_HOST": "gas-city-aegis-dolt",
    "GC_DOLT_PORT": "3306",
    "GC_DOLT_USER": "aegis_beads",
    "GC_DOLT_DATABASE": "aegis_beads",
    "BEADS_DOLT_SERVER_HOST": "gas-city-aegis-dolt",
    "BEADS_DOLT_SERVER_PORT": "3306",
    "BEADS_DOLT_SERVER_USER": "aegis_beads",
    "BEADS_DOLT_SERVER_DATABASE": "aegis_beads",
    "BEADS_CREDENTIALS_FILE": str(DOLT_CREDENTIALS_PATH),
    "BEADS_DIR": "/home/loucmane/codex/.beads",
    "GC_WORKER_BOUNDARY_ROLE": "aegis",
    "GC_HOST_CITY_CONFIG": str(HOST_CITY_CONFIG_PATH),
    "GC_IMAGE_WORKER_CITY_CONFIG": str(IMAGE_WORKER_CITY_CONFIG_PATH),
    "GC_AEGIS_CONFIG_OVERLAY": str(AEGIS_CONFIG_OVERLAY_PATH),
    "GC_AEGIS_METADATA_OVERLAY": str(AEGIS_METADATA_OVERLAY_PATH),
    "GC_GITHUB_REQUIRED": "true",
    "GC_GITHUB_TOKEN_FILE": "/run/secrets/github_token",
}
HQ_RUNTIME_IDENTITY = {
    "GC_CITY_ROOT": "/home/loucmane/gas-city",
    "GC_DOLT_HOST": "gas-city-hq-dolt",
    "GC_DOLT_PORT": "3306",
    "GC_DOLT_USER": "gas_city_hq",
    "GC_DOLT_DATABASE": "hq",
    "BEADS_DOLT_SERVER_HOST": "gas-city-hq-dolt",
    "BEADS_DOLT_SERVER_PORT": "3306",
    "BEADS_DOLT_SERVER_USER": "gas_city_hq",
    "BEADS_DOLT_SERVER_DATABASE": "hq",
    "BEADS_CREDENTIALS_FILE": str(DOLT_CREDENTIALS_PATH),
    "BEADS_DIR": "/home/loucmane/gas-city/.beads",
    "GC_HOST_CITY_CONFIG": str(HOST_CITY_CONFIG_PATH),
    "GC_IMAGE_WORKER_CITY_CONFIG": str(IMAGE_WORKER_CITY_CONFIG_PATH),
    "GC_HQ_CONFIG_OVERLAY": str(HQ_CONFIG_OVERLAY_PATH),
    "GC_GITHUB_REQUIRED": "false",
}
CUSTOM_TYPES = (
    "molecule,convoy,message,event,gate,merge-request,agent,role,rig,session,"
    "spec,convergence,step"
)
HQ_CONFIG_OVERLAY_CONTENT = (
    "issue_prefix: gc\n"
    "issue-prefix: gc\n"
    "dolt.auto-start: false\n"
    "dolt.host: gas-city-hq-dolt\n"
    "dolt.port: 3306\n"
    "dolt.user: gas_city_hq\n"
    "dolt:\n"
    "  disable-event-flush: true\n"
    "export.auto: false\n"
    "backup.enabled: false\n"
    "gc.endpoint_origin: city_canonical\n"
    "gc.endpoint_status: verified\n"
    f"types.custom: {CUSTOM_TYPES}\n"
).encode("utf-8")
AEGIS_CONFIG_OVERLAY_CONTENT = (
    "issue_prefix: ags\n"
    "issue-prefix: ags\n"
    "dolt.auto-start: false\n"
    "dolt.host: gas-city-aegis-dolt\n"
    "dolt.port: 3306\n"
    "dolt.user: aegis_beads\n"
    "dolt:\n"
    "  disable-event-flush: true\n"
    "export.auto: false\n"
    "backup.enabled: false\n"
    "gc.endpoint_origin: explicit\n"
    "gc.endpoint_status: verified\n"
    f"types.custom: {CUSTOM_TYPES}\n"
).encode("utf-8")


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"missing required worker identity environment: {name}")
    return value


def _secure_directory(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} is missing or unreadable") from exc
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise RuntimeError(f"{label} must be one owner-only real directory")


def _exact_directory_entries(path: Path, expected: set[str], label: str) -> None:
    _secure_directory(path, label)
    try:
        observed = {entry.name for entry in path.iterdir()}
    except OSError as exc:
        raise RuntimeError(f"could not inspect {label}") from exc
    if observed != expected:
        raise RuntimeError(f"{label} has unexpected or missing artifacts")


def _secure_read(
    path: Path,
    label: str,
    *,
    maximum_bytes: int,
    allowed_modes: set[int],
    allowed_uids: set[int] | None = None,
) -> bytes:
    """Read one non-symlink file through a verified descriptor without TOCTOU."""

    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production workers are Linux.
        raise RuntimeError(f"{label} cannot be opened without symlink protection")
    flags = os.O_RDONLY | os.O_CLOEXEC | no_follow
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"{label} must be one readable non-symlink file") from exc
    try:
        before = os.fstat(descriptor)
        mode = stat.S_IMODE(before.st_mode)
        owners = allowed_uids if allowed_uids is not None else {os.geteuid()}
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid not in owners
            or mode not in allowed_modes
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > maximum_bytes
        ):
            raise RuntimeError(f"{label} has unsafe ownership, mode, links, or size")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
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
    if (
        identity_before != identity_after
        or len(content) != after.st_size
        or len(content) > maximum_bytes
    ):
        raise RuntimeError(f"{label} changed while it was read")
    return content


def _strict_json_object(content: bytes, label: str) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise RuntimeError(f"{label} contains duplicate JSON keys")
            result[key] = value
        return result

    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                RuntimeError(f"{label} contains a non-finite JSON value: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict) or not value:
        raise RuntimeError(f"{label} must contain one non-empty JSON object")
    return value


def _provider_credential(path: Path, label: str) -> tuple[bytes, str]:
    content = _secure_read(
        path,
        label,
        maximum_bytes=MAX_PROVIDER_CREDENTIAL_BYTES,
        allowed_modes={0o600},
    )
    _strict_json_object(content, label)
    return content, hashlib.sha256(content).hexdigest()


def _secret_text(path: Path, label: str, *, minimum: int, maximum: int) -> str:
    content = _secure_read(
        path,
        label,
        maximum_bytes=MAX_SECRET_BYTES,
        allowed_modes={0o400, 0o600},
    )
    try:
        value = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8 text") from exc
    if value.endswith("\n"):
        value = value[:-1]
    if not minimum <= len(value) <= maximum or any(
        character.isspace() or character == "\x00" for character in value
    ):
        raise RuntimeError(f"{label} has an invalid secret shape")
    return value


def _city_config(content: bytes, label: str) -> dict[str, Any]:
    try:
        value = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(f"{label} is not strict UTF-8 TOML") from exc
    return value


def _one_aegis_rig(city: dict[str, Any], label: str) -> dict[str, Any]:
    rigs = city.get("rigs")
    if not isinstance(rigs, list):
        raise RuntimeError(f"{label} does not define a rigs array")
    matches = [rig for rig in rigs if isinstance(rig, dict) and rig.get("name") == "aegis"]
    if len(matches) != 1:
        raise RuntimeError(f"{label} does not define exactly one Aegis rig")
    return matches[0]


def _normalize_city_endpoints(
    city: dict[str, Any], label: str, *, worker: bool
) -> dict[str, Any]:
    # JSON round-tripping gives a deep copy for TOML's scalar/list/dict value
    # domain without retaining aliases that could mask a comparison change.
    value = json.loads(json.dumps(city))
    dolt = value.get("dolt")
    if not isinstance(dolt, dict):
        raise RuntimeError(f"{label} is missing the city Dolt table")
    hq_endpoint = (
        ("gas-city-hq-dolt", 3306) if worker else ("127.0.0.1", 33070)
    )
    if (dolt.get("host"), dolt.get("port")) != hq_endpoint:
        raise RuntimeError(f"{label} has a drifted HQ endpoint")
    dolt["host"] = "__HQ_DOLT_HOST__"
    dolt["port"] = "__HQ_DOLT_PORT__"
    rig = _one_aegis_rig(value, label)
    aegis_endpoint = (
        ("gas-city-aegis-dolt", "3306")
        if worker
        else ("127.0.0.1", "33071")
    )
    if (rig.get("dolt_host"), rig.get("dolt_port")) != aegis_endpoint:
        raise RuntimeError(f"{label} has a drifted Aegis endpoint")
    rig["dolt_host"] = "__AEGIS_DOLT_HOST__"
    rig["dolt_port"] = "__AEGIS_DOLT_PORT__"
    return value


def _worker_boundary_role() -> str:
    configured = _required_environment("GC_WORKER_BOUNDARY_ROLE")
    rig = os.environ.get("GC_RIG", "")
    mayor_values = (
        os.environ.get("GC_AGENT", ""),
        os.environ.get("GC_ALIAS", ""),
        os.environ.get("GC_TEMPLATE", ""),
    )
    mayor_marker = "gastown.mayor" in mayor_values
    if rig:
        if configured != "aegis" or rig != "aegis" or mayor_marker:
            raise RuntimeError("rig worker cannot carry the trusted Mayor boundary")
        return configured
    if mayor_marker:
        if (
            mayor_values != ("gastown.mayor",) * 3
            or os.environ.get("GC_SESSION_ORIGIN") != "named"
        ):
            raise RuntimeError("trusted Mayor identity is partial or conflicting")
        city_root = Path(_required_environment("GC_CITY_ROOT"))
        mayor_root = city_root / ".gc/agents/mayor"
        workdir = Path.cwd().resolve(strict=True)
        if workdir != mayor_root and mayor_root not in workdir.parents:
            raise RuntimeError("trusted Mayor escaped its exact work directory")
        if configured != "mayor":
            raise RuntimeError("trusted Mayor did not receive the Mayor boundary")
        return configured
    if configured != "hq":
        raise RuntimeError("ordinary HQ worker received a cross-rig boundary")
    return configured


def _required_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or TASK_AUTHORITY_SHA256_RE.fullmatch(value) is None:
        raise RuntimeError(f"{label} is not one lowercase SHA-256")
    return value


def _validate_projected_metadata(content: bytes) -> None:
    metadata = _strict_json_object(content, "Aegis worker metadata overlay")
    expected_keys = {
        "backend",
        "database",
        "dolt_database",
        "dolt_mode",
        "dolt_server_host",
        "dolt_server_port",
        "dolt_server_user",
        "project_id",
    }
    if set(metadata) != expected_keys:
        raise RuntimeError("Aegis worker metadata fields are not exact")
    expected = {
        "backend": "dolt",
        "database": "dolt",
        "dolt_database": "aegis_beads",
        "dolt_mode": "server",
        "dolt_server_host": "gas-city-aegis-dolt",
        "dolt_server_port": 3306,
        "dolt_server_user": "aegis_beads",
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Aegis worker metadata does not name the scoped service")
    project_id = metadata.get("project_id")
    if not isinstance(project_id, str) or SAFE_PROJECT_ID_RE.fullmatch(project_id) is None:
        raise RuntimeError("Aegis worker metadata project_id is not canonical")


def validate_worker_boundary() -> str:
    """Verify image/config overlays and return the exact credential role."""

    role = _worker_boundary_role()
    if Path(_required_environment("GC_HOST_CITY_CONFIG")) != HOST_CITY_CONFIG_PATH:
        raise RuntimeError("host city snapshot path is not exact")
    if Path(_required_environment("GC_IMAGE_WORKER_CITY_CONFIG")) != IMAGE_WORKER_CITY_CONFIG_PATH:
        raise RuntimeError("image worker city path is not exact")
    image_worker = _secure_read(
        IMAGE_WORKER_CITY_CONFIG_PATH,
        "root-owned worker city configuration",
        maximum_bytes=MAX_CITY_CONFIG_BYTES,
        allowed_modes={0o444},
        allowed_uids={IMAGE_ROOT_UID},
    )
    city_root = Path(_required_environment("GC_CITY_ROOT"))
    effective_worker = _secure_read(
        city_root / "city.toml",
        "mounted worker city configuration",
        maximum_bytes=MAX_CITY_CONFIG_BYTES,
        allowed_modes={0o600, 0o640, 0o644},
    )
    if effective_worker != image_worker:
        raise RuntimeError("mounted worker city configuration differs from the image lock")
    host_city = _secure_read(
        HOST_CITY_CONFIG_PATH,
        "validated host city snapshot",
        maximum_bytes=MAX_CITY_CONFIG_BYTES,
        allowed_modes={0o600},
    )
    normalized_host = _normalize_city_endpoints(
        _city_config(host_city, "host city configuration"),
        "host city configuration",
        worker=False,
    )
    normalized_worker = _normalize_city_endpoints(
        _city_config(image_worker, "worker city configuration"),
        "worker city configuration",
        worker=True,
    )
    if normalized_host != normalized_worker:
        raise RuntimeError("worker city differs from host city outside scoped endpoints")

    hq_config: bytes | None = None
    aegis_config: bytes | None = None
    aegis_metadata: bytes | None = None
    if role in {"hq", "mayor"}:
        if Path(_required_environment("GC_HQ_CONFIG_OVERLAY")) != HQ_CONFIG_OVERLAY_PATH:
            raise RuntimeError("HQ config overlay path is not exact")
        hq_config = _secure_read(
            HQ_CONFIG_OVERLAY_PATH,
            "HQ worker config overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        if hq_config != HQ_CONFIG_OVERLAY_CONTENT:
            raise RuntimeError("HQ worker config overlay content drifted")
        mounted_hq = _secure_read(
            city_root / ".beads/config.yaml",
            "mounted HQ config overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        if mounted_hq != hq_config:
            raise RuntimeError("HQ config overlay is not mounted at the Beads scope")
    elif os.environ.get("GC_HQ_CONFIG_OVERLAY"):
        raise RuntimeError("Aegis worker received an HQ config overlay")

    if role in {"aegis", "mayor"}:
        if Path(_required_environment("GC_AEGIS_CONFIG_OVERLAY")) != AEGIS_CONFIG_OVERLAY_PATH:
            raise RuntimeError("Aegis config overlay path is not exact")
        if Path(_required_environment("GC_AEGIS_METADATA_OVERLAY")) != AEGIS_METADATA_OVERLAY_PATH:
            raise RuntimeError("Aegis metadata overlay path is not exact")
        aegis_config = _secure_read(
            AEGIS_CONFIG_OVERLAY_PATH,
            "Aegis worker config overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        aegis_metadata = _secure_read(
            AEGIS_METADATA_OVERLAY_PATH,
            "Aegis worker metadata overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        if aegis_config != AEGIS_CONFIG_OVERLAY_CONTENT:
            raise RuntimeError("Aegis worker config overlay content drifted")
        _validate_projected_metadata(aegis_metadata)
        rig_root = Path(AEGIS_RUNTIME_IDENTITY["GC_RIG_ROOT"])
        mounted_config = _secure_read(
            rig_root / ".beads/config.yaml",
            "mounted Aegis config overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        mounted_metadata = _secure_read(
            rig_root / ".beads/metadata.json",
            "mounted Aegis metadata overlay",
            maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
            allowed_modes={0o600},
        )
        if mounted_config != aegis_config or mounted_metadata != aegis_metadata:
            raise RuntimeError("Aegis overlays are not mounted at the exact rig scope")
    elif os.environ.get("GC_AEGIS_CONFIG_OVERLAY") or os.environ.get("GC_AEGIS_METADATA_OVERLAY"):
        raise RuntimeError("ordinary HQ worker received Aegis scope overlays")

    receipt_content = _secure_read(
        WORKER_BOUNDARY_RECEIPT_PATH,
        "worker boundary receipt",
        maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
        allowed_modes={0o600},
    )
    receipt = _strict_json_object(receipt_content, "worker boundary receipt")
    receipt_keys = {
        "schema_version",
        "kind",
        "role",
        "host_city_sha256",
        "worker_city_sha256",
        "hq_config_source_sha256",
        "hq_config_projected_sha256",
        "aegis_config_source_sha256",
        "aegis_config_projected_sha256",
        "aegis_metadata_source_sha256",
        "aegis_metadata_projected_sha256",
    }
    if (
        set(receipt) != receipt_keys
        or receipt.get("schema_version") != 1
        or receipt.get("kind") != "gas-city-worker-boundary"
        or receipt.get("role") != role
    ):
        raise RuntimeError("worker boundary receipt identity is invalid")
    expected_hashes: dict[str, bytes | None] = {
        "host_city_sha256": host_city,
        "worker_city_sha256": image_worker,
        "hq_config_projected_sha256": hq_config,
        "aegis_config_projected_sha256": aegis_config,
        "aegis_metadata_projected_sha256": aegis_metadata,
    }
    for key, content in expected_hashes.items():
        observed = receipt.get(key)
        if content is None:
            if observed is not None:
                raise RuntimeError(f"worker boundary receipt unexpectedly carries {key}")
        elif _required_digest(observed, key) != hashlib.sha256(content).hexdigest():
            raise RuntimeError(f"worker boundary receipt hash mismatch for {key}")
    for key, required in (
        ("hq_config_source_sha256", role in {"hq", "mayor"}),
        ("aegis_config_source_sha256", role in {"aegis", "mayor"}),
        ("aegis_metadata_source_sha256", role in {"aegis", "mayor"}),
    ):
        value = receipt.get(key)
        if required:
            _required_digest(value, key)
        elif value is not None:
            raise RuntimeError(f"worker boundary receipt unexpectedly carries {key}")
    return role


def _ensure_private_directory(parent: Path, name: str, label: str) -> Path:
    _secure_directory(parent, f"parent of {label}")
    target = parent / name
    try:
        target.mkdir(mode=0o700)
    except FileExistsError:
        pass
    _secure_directory(target, label)
    return target


def _write_new_private_file(path: Path, content: bytes, label: str) -> None:
    _secure_directory(path.parent, f"parent of {label}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RuntimeError(f"{label} already exists or is unsafe") from exc
    try:
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OSError("short credentials write")
            offset += written
        os.fsync(descriptor)
    except OSError as exc:
        raise RuntimeError(f"could not create {label}") from exc
    finally:
        os.close(descriptor)
    _secure_read(
        path,
        label,
        maximum_bytes=MAX_SECRET_BYTES,
        allowed_modes={0o600},
    )


def prepare_dolt_credentials(role: str) -> Path:
    """Create endpoint-keyed credentials only inside the worker-home tmpfs."""

    if _exact_mount_type(WORKER_HOME_PATH) != "tmpfs":
        raise RuntimeError("worker home is not the launcher-provided tmpfs")
    primary = _secret_text(
        PASSWORD_SECRET_PATH,
        "primary Dolt application credential",
        minimum=32,
        maximum=128,
    )
    if DOLT_PASSWORD_RE.fullmatch(primary) is None:
        raise RuntimeError("primary Dolt application credential has an invalid alphabet")
    entries: list[tuple[str, str]]
    if role == "aegis":
        entries = [("gas-city-aegis-dolt:3306", primary)]
    else:
        entries = [("gas-city-hq-dolt:3306", primary)]
    if role == "mayor":
        aegis = _secret_text(
            AEGIS_PASSWORD_SECRET_PATH,
            "Aegis Dolt application credential",
            minimum=32,
            maximum=128,
        )
        if DOLT_PASSWORD_RE.fullmatch(aegis) is None:
            raise RuntimeError("Aegis Dolt application credential has an invalid alphabet")
        if aegis == primary:
            raise RuntimeError("HQ and Aegis Dolt credentials must be distinct")
        entries.append(("gas-city-aegis-dolt:3306", aegis))
    config_root = _ensure_private_directory(WORKER_HOME_PATH, ".config", "worker config root")
    beads_root = _ensure_private_directory(config_root, "beads", "worker Beads config root")
    if DOLT_CREDENTIALS_PATH.parent != beads_root:
        raise RuntimeError("Dolt credentials path escaped the worker Beads config root")
    content = "".join(
        f"[{endpoint}]\npassword={password}\n" for endpoint, password in entries
    ).encode("utf-8")
    _write_new_private_file(DOLT_CREDENTIALS_PATH, content, "ephemeral Dolt credentials")
    os.environ["BEADS_CREDENTIALS_FILE"] = str(DOLT_CREDENTIALS_PATH)
    # GC v1.3.5 resolves GC_DOLT_USER ahead of the selected rig user and does
    # not include either database mirror in its scoped projection key set.
    # Only Mayor can switch stores, so remove those primary-scope mirrors for
    # Mayor after identity validation. Single-scope Aegis workers retain their
    # exact database identity for the locked pre-provider startup helper.
    if role == "mayor":
        for name in (
            "GC_DOLT_USER",
            "GC_DOLT_DATABASE",
            "BEADS_DOLT_SERVER_DATABASE",
        ):
            os.environ.pop(name, None)
    for name in (
        "GC_DOLT_PASSWORD",
        "BEADS_DOLT_PASSWORD",
        "GC_DOLT_PASSWORD_FILE",
        "BEADS_DOLT_PASSWORD_FILE",
    ):
        os.environ.pop(name, None)
    return DOLT_CREDENTIALS_PATH


def _write_private_atomic(
    path: Path,
    content: bytes,
    *,
    mode: int = 0o600,
    expected_current_sha256: str | None = None,
) -> None:
    _secure_directory(path.parent, "provider credential destination")
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(raw)
        os.fchmod(descriptor, mode)
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OSError("short credential write")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        if expected_current_sha256 is not None:
            _, live_digest = _provider_credential(
                path, "compare-and-swap provider credential"
            )
            if live_digest != expected_current_sha256:
                raise RuntimeError(
                    "durable provider credential changed during synchronization"
                )
        os.replace(temporary, path)
        temporary = None
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise RuntimeError("could not atomically write the provider credential") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _validate_seed_marker(path: Path, provider: str) -> None:
    content = _secure_read(
        path,
        "provider seed marker",
        maximum_bytes=4096,
        allowed_modes={0o400},
    )
    value = _strict_json_object(content, "provider seed marker")
    digest = value.get("seed_sha256")
    if (
        set(value) != {"provider", "schema_version", "seed_sha256"}
        or value.get("provider") != provider
        or value.get("schema_version") != 1
        or not isinstance(digest, str)
        or TASK_AUTHORITY_SHA256_RE.fullmatch(digest) is None
    ):
        raise RuntimeError("provider seed marker identity or fields are invalid")


def _read_locked_provider_config(provider: str) -> bytes:
    content = _secure_read(
        PROVIDER_CONFIG_PATH,
        "locked provider configuration",
        maximum_bytes=64 * 1024,
        allowed_modes={0o400, 0o440, 0o444, 0o600, 0o640, 0o644},
        allowed_uids={0, os.geteuid()},
    )
    if provider == "codex":
        try:
            value = tomllib.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise RuntimeError("locked Codex configuration is invalid") from exc
        if value != {
            "model": "gpt-5.6-sol",
            "model_reasoning_effort": "xhigh",
            "approval_policy": "never",
            "sandbox_mode": "danger-full-access",
            "check_for_update_on_startup": False,
        }:
            raise RuntimeError("locked Codex configuration has unexpected settings")
    else:
        value = _strict_json_object(content, "locked Claude configuration")
        if value != {
            "switchModelsOnFlag": False,
            "disableAllHooks": False,
            "enableAllProjectMcpServers": False,
            "skipDangerousModePermissionPrompt": False,
        }:
            raise RuntimeError("locked Claude configuration has unexpected settings")
    return content


def _strip_locked_provider_arguments(provider: str, arguments: list[str]) -> list[str]:
    """Remove only exact Gas City renderings of settings locked below.

    Gas City resolves provider option defaults into command-line arguments before
    it invokes the container wrapper.  The supervisor is the final policy
    boundary, so it must not pass those settings through a second time (where a
    later alias such as Codex ``--full-auto`` could win).  Exact locked values
    are consumed here and then re-injected once by :func:`_provider_command`;
    conflicting or ambiguous values fail closed.
    """

    if provider == "codex":
        locked = (
            (("-m", "--model"), "gpt-5.6-sol", "model"),
            (("-c", "--config"), "model_reasoning_effort=xhigh", "reasoning effort"),
            (("-s", "--sandbox"), "danger-full-access", "sandbox"),
            (("-a", "--ask-for-approval"), "never", "approval policy"),
        )
        valueless = {"--full-auto": "full-auto alias"}
    else:
        locked = ((("--model",), "claude-fable-5", "model"),)
        valueless = {}

    result: list[str] = []
    seen: set[str] = set()
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            result.extend(arguments[index:])
            break

        if argument in valueless:
            identity = valueless[argument]
            if identity in seen:
                raise RuntimeError(f"worker arguments repeat locked {provider} {identity}")
            seen.add(identity)
            index += 1
            continue

        matched = False
        for aliases, expected, identity in locked:
            separate = argument in aliases
            attached_value: str | None = None
            if not separate:
                for alias in aliases:
                    if alias.startswith("--") and argument.startswith(alias + "="):
                        attached_value = argument[len(alias) + 1 :]
                        break
            if not separate and attached_value is None:
                continue
            if identity in seen:
                raise RuntimeError(f"worker arguments repeat locked {provider} {identity}")
            if separate:
                if index + 1 >= len(arguments):
                    raise RuntimeError(f"worker arguments omit locked {provider} {identity}")
                observed = arguments[index + 1]
                index += 2
            else:
                observed = attached_value
                index += 1
            if observed != expected:
                raise RuntimeError(f"worker arguments conflict with locked {provider} {identity}")
            seen.add(identity)
            matched = True
            break
        if matched:
            continue
        result.append(argument)
        index += 1
    return result


def _reject_provider_overrides(provider: str, arguments: list[str]) -> None:
    if provider == "codex":
        forbidden = {
            "-c", "--config", "-m", "--model", "-p", "--profile",
            "-s", "--sandbox", "-a", "--ask-for-approval", "--oss",
            "--local-provider", "--dangerously-bypass-approvals-and-sandbox",
        }
    else:
        forbidden = {
            "--model", "--fallback-model", "--settings", "--setting-sources",
            "--mcp-config", "--strict-mcp-config", "--agent", "--agents",
            "--bare", "--safe-mode",
        }
    for argument in arguments:
        if argument == "--":
            break
        option = argument.split("=", 1)[0]
        short_override = provider == "codex" and any(
            argument.startswith(prefix)
            for prefix in ("-c", "-m", "-p", "-s", "-a")
        )
        if option in forbidden or short_override:
            raise RuntimeError(f"worker arguments cannot override locked {provider} settings")


def _provider_command(provider: str, arguments: list[str]) -> list[str]:
    _read_locked_provider_config(provider)
    normalized_arguments = _strip_locked_provider_arguments(provider, arguments)
    _reject_provider_overrides(provider, normalized_arguments)
    if provider == "codex":
        return [
            "codex",
            "--strict-config",
            "--model", "gpt-5.6-sol",
            "--sandbox", "danger-full-access",
            "--ask-for-approval", "never",
            "--config", 'model_reasoning_effort="xhigh"',
            "--config", "check_for_update_on_startup=false",
            "--config", "mcp_servers={}",
            *normalized_arguments,
        ]
    return [
        "claude",
        "--model", "claude-fable-5",
        "--settings", str(PROVIDER_CONFIG_PATH),
        "--setting-sources", "user",
        "--strict-mcp-config",
        *normalized_arguments,
    ]


class ProviderCredentialSync:
    """Seed a tmpfs provider HOME and durably adopt validated refreshes."""

    def __init__(self, provider: str, sync_receipt: Path):
        self.provider = provider
        self.layout = PROVIDER_LAYOUTS[provider]
        self.persistent_path = PROVIDER_HOME_PATH / str(
            self.layout["stable_credential"]
        )
        self.visible_directory = WORKER_HOME_PATH / str(
            self.layout["home_directory"]
        )
        self.visible_path = self.visible_directory / str(
            self.layout["home_credential"]
        )
        self.sync_receipt = sync_receipt
        self.durable_digest = ""

    def initialize(self, *, session_overlays: bool = True) -> None:
        stable_name = str(self.layout["stable_credential"])
        _exact_directory_entries(
            PROVIDER_HOME_PATH,
            {stable_name, ".seed-generation.json"},
            "durable provider credential directory",
        )
        _validate_seed_marker(PROVIDER_HOME_PATH / ".seed-generation.json", self.provider)
        content, self.durable_digest = _provider_credential(
            self.persistent_path, "durable provider credential"
        )
        _secure_directory(WORKER_HOME_PATH, "tmpfs provider HOME")
        try:
            self.visible_directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise RuntimeError("could not create the tmpfs provider configuration root") from exc
        _secure_directory(self.visible_directory, "tmpfs provider configuration root")
        if session_overlays:
            _exact_directory_entries(
                PROVIDER_SESSION_PATH,
                {str(item) for item in self.layout["overlays"]},
                "provider session overlay root",
            )
            for overlay in self.layout["overlays"]:
                source = PROVIDER_SESSION_PATH / str(overlay)
                _secure_directory(source, f"provider {overlay} session overlay")
                target = self.visible_directory / str(overlay)
                try:
                    target.symlink_to(source, target_is_directory=True)
                except FileExistsError as exc:
                    raise RuntimeError("tmpfs provider root was not empty at initialization") from exc
        _write_private_atomic(self.visible_path, content)

    def sync(self, *, final: bool = False) -> bool:
        stable_name = str(self.layout["stable_credential"])
        _exact_directory_entries(
            PROVIDER_HOME_PATH,
            {stable_name, ".seed-generation.json"},
            "durable provider credential directory",
        )
        _validate_seed_marker(PROVIDER_HOME_PATH / ".seed-generation.json", self.provider)
        try:
            session_content, session_digest = _provider_credential(
                self.visible_path, "tmpfs provider credential"
            )
        except RuntimeError:
            if final:
                raise
            return False
        _, observed_durable_digest = _provider_credential(
            self.persistent_path, "durable provider credential"
        )
        if observed_durable_digest != self.durable_digest:
            raise RuntimeError("durable provider credential changed outside the supervisor")
        if session_digest == self.durable_digest:
            return False
        _write_private_atomic(
            self.persistent_path,
            session_content,
            expected_current_sha256=self.durable_digest,
        )
        _, installed_digest = _provider_credential(
            self.persistent_path, "synchronized durable provider credential"
        )
        if installed_digest != session_digest:
            raise RuntimeError("durable provider credential failed post-sync verification")
        previous = self.durable_digest
        self.durable_digest = session_digest
        write_receipt(
            self.sync_receipt,
            {
                "schema_version": 1,
                "status": "synced",
                "provider": self.provider,
                "previous_sha256": previous,
                "credential_sha256": session_digest,
            },
        )
        return True


def load_task_authority_runtime():
    configured = Path(_required_environment("AEGIS_TASK_AUTHORITY_RUNTIME_FILE"))
    expected_digest = _required_environment("AEGIS_TASK_AUTHORITY_RUNTIME_SHA256")
    if configured != TASK_AUTHORITY_RUNTIME_PATH:
        raise RuntimeError("task-authority runtime path is not the immutable image path")
    if not TASK_AUTHORITY_SHA256_RE.fullmatch(expected_digest):
        raise RuntimeError("task-authority runtime digest is not one lowercase SHA-256")
    if not configured.is_absolute() or configured.is_symlink():
        raise RuntimeError("task-authority runtime must be one absolute non-symlink file")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production workers are Linux.
        raise RuntimeError("task-authority runtime cannot be opened without symlink following")
    try:
        descriptor = os.open(configured, os.O_RDONLY | os.O_CLOEXEC | no_follow)
    except OSError as exc:
        raise RuntimeError("task-authority runtime could not be opened") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RuntimeError("task-authority runtime is not a regular file")
        if before.st_uid != TASK_AUTHORITY_RUNTIME_UID:
            raise RuntimeError("task-authority runtime is not owned by image root")
        if stat.S_IMODE(before.st_mode) != TASK_AUTHORITY_RUNTIME_MODE:
            raise RuntimeError("task-authority runtime permissions are not immutable 0444")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            content = stream.read(TASK_AUTHORITY_MAX_RUNTIME_BYTES + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if len(content) > TASK_AUTHORITY_MAX_RUNTIME_BYTES:
        raise RuntimeError("task-authority runtime exceeds its maximum size")
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity or len(content) != after.st_size:
        raise RuntimeError("task-authority runtime changed while being verified")
    if hashlib.sha256(content).hexdigest() != expected_digest:
        raise RuntimeError("task-authority runtime SHA-256 does not match the deployment lock")
    module_name = "_gas_city_task_authority_runtime"
    module = types.ModuleType(module_name)
    module.__file__ = str(configured)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(content, str(configured), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def validate_task_authority_environment() -> str | None:
    """Validate the live generation-2 Beads receipt before provider execution."""

    rig = os.environ.get("GC_RIG", "")
    authority_names = (
        "AEGIS_TASK_AUTHORITY_FILE",
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE",
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256",
        "GC_BEADS_PREFIX",
    )
    if not rig:
        if any(os.environ.get(name) for name in authority_names):
            raise RuntimeError("HQ worker cannot carry a partial rig task-authority identity")
        for name, expected in HQ_RUNTIME_IDENTITY.items():
            if _required_environment(name) != expected:
                raise RuntimeError(f"HQ worker identity mismatch for {name}")
        workdir = Path.cwd().resolve()
        city_root = Path(HQ_RUNTIME_IDENTITY["GC_CITY_ROOT"])
        hq_work_roots = tuple(
            city_root / ".gc" / "agents" / name
            for name in ("boot", "deacon", "mayor", "dogs")
        )
        if not any(workdir == root or root in workdir.parents for root in hq_work_roots):
            raise RuntimeError("HQ worker process escaped its assigned agent scope")
        return None
    for name, expected in AEGIS_RUNTIME_IDENTITY.items():
        if _required_environment(name) != expected:
            raise RuntimeError(f"Aegis worker identity mismatch for {name}")
    workdir = Path.cwd().resolve()
    city_root = Path(AEGIS_RUNTIME_IDENTITY["GC_CITY_ROOT"])
    allowed_work_roots = (
        city_root / ".gc" / "worktrees" / "aegis",
        city_root / ".gc" / "agents" / "aegis",
    )
    if not any(workdir == root or root in workdir.parents for root in allowed_work_roots):
        raise RuntimeError("Aegis worker process escaped its assigned worktree scope")
    receipt_path = Path(_required_environment("AEGIS_TASK_AUTHORITY_FILE"))
    if receipt_path != TASK_AUTHORITY_RECEIPT_PATH:
        raise RuntimeError("Aegis worker receipt path is not the live authority-directory path")
    module = load_task_authority_runtime()
    selected = module.load_authority_from_environment(
        os.environ,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
    )
    receipt = selected.receipt
    if not selected.explicit or receipt is None:
        raise RuntimeError("Aegis worker requires explicit task authority")
    if receipt.generation != TASK_AUTHORITY_REQUIRED_GENERATION:
        raise RuntimeError(
            "Aegis worker requires exact task-authority receipt generation "
            f"{TASK_AUTHORITY_REQUIRED_GENERATION}"
        )
    if str(selected.mode.value) != "beads":
        raise RuntimeError("Aegis worker requires explicit Beads task authority")
    return str(module.receipt_sha256(receipt))


def validate_aegis_git_broker_environment(*, frozen_startup: bool) -> dict[str, Any]:
    """Require the host broker's private Git boundary and optional frozen startup."""

    if os.environ.get("GC_RIG") != "aegis":
        raise RuntimeError("Git broker validation is only valid for the Aegis rig")
    expected_environment = {
        "GIT_DIR": str(AEGIS_PRIVATE_GIT_DIR),
        "GIT_WORK_TREE": str(Path.cwd().resolve(strict=True)),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "AEGIS_GIT_BROKER_RECEIPT_PATH": str(AEGIS_GIT_BROKER_RECEIPT_PATH),
    }
    for name, expected in expected_environment.items():
        if _required_environment(name) != expected:
            raise RuntimeError(f"Aegis private Git identity mismatch for {name}")
    expected_digest = _required_environment("AEGIS_GIT_BROKER_RECEIPT_SHA256")
    if TASK_AUTHORITY_SHA256_RE.fullmatch(expected_digest) is None:
        raise RuntimeError("Git broker receipt digest is invalid")
    content = _secure_read(
        AEGIS_GIT_BROKER_RECEIPT_PATH,
        "host-generated Git broker receipt",
        maximum_bytes=MAX_BEADS_BOUNDARY_BYTES,
        allowed_modes={0o400},
    )
    if hashlib.sha256(content).hexdigest() != expected_digest:
        raise RuntimeError("Git broker receipt digest does not match the host binding")
    value = _strict_json_object(content, "host-generated Git broker receipt")
    session_digest = hashlib.sha256(
        _required_environment("GC_SESSION_ID").encode("utf-8")
    ).hexdigest()
    worktree = str(Path.cwd().resolve(strict=True))
    expected = {
        "schema_version": 1,
        "kind": "aegis-private-git-broker",
        "status": "prepared",
        "agent": _required_environment("GC_AGENT"),
        "session_id_sha256": session_digest,
        "worktree": worktree,
        "source_common_dir": "/home/loucmane/codex/.git",
        "base_branch": "main",
        "base_ref": "refs/remotes/origin/main",
        "container_private_git_dir": str(AEGIS_PRIVATE_GIT_DIR),
        "container_receipt_path": str(AEGIS_GIT_BROKER_RECEIPT_PATH),
        "frozen_startup_receipt_path": str(AEGIS_POLECAT_STARTUP_RECEIPT_PATH),
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise RuntimeError("Git broker receipt does not bind this exact worker")
    for name in ("starting_oid", "base_oid"):
        if not isinstance(value.get(name), str) or GIT_OID_RE.fullmatch(value[name]) is None:
            raise RuntimeError(f"Git broker receipt {name} is not one commit")
    source_branch = value.get("source_branch")
    if (
        not isinstance(source_branch, str)
        or not source_branch.startswith("gc-")
        or value.get("source_ref") != f"refs/heads/{source_branch}"
    ):
        raise RuntimeError("Git broker receipt source branch is invalid")
    private_info = AEGIS_PRIVATE_GIT_DIR.lstat()
    if (
        stat.S_ISLNK(private_info.st_mode)
        or not stat.S_ISDIR(private_info.st_mode)
        or private_info.st_uid != os.geteuid()
        or stat.S_IMODE(private_info.st_mode) != 0o700
    ):
        raise RuntimeError("session-private Git directory is not owner-only")
    if not frozen_startup:
        return value

    startup_digest = _required_environment("AEGIS_FROZEN_STARTUP_RECEIPT_SHA256")
    if TASK_AUTHORITY_SHA256_RE.fullmatch(startup_digest) is None:
        raise RuntimeError("frozen startup receipt digest is invalid")
    startup_content = _secure_read(
        AEGIS_POLECAT_STARTUP_RECEIPT_PATH,
        "frozen pre-provider startup receipt",
        maximum_bytes=AEGIS_POLECAT_STARTUP_MAX_BYTES,
        allowed_modes={0o400},
    )
    if hashlib.sha256(startup_content).hexdigest() != startup_digest:
        raise RuntimeError("frozen startup receipt digest does not match the host binding")
    startup = _strict_json_object(startup_content, "frozen pre-provider startup receipt")
    source_id = startup.get("source_work_id")
    branch = startup.get("branch")
    if (
        startup.get("schema_version") != 1
        or startup.get("kind") != "aegis-polecat-pre-provider-startup"
        or startup.get("status") not in {"prepared", "resumed"}
        or startup.get("git_broker_receipt_sha256") != expected_digest
        or startup.get("git_broker_id") != value.get("broker_id")
        or startup.get("git_source_branch") != source_branch
        or startup.get("git_starting_oid") != value.get("starting_oid")
        or startup.get("git_source_common_dir") != value.get("source_common_dir")
        or startup.get("git_private_common_dir") != str(AEGIS_PRIVATE_GIT_DIR)
        or startup.get("work_dir") != worktree
        or not isinstance(source_id, str)
        or AEGIS_BEAD_ID_RE.fullmatch(source_id) is None
        or branch != f"polecat/{source_id}"
        or not isinstance(startup.get("git_head"), str)
        or GIT_OID_RE.fullmatch(startup["git_head"]) is None
    ):
        raise RuntimeError("frozen startup receipt is not bound to this private Git session")
    return value


def configure_github_delivery() -> dt.datetime | None:
    """Install one receipt-bound, short-lived GitHub App credential."""

    github_required = os.environ.get("GC_GITHUB_REQUIRED", "false").lower() == "true"
    github_token_file = os.environ.get("GC_GITHUB_TOKEN_FILE")
    if not github_required:
        return None
    receipt_path = os.environ.get("GC_GITHUB_RECEIPT_PATH")
    receipt_sha256 = os.environ.get("GC_GITHUB_RECEIPT_SHA256")
    if (
        github_token_file != str(GITHUB_SECRET_PATH)
        or receipt_path != str(GITHUB_DELIVERY_RECEIPT_PATH)
        or not isinstance(receipt_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", receipt_sha256) is None
    ):
        raise RuntimeError("GitHub delivery credential is required but not mounted")
    token_content = _secure_read(
        GITHUB_SECRET_PATH,
        "GitHub delivery credential",
        maximum_bytes=4097,
        allowed_modes={0o400},
    )
    try:
        github_token = token_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("GitHub delivery credential is not UTF-8") from exc
    if github_token.endswith("\n"):
        github_token = github_token[:-1]
    if (
        not 20 <= len(github_token) <= 4096
        or any(character.isspace() or character == "\x00" for character in github_token)
    ):
        raise RuntimeError("GitHub delivery credential has an invalid shape")
    receipt_content = _secure_read(
        GITHUB_DELIVERY_RECEIPT_PATH,
        "GitHub delivery receipt",
        maximum_bytes=1024 * 1024,
        allowed_modes={0o400},
    )
    if hashlib.sha256(receipt_content).hexdigest() != receipt_sha256:
        raise RuntimeError("GitHub delivery receipt digest does not match its host binding")
    receipt = _strict_json_object(receipt_content, "GitHub delivery receipt")
    repository = receipt.get("repository")
    issued_raw = receipt.get("issued_at")
    expires_raw = receipt.get("expires_at")
    try:
        issued = dt.datetime.fromisoformat(str(issued_raw).replace("Z", "+00:00"))
        expires = dt.datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("GitHub delivery receipt timestamps are invalid") from exc
    now = dt.datetime.now(dt.timezone.utc)
    digest_fields = (
        "app_id_sha256",
        "installation_id_sha256",
        "token_sha256",
        "effective_rules_sha256",
        "rulesets_sha256",
    )
    if (
        set(receipt)
        != {
            "schema_version",
            "kind",
            "status",
            "repository",
            "permissions",
            "app_id_sha256",
            "installation_id_sha256",
            "token_sha256",
            "issued_at",
            "expires_at",
            "lifetime_seconds",
            "effective_rules_sha256",
            "effective_rule_types",
            "ruleset_ids",
            "rulesets_sha256",
            "api_version",
        }
        or receipt.get("schema_version") != 1
        or receipt.get("kind") != "gas-city-github-app-delivery-token"
        or receipt.get("status") != "verified"
        or not isinstance(repository, dict)
        or set(repository) != {"id", "name_with_owner", "default_branch"}
        or type(repository.get("id")) is not int
        or repository["id"] < 1
        or str(repository.get("name_with_owner", "")).casefold()
        != GITHUB_DELIVERY_REPOSITORY.casefold()
        or repository.get("default_branch") != "main"
        or receipt.get("permissions") != GITHUB_DELIVERY_PERMISSIONS
        or receipt.get("api_version") != "2022-11-28"
        or receipt.get("lifetime_seconds") not in range(50 * 60, 65 * 60 + 1)
        or issued.tzinfo is None
        or expires.tzinfo is None
        or issued > now
        or expires <= now + dt.timedelta(minutes=5)
        or int((expires - issued).total_seconds()) != receipt.get("lifetime_seconds")
        or not isinstance(receipt.get("effective_rule_types"), list)
        or not GITHUB_REQUIRED_DEFAULT_RULES.issubset(receipt["effective_rule_types"])
        or not isinstance(receipt.get("ruleset_ids"), list)
        or not receipt["ruleset_ids"]
        or any(type(item) is not int or item < 1 for item in receipt["ruleset_ids"])
        or any(
            not isinstance(receipt.get(field), str)
            or re.fullmatch(r"[0-9a-f]{64}", receipt[field]) is None
            for field in digest_fields
        )
        or receipt.get("token_sha256") != hashlib.sha256(token_content).hexdigest()
    ):
        raise RuntimeError("GitHub delivery receipt is stale or outside its exact scope")
    os.environ["GH_TOKEN"] = github_token
    transient_git_config = (
        ("credential.https://github.com.helper", "!bash /opt/gas-city/git-credential-github.sh"),
        ("url.https://github.com/.insteadOf", "git@github.com:"),
        ("url.https://github.com/.insteadOf", "ssh://git@github.com/"),
    )
    os.environ["GIT_CONFIG_COUNT"] = str(len(transient_git_config))
    for index, (key, item) in enumerate(transient_git_config):
        os.environ[f"GIT_CONFIG_KEY_{index}"] = key
        os.environ[f"GIT_CONFIG_VALUE_{index}"] = item
    return expires


def _validate_aegis_polecat_startup_helper() -> str:
    """Verify the root-owned helper before its only permitted invocation."""

    configured = Path(_required_environment("AEGIS_STARTUP_HELPER_FILE"))
    expected_digest = _required_environment("AEGIS_STARTUP_HELPER_SHA256")
    receipt_path = Path(_required_environment("AEGIS_STARTUP_RECEIPT_PATH"))
    if configured != AEGIS_POLECAT_STARTUP_PATH:
        raise RuntimeError("Aegis polecat startup helper path is not immutable")
    if receipt_path != AEGIS_POLECAT_STARTUP_RECEIPT_PATH:
        raise RuntimeError("Aegis polecat startup receipt path is not exact")
    if TASK_AUTHORITY_SHA256_RE.fullmatch(expected_digest) is None:
        raise RuntimeError("Aegis polecat startup helper digest is invalid")
    content = _secure_read(
        configured,
        "immutable Aegis polecat startup helper",
        maximum_bytes=AEGIS_POLECAT_STARTUP_MAX_BYTES,
        allowed_modes={0o444},
        allowed_uids={0},
    )
    if hashlib.sha256(content).hexdigest() != expected_digest:
        raise RuntimeError("Aegis polecat startup helper digest does not match the lock")
    return expected_digest


def _validate_aegis_runtime() -> tuple[str, str, str]:
    """Verify the offline wheel, image shim, and exact tmpfs launcher digest."""

    artifact = Path(_required_environment("AEGIS_RUNTIME_ARTIFACT_FILE"))
    shim = Path(_required_environment("AEGIS_RUNTIME_SHIM_FILE"))
    artifact_digest = _required_environment("AEGIS_RUNTIME_ARTIFACT_SHA256")
    shim_digest = _required_environment("AEGIS_RUNTIME_SHIM_SHA256")
    launcher_digest = _required_environment("AEGIS_LOCAL_LAUNCHER_SHA256")
    if artifact != AEGIS_RUNTIME_ARTIFACT_PATH or shim != AEGIS_RUNTIME_SHIM_PATH:
        raise RuntimeError("Aegis runtime paths are not the immutable image paths")
    for label, value in (
        ("Aegis runtime artifact", artifact_digest),
        ("Aegis runtime shim", shim_digest),
        ("Aegis local launcher", launcher_digest),
    ):
        if TASK_AUTHORITY_SHA256_RE.fullmatch(value) is None:
            raise RuntimeError(f"{label} digest is invalid")
    artifact_content = _secure_read(
        artifact,
        "immutable offline Aegis runtime artifact",
        maximum_bytes=AEGIS_RUNTIME_ARTIFACT_MAX_BYTES,
        allowed_modes={0o444},
        allowed_uids={0},
    )
    shim_content = _secure_read(
        shim,
        "immutable Aegis runtime shim",
        maximum_bytes=AEGIS_RUNTIME_SHIM_MAX_BYTES,
        allowed_modes={0o444},
        allowed_uids={0},
    )
    if hashlib.sha256(artifact_content).hexdigest() != artifact_digest:
        raise RuntimeError("Aegis runtime artifact digest does not match the deployment lock")
    if hashlib.sha256(shim_content).hexdigest() != shim_digest:
        raise RuntimeError("Aegis runtime shim digest does not match the deployment lock")
    if hashlib.sha256(AEGIS_LOCAL_LAUNCHER_CONTENT).hexdigest() != launcher_digest:
        raise RuntimeError("Aegis local launcher digest does not match the deployment lock")
    return artifact_digest, shim_digest, launcher_digest


def _exact_mount_type(path: Path) -> str | None:
    """Return the filesystem type only when *path* is one exact mountpoint."""

    try:
        lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
    except OSError as exc:  # pragma: no cover - production workers are Linux.
        raise RuntimeError("cannot inspect the target-local Aegis launcher mount") from exc
    encoded = str(path).replace(" ", "\\040")
    matches: list[str] = []
    for line in lines:
        fields = line.split()
        if len(fields) < 10 or fields[4] != encoded or "-" not in fields:
            continue
        separator = fields.index("-")
        if separator + 1 < len(fields):
            matches.append(fields[separator + 1])
    if len(matches) > 1:
        raise RuntimeError("target-local Aegis launcher mount is ambiguous")
    return matches[0] if matches else None


def _prepare_local_aegis_launcher() -> Path:
    """Materialize the only target-local executable inside its nested tmpfs."""

    _validate_aegis_runtime()
    target = Path.cwd().resolve(strict=True)
    bin_directory = target / AEGIS_LOCAL_LAUNCHER_REL.parent
    try:
        directory = bin_directory.lstat()
    except OSError as exc:
        raise RuntimeError("target-local Aegis bin tmpfs is missing") from exc
    if (
        stat.S_ISLNK(directory.st_mode)
        or not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != os.geteuid()
        or stat.S_IMODE(directory.st_mode) != 0o700
    ):
        raise RuntimeError("target-local Aegis bin tmpfs is not private")
    if _exact_mount_type(bin_directory) != "tmpfs":
        raise RuntimeError("target-local Aegis bin directory is not the nested tmpfs")
    launcher = target / AEGIS_LOCAL_LAUNCHER_REL
    if not launcher.exists() and not launcher.is_symlink():
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(launcher, flags, 0o500)
            offset = 0
            while offset < len(AEGIS_LOCAL_LAUNCHER_CONTENT):
                written = os.write(descriptor, AEGIS_LOCAL_LAUNCHER_CONTENT[offset:])
                if written <= 0:
                    raise OSError("short Aegis launcher write")
                offset += written
            os.fsync(descriptor)
        except OSError as exc:
            try:
                os.close(descriptor)  # type: ignore[possibly-undefined]
            except (OSError, UnboundLocalError):
                pass
            raise RuntimeError("could not create the target-local Aegis launcher") from exc
        else:
            os.close(descriptor)
    content = _secure_read(
        launcher,
        "target-local Aegis launcher",
        maximum_bytes=4096,
        allowed_modes={0o500},
    )
    if content != AEGIS_LOCAL_LAUNCHER_CONTENT:
        raise RuntimeError("target-local Aegis launcher content is not exact")
    return launcher


def _run_aegis_polecat_startup(authority_digest: str) -> bool:
    """Run pre-provider preparation; return false for an authoritative drain."""

    _validate_aegis_polecat_startup_helper()
    _prepare_local_aegis_launcher()
    session_name = _required_environment("GC_SESSION_NAME")
    if os.environ.get("GC_AGENT") != session_name:
        raise RuntimeError("Aegis polecat agent and session identities differ")
    inherited_actor = os.environ.get("BEADS_ACTOR")
    if inherited_actor not in {None, "", session_name}:
        raise RuntimeError("Aegis polecat inherited a conflicting BEADS_ACTOR")
    os.environ["BEADS_ACTOR"] = session_name
    os.environ["AEGIS_TASK_AUTHORITY_RECEIPT_SHA256"] = authority_digest
    try:
        result = subprocess.run(
            ["/usr/bin/python3", "-I", str(AEGIS_POLECAT_STARTUP_PATH), "prepare"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Aegis polecat startup helper could not complete") from exc
    if (
        len(result.stdout) > AEGIS_POLECAT_STARTUP_MAX_BYTES
        or len(result.stderr) > AEGIS_POLECAT_STARTUP_MAX_BYTES
    ):
        raise RuntimeError("Aegis polecat startup helper exceeded its output bound")
    if result.returncode == AEGIS_POLECAT_STARTUP_NO_WORK_EXIT:
        return False
    if result.returncode != 0:
        raise RuntimeError("Aegis polecat startup helper rejected provider launch")
    return True


def extract_receipt(provider: str, event: dict[str, Any]) -> tuple[str, str | None] | None:
    """Return a provider-authored model receipt from a recognized event only."""
    if provider == "claude" and event.get("type") == "assistant":
        message = event.get("message")
        if isinstance(message, dict) and isinstance(message.get("model"), str):
            return message["model"], None
    if provider == "codex" and event.get("type") == "turn_context":
        payload = event.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("model"), str):
            effort = payload.get("effort") or payload.get("reasoning_effort")
            collaboration = payload.get("collaboration_mode")
            if not effort and isinstance(collaboration, dict):
                settings = collaboration.get("settings")
                if isinstance(settings, dict):
                    effort = settings.get("reasoning_effort")
            return payload["model"], effort if isinstance(effort, str) else None
    return None


def is_claude_refusal_fallback(provider: str, event: dict[str, Any]) -> bool:
    return (
        provider == "claude"
        and event.get("type") == "system"
        and event.get("subtype") == "model_refusal_fallback"
    )


def is_model_receipt_event(provider: str, event: dict[str, Any]) -> bool:
    """Return whether an event type is required to carry model metadata."""

    return (
        provider == "claude" and event.get("type") == "assistant"
    ) or (
        provider == "codex" and event.get("type") == "turn_context"
    )


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


class TrustedModelEvidenceChannel:
    """One host-authenticated connection opened before provider code runs."""

    def __init__(self, provider: str, phase: str):
        configured = Path(os.environ.get("GC_MODEL_EVIDENCE_SOCKET", ""))
        if configured != MODEL_EVIDENCE_SOCKET_PATH:
            raise RuntimeError("trusted model evidence socket path is invalid")
        try:
            info = configured.lstat()
        except OSError as exc:
            raise RuntimeError("trusted model evidence socket is unavailable") from exc
        if (
            not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise RuntimeError("trusted model evidence socket is unsafe")
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.set_inheritable(False)
        connection.settimeout(20)
        try:
            connection.connect(str(configured))
            self._send(
                connection,
                {
                    "schema_version": 1,
                    "kind": "supervisor-model-evidence-hello",
                    "phase": phase,
                    "provider": provider,
                },
            )
            acknowledgement = self._receive(connection, "host evidence acknowledgement")
        except Exception:
            connection.close()
            raise
        expected = {
            "schema_version": 1,
            "kind": "host-model-evidence-ack",
            "status": "accepted",
            "phase": phase,
            "provider": provider,
        }
        challenge = acknowledgement.get("challenge")
        if (
            set(acknowledgement) != {*expected, "challenge"}
            or any(acknowledgement.get(key) != value for key, value in expected.items())
            or not isinstance(challenge, str)
            or TASK_AUTHORITY_SHA256_RE.fullmatch(challenge) is None
        ):
            connection.close()
            raise RuntimeError("host evidence acknowledgement is invalid")
        connection.settimeout(None)
        self.connection = connection
        self.provider = provider
        self.phase = phase
        self.challenge = challenge

    @staticmethod
    def _send(connection: socket.socket, value: dict[str, Any]) -> None:
        content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(content) > MODEL_EVIDENCE_MAX_BYTES:
            raise RuntimeError("trusted model evidence exceeds its size bound")
        connection.sendall(content)

    @staticmethod
    def _receive(connection: socket.socket, label: str) -> dict[str, Any]:
        content = bytearray()
        while len(content) <= MODEL_EVIDENCE_MAX_BYTES:
            chunk = connection.recv(
                min(65536, MODEL_EVIDENCE_MAX_BYTES + 1 - len(content))
            )
            if not chunk:
                raise RuntimeError(f"host closed the trusted channel during {label}")
            content.extend(chunk)
            newline = content.find(b"\n")
            if newline >= 0:
                if content[newline + 1 :]:
                    raise RuntimeError(f"host coalesced messages during {label}")
                return _strict_json_object(bytes(content[:newline]), label)
        raise RuntimeError(f"{label} exceeds its size bound")

    def send_evidence(
        self,
        *,
        expected_model: str,
        expected_effort: str | None,
        observed_model: str,
        observed_effort: str | None,
        provider_exit_code: int,
        event_sha256: str,
        transcript_sha256: str,
        transcript_locator: str,
        tool_free: bool,
    ) -> None:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "kind": "supervisor-model-evidence",
            "phase": self.phase,
            "provider": self.provider,
            "challenge": self.challenge,
            "provider_exit_code": provider_exit_code,
            "transcript_sha256": transcript_sha256,
            "transcript_locator": transcript_locator,
            "tool_free": tool_free,
        }
        if self.phase == "preflight":
            payload.update(
                {
                    "expected_model": expected_model,
                    "expected_effort": expected_effort,
                    "observed_model": observed_model,
                    "observed_effort": observed_effort,
                    "event_sha256": event_sha256,
                }
            )
        # Session JSONL is provider-writable.  The authority-bearing channel
        # attests supervisor completion and a run-bound transcript digest, but
        # deliberately makes no positive model claim.  Model authority comes
        # only from the prior no-tool preflight receipt.
        self._send(self.connection, payload)
        try:
            self.connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        self.connection.settimeout(30)
        acknowledgement = self._receive(
            self.connection, "host evidence commit acknowledgement"
        )
        expected = {
            "schema_version": 1,
            "kind": "host-model-evidence-committed",
            "status": "committed",
            "phase": self.phase,
            "provider": self.provider,
            "challenge": self.challenge,
        }
        receipt_sha256 = acknowledgement.get("receipt_sha256")
        if (
            set(acknowledgement) != {*expected, "receipt_sha256"}
            or any(acknowledgement.get(key) != value for key, value in expected.items())
            or not isinstance(receipt_sha256, str)
            or TASK_AUTHORITY_SHA256_RE.fullmatch(receipt_sha256) is None
        ):
            raise RuntimeError("host evidence commit acknowledgement is invalid")

    def close(self) -> None:
        self.connection.close()


def _event_contains_tool_use(event: Mapping[str, Any]) -> bool:
    """Reject provider tool events in an identity-only preflight transcript."""

    if event.get("type") in {"tool_use", "tool_result", "item.started", "item.updated"}:
        return True
    if event.get("type") == "item.completed":
        item = event.get("item")
        return not (
            isinstance(item, dict)
            and item.get("type") in CODEX_PREFLIGHT_ALLOWED_ITEM_TYPES
        )
    message = event.get("message")
    if not isinstance(message, dict):
        return False
    blocks = message.get("content")
    if not isinstance(blocks, list):
        return False
    return any(
        isinstance(block, dict) and block.get("type") in {"tool_use", "tool_result"}
        for block in blocks
    )


def _model_preflight_environment(provider: str) -> dict[str, str]:
    """Return the minimal subscription-auth environment for a preflight child."""

    environment = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(WORKER_HOME_PATH),
        "USER": "worker",
        "LOGNAME": "worker",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "DISABLE_AUTOUPDATER": "1",
    }
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "NODE_EXTRA_CA_CERTS",
    ):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    if provider == "codex":
        environment.update(
            {
                "CODEX_HOME": str(WORKER_HOME_PATH / ".codex"),
                "RUST_LOG": (
                    "codex_core::session=info,"
                    "codex_core::session::handlers=off"
                ),
            }
        )
    else:
        environment.update(
            {
                "CLAUDE_CONFIG_DIR": str(WORKER_HOME_PATH / ".claude"),
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            }
        )
    return environment


def _validate_codex_catalog() -> None:
    content = _secure_read(
        CODEX_PREFLIGHT_MODEL_CATALOG_PATH,
        "Codex preflight model catalog",
        maximum_bytes=64 * 1024,
        allowed_modes={0o444},
        allowed_uids={IMAGE_ROOT_UID},
    )
    if hashlib.sha256(content).hexdigest() != CODEX_PREFLIGHT_MODEL_CATALOG_SHA256:
        raise RuntimeError("Codex preflight model catalog digest does not match the image contract")
    value = _strict_json_object(content, "Codex preflight model catalog")
    models = value.get("models")
    if set(value) != {"models"} or not isinstance(models, list) or len(models) != 1:
        raise RuntimeError("Codex preflight model catalog is not the exact one-model contract")
    model = models[0]
    if not isinstance(model, dict) or (
        model.get("slug") != "gpt-5.6-sol"
        or model.get("default_reasoning_level") != "xhigh"
        or model.get("shell_type") != "disabled"
        or model.get("apply_patch_tool_type") is not None
        or model.get("input_modalities") != ["text"]
        or model.get("supports_search_tool") is not False
        or model.get("supports_reasoning_summaries") is not True
        or model.get("use_responses_lite") is not True
        or model.get("tool_mode") != "direct"
        or model.get("multi_agent_version") != "disabled"
    ):
        raise RuntimeError("Codex preflight model catalog weakens the locked capability boundary")


def _codex_preflight_command(expected_model: str, expected_effort: str) -> list[str]:
    command = [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        expected_model,
        "--config",
        'approval_policy="never"',
        "--config",
        f'model_reasoning_effort="{expected_effort}"',
        "--config",
        f'model_catalog_json="{CODEX_PREFLIGHT_MODEL_CATALOG_PATH}"',
        "--config",
        'web_search="disabled"',
        "--config",
        "mcp_servers={}",
        "--config",
        "skills.include_instructions=false",
        "--config",
        "skills.bundled.enabled=false",
        "--config",
        "tools.experimental_request_user_input={ enabled = false }",
    ]
    for feature in CODEX_PREFLIGHT_FEATURES_DISABLED:
        command.extend(("--disable", feature))
    command.append("Reply with exactly READY and do not perform any other action.")
    return command


def _validate_codex_preflight(
    stdout: bytes,
    stderr: bytes,
    *,
    expected_model: str,
) -> tuple[str, str]:
    events: list[dict[str, Any]] = []
    ready_messages = 0
    for raw_line in stdout.splitlines(keepends=True):
        if not raw_line.strip():
            continue
        event = _strict_json_object(
            raw_line.rstrip(b"\r\n"), "Codex preflight event"
        )
        if _event_contains_tool_use(event):
            raise RuntimeError("Codex preflight emitted or invoked a tool event")
        event_type = event.get("type")
        if event_type == "thread.started":
            thread_id = event.get("thread_id")
            if (
                set(event) != {"type", "thread_id"}
                or not isinstance(thread_id, str)
                or not thread_id
                or len(thread_id) > 128
            ):
                raise RuntimeError("Codex preflight thread event is malformed")
        elif event_type == "turn.started":
            if set(event) != {"type"}:
                raise RuntimeError("Codex preflight turn-start event is malformed")
        elif event_type == "item.completed":
            item = event.get("item")
            if (
                set(event) != {"type", "item"}
                or not isinstance(item, dict)
                or set(item) != {"id", "type", "text"}
                or not isinstance(item.get("id"), str)
                or not isinstance(item.get("text"), str)
            ):
                raise RuntimeError("Codex preflight item event is malformed")
            if item["type"] == "agent_message":
                if item["text"] != "READY":
                    raise RuntimeError("Codex preflight returned an unexpected assistant message")
                ready_messages += 1
        elif event_type == "turn.completed":
            usage = event.get("usage")
            usage_fields = {
                "input_tokens",
                "cached_input_tokens",
                "output_tokens",
                "reasoning_output_tokens",
            }
            if (
                set(event) != {"type", "usage"}
                or not isinstance(usage, dict)
                or set(usage) != usage_fields
                or any(
                    not isinstance(usage.get(field), int)
                    or isinstance(usage.get(field), bool)
                    or usage[field] < 0
                    for field in usage_fields
                )
            ):
                raise RuntimeError("Codex preflight completion event is malformed")
        else:
            raise RuntimeError("Codex preflight emitted a forbidden lifecycle or error event")
        events.append(event)
    if (
        len(events) < 4
        or events[0].get("type") != "thread.started"
        or events[1].get("type") != "turn.started"
        or events[-1].get("type") != "turn.completed"
        or sum(event.get("type") == "thread.started" for event in events) != 1
        or sum(event.get("type") == "turn.started" for event in events) != 1
        or sum(event.get("type") == "turn.completed" for event in events) != 1
        or ready_messages != 1
    ):
        raise RuntimeError("Codex preflight lifecycle did not complete exactly once")
    matching_lines = [
        line
        for line in stderr.splitlines(keepends=True)
        if CODEX_SERVER_MODEL_MATCH_RE.search(line)
    ]
    if len(matching_lines) != 1:
        raise RuntimeError("Codex preflight lacks one server-selected model signal")
    match = CODEX_SERVER_MODEL_MATCH_RE.search(matching_lines[0])
    assert match is not None
    observed_model = match.group(1).decode("ascii")
    if observed_model != expected_model:
        raise RuntimeError("Codex preflight server selected the wrong model")
    lowered_stderr = stderr.lower()
    if (
        b" while requested model was " in lowered_stderr
        or b"model rerouted" in lowered_stderr
        or b"highriskcyberactivity" in lowered_stderr
        or b" fallback" in lowered_stderr
    ):
        raise RuntimeError("Codex preflight reported a model reroute or fallback")
    return observed_model, hashlib.sha256(matching_lines[0]).hexdigest()


def _disable_same_uid_process_inspection() -> None:
    """Prevent the provider child from ptracing or duplicating supervisor FDs."""

    pr_set_dumpable = 4
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(pr_set_dumpable, 0, 0, 0, 0) != 0:
        error = ctypes.get_errno()
        raise RuntimeError(
            f"could not disable same-UID supervisor inspection: errno {error}"
        )


def _model_preflight(provider: str, channel: TrustedModelEvidenceChannel) -> int:
    """Run the pinned provider in an empty identity-only auth boundary."""

    if provider == "codex":
        expected_model = "gpt-5.6-sol"
        expected_effort: str | None = "xhigh"
        _validate_codex_catalog()
        command = _codex_preflight_command(expected_model, expected_effort)
    else:
        expected_model = "claude-fable-5"
        expected_effort = None
        command = [
            "claude",
            "--print",
            "--output-format", "stream-json",
            "--verbose",
            "--model", expected_model,
            "--tools", "",
            "--strict-mcp-config",
            "--mcp-config", '{"mcpServers":{}}',
            "--safe-mode",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--permission-mode", "plan",
            "--setting-sources", "user",
            "--settings", '{"disableAllHooks":true,"enableAllProjectMcpServers":false}',
            "--no-chrome",
            "Reply with exactly READY and do not perform any other action.",
        ]
    sync_path = Path("/home/worker/provider-auth-preflight-sync.json")
    credential_sync = ProviderCredentialSync(provider, sync_path)
    credential_sync.initialize(session_overlays=False)
    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=180,
            cwd=Path("/opt/gas-city/model-preflight"),
            env=_model_preflight_environment(provider),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{provider} model preflight could not complete") from exc
    if (
        len(result.stdout) > MODEL_EVIDENCE_MAX_BYTES
        or len(result.stderr) > MODEL_EVIDENCE_MAX_BYTES
    ):
        raise RuntimeError(f"{provider} model preflight exceeded its output bound")
    if result.returncode != 0:
        raise RuntimeError(f"{provider} model preflight exited unsuccessfully")
    if provider == "codex":
        observed_model, observed_event_sha256 = _validate_codex_preflight(
            result.stdout,
            result.stderr,
            expected_model=expected_model,
        )
        channel.send_evidence(
            expected_model=expected_model,
            expected_effort=expected_effort,
            observed_model=observed_model,
            observed_effort=expected_effort,
            provider_exit_code=0,
            event_sha256=observed_event_sha256,
            transcript_sha256=hashlib.sha256(
                result.stdout + b"\x00" + result.stderr
            ).hexdigest(),
            transcript_locator="in-memory:codex-exec-jsonl+server-model-log",
            tool_free=True,
        )
        return 0
    observed_model: str | None = None
    observed_event_sha256: str | None = None
    for raw_line in result.stdout.splitlines(keepends=True):
        if not raw_line.strip():
            continue
        event = _strict_json_object(raw_line.rstrip(b"\r\n"), "Claude preflight event")
        if _event_contains_tool_use(event):
            raise RuntimeError("Claude preflight emitted a tool-use event")
        if is_claude_refusal_fallback(provider, event):
            raise RuntimeError("Claude preflight reported model fallback")
        receipt = extract_receipt(provider, event)
        if receipt is None and is_model_receipt_event(provider, event):
            raise RuntimeError("Claude preflight assistant event lacks model identity")
        if receipt is None:
            continue
        model, effort = receipt
        if model != expected_model or effort is not expected_effort:
            raise RuntimeError("Claude preflight observed the wrong model")
        if observed_model is not None and observed_model != model:
            raise RuntimeError("Claude preflight model identity changed within one response")
        observed_model = model
        observed_event_sha256 = hashlib.sha256(raw_line).hexdigest()
    if observed_model is None or observed_event_sha256 is None:
        raise RuntimeError("Claude preflight emitted no provider-authored model identity")
    channel.send_evidence(
        expected_model=expected_model,
        expected_effort=expected_effort,
        observed_model=observed_model,
        observed_effort=None,
        provider_exit_code=0,
        event_sha256=observed_event_sha256,
        transcript_sha256=hashlib.sha256(result.stdout).hexdigest(),
        transcript_locator="in-memory:claude-stream-json",
        tool_free=True,
    )
    return 0


def terminate_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def transcript_snapshot(root: Path) -> dict[Path, int]:
    snapshot: dict[Path, int] = {}
    for path in root.rglob("*.jsonl"):
        try:
            snapshot[path] = path.stat().st_size
        except OSError:
            continue
    return snapshot


def main(argv: list[str]) -> int:
    preparation_only = len(argv) == 2 and argv[1] == "aegis-prepare"
    model_preflight = (
        len(argv) == 3
        and argv[1] == "model-preflight"
        and argv[2] in {"claude", "codex"}
    )
    if not preparation_only and not model_preflight and (
        len(argv) < 2 or argv[1] not in {"claude", "codex"}
    ):
        print(
            "provider-supervisor requires claude, codex, model-preflight, or exact aegis-prepare",
            file=sys.stderr,
        )
        return 64

    if preparation_only:
        try:
            authority_digest = validate_task_authority_environment()
            boundary_role = validate_worker_boundary()
            if (
                authority_digest is None
                or boundary_role != "aegis"
                or os.environ.get("GC_TEMPLATE") != AEGIS_POLECAT_TEMPLATE
            ):
                raise RuntimeError("pre-provider preparation is only valid for an Aegis polecat")
            validate_aegis_git_broker_environment(frozen_startup=False)
            prepare_dolt_credentials(boundary_role)
            has_work = _run_aegis_polecat_startup(authority_digest)
        except Exception as exc:  # noqa: BLE001 - trusted preparation fails closed.
            print(f"Aegis polecat pre-provider startup failed: {exc}", file=sys.stderr)
            return 71
        # The helper has already written a strict no_work or prepared receipt;
        # the host broker freezes and interprets it before any AI is launched.
        return 0 if has_work else AEGIS_POLECAT_STARTUP_NO_WORK_EXIT

    if model_preflight:
        provider = argv[2]
        channel: TrustedModelEvidenceChannel | None = None
        try:
            channel = TrustedModelEvidenceChannel(provider, "preflight")
            _disable_same_uid_process_inspection()
            return _model_preflight(provider, channel)
        except Exception as exc:  # noqa: BLE001 - preflight must fail closed.
            print(f"trusted model preflight failed: {exc}", file=sys.stderr)
            return 94
        finally:
            if channel is not None:
                channel.close()

    provider = argv[1]
    evidence_channel: TrustedModelEvidenceChannel | None = None
    evidence_required = os.environ.get("GC_MODEL_EVIDENCE_REQUIRED", "")
    if evidence_required == "true":
        try:
            evidence_channel = TrustedModelEvidenceChannel(provider, "session")
            _disable_same_uid_process_inspection()
        except RuntimeError as exc:
            print(f"trusted model evidence channel failed: {exc}", file=sys.stderr)
            return 94
    elif evidence_required or os.environ.get("GC_MODEL_EVIDENCE_SOCKET"):
        print("invalid partial trusted model evidence environment", file=sys.stderr)
        return 65
    expected_model = os.environ.get("GC_EXPECTED_MODEL", "")
    expected_effort = os.environ.get("GC_EXPECTED_EFFORT") or None
    transcript_root = Path(os.environ.get("GC_TRANSCRIPT_ROOT", ""))
    receipt_path = Path(os.environ.get("GC_MODEL_RECEIPT_PATH", "/run/gas-city/model-receipt.json"))
    sync_receipt_path = Path(os.environ.get("GC_PROVIDER_SYNC_RECEIPT_PATH", ""))
    timeout = int(os.environ.get("GC_MODEL_RECEIPT_TIMEOUT_SECONDS", "180"))
    expected_transcript_root = (
        WORKER_HOME_PATH
        / str(PROVIDER_LAYOUTS[provider]["home_directory"])
        / str(PROVIDER_LAYOUTS[provider]["transcript"])
    )
    provider_paths = {
        "GC_PROVIDER_HOME": PROVIDER_HOME_PATH,
        "GC_PROVIDER_CONFIG": PROVIDER_CONFIG_PATH,
        "GC_PROVIDER_SESSION": PROVIDER_SESSION_PATH,
    }
    locked_expected_model = "gpt-5.6-sol" if provider == "codex" else "claude-fable-5"
    locked_expected_effort = "xhigh" if provider == "codex" else None
    if (
        expected_model != locked_expected_model
        or expected_effort != locked_expected_effort
        or transcript_root != expected_transcript_root
        or sync_receipt_path != PROVIDER_SYNC_RECEIPT_PATH
        or timeout < 1
        or any(Path(os.environ.get(name, "")) != expected for name, expected in provider_paths.items())
    ):
        print("invalid model-guard environment", file=sys.stderr)
        return 65
    try:
        authority_digest = validate_task_authority_environment()
    except Exception as exc:  # noqa: BLE001 - worker startup must fail closed.
        print(f"invalid task-authority environment: {exc}", file=sys.stderr)
        return 68
    try:
        boundary_role = validate_worker_boundary()
    except Exception as exc:  # noqa: BLE001 - endpoint boundary must fail closed.
        print(f"invalid worker endpoint boundary: {exc}", file=sys.stderr)
        return 71

    try:
        prepare_dolt_credentials(boundary_role)
    except RuntimeError as exc:
        print(f"could not prepare scoped Dolt credentials: {exc}", file=sys.stderr)
        return 66

    try:
        github_delivery_expires = configure_github_delivery()
    except RuntimeError as exc:
        print(f"could not read GitHub delivery credential: {exc}", file=sys.stderr)
        return 67

    if authority_digest is not None:
        try:
            is_polecat = os.environ.get("GC_TEMPLATE") == AEGIS_POLECAT_TEMPLATE
            git_broker_mode = _required_environment("AEGIS_GIT_BROKER_MODE")
            if git_broker_mode == "private":
                validate_aegis_git_broker_environment(frozen_startup=is_polecat)
            elif git_broker_mode == "none" and not is_polecat:
                forbidden = (
                    "GIT_DIR",
                    "GIT_WORK_TREE",
                    "AEGIS_GIT_BROKER_RECEIPT_PATH",
                    "AEGIS_GIT_BROKER_RECEIPT_SHA256",
                )
                if any(os.environ.get(name) for name in forbidden):
                    raise RuntimeError("non-repository Aegis worker carries partial Git broker state")
                probe = subprocess.run(
                    ["/usr/bin/git", "rev-parse", "--is-inside-work-tree"],
                    cwd=Path.cwd(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=10,
                )
                if probe.returncode == 0:
                    raise RuntimeError("repository-backed Aegis worker cannot disable the Git broker")
            else:
                raise RuntimeError("Aegis Git broker mode is invalid")
            if is_polecat:
                # Startup already ran in a provider-free container.  Recreate
                # only the immutable tmpfs launcher and consume the host-frozen
                # receipt; never claim or mutate branch metadata a second time.
                _prepare_local_aegis_launcher()
        except RuntimeError as exc:
            print(f"invalid Aegis private Git boundary: {exc}", file=sys.stderr)
            return 71

    try:
        command = _provider_command(provider, argv[2:])
        credential_sync = ProviderCredentialSync(provider, sync_receipt_path)
        credential_sync.initialize()
    except RuntimeError as exc:
        print(f"invalid provider credential or configuration boundary: {exc}", file=sys.stderr)
        return 69

    transcript_root.mkdir(parents=True, exist_ok=True)
    baseline = {path: path.stat().st_size for path in transcript_root.rglob("*.jsonl")}
    offsets = dict(baseline)
    transcript_identities = {
        path: (path.stat().st_dev, path.stat().st_ino) for path in baseline
    }
    started = time.monotonic()
    verified = False
    observed_model: str | None = None
    observed_effort: str | None = None
    observed_path: Path | None = None
    observed_event_sha256: str | None = None
    stable_snapshot: dict[Path, int] | None = None
    stable_since: float | None = None
    final_drain_seconds = 1.0
    last_authority_check = started
    github_delivery_deadline = (
        None
        if github_delivery_expires is None
        else started
        + max(
            0.0,
            (
                github_delivery_expires - dt.datetime.now(dt.timezone.utc)
            ).total_seconds()
            - 5 * 60,
        )
    )

    process = subprocess.Popen(command, start_new_session=True)
    try:
        while True:
            now = time.monotonic()
            if github_delivery_deadline is not None and now >= github_delivery_deadline:
                write_receipt(
                    receipt_path,
                    {
                        "schema_version": 1,
                        "status": "rejected",
                        "provider": provider,
                        "expected_model": expected_model,
                        "expected_effort": expected_effort,
                        "reason": "github_delivery_token_expiring",
                    },
                )
                print(
                    "GitHub delivery guard stopped the worker before token expiry",
                    file=sys.stderr,
                )
                terminate_group(process)
                return 95
            try:
                credential_sync.sync()
            except RuntimeError as exc:
                write_receipt(
                    receipt_path,
                    {
                        "schema_version": 1,
                        "status": "rejected",
                        "provider": provider,
                        "expected_model": expected_model,
                        "expected_effort": expected_effort,
                        "reason": "provider_credential_sync_failed",
                        "error": str(exc),
                    },
                )
                print("provider credential synchronization failed", file=sys.stderr)
                terminate_group(process)
                return 93
            if authority_digest is not None and now - last_authority_check >= 1.0:
                last_authority_check = now
                try:
                    live_authority_digest = validate_task_authority_environment()
                except Exception as exc:  # noqa: BLE001 - authority drift kills the worker.
                    write_receipt(
                        receipt_path,
                        {
                            "schema_version": 1,
                            "status": "rejected",
                            "provider": provider,
                            "expected_model": expected_model,
                            "expected_effort": expected_effort,
                            "reason": "task_authority_invalid_or_changed",
                            "error": str(exc),
                        },
                    )
                    print("task-authority guard rejected the live receipt", file=sys.stderr)
                    terminate_group(process)
                    return 92
                if live_authority_digest != authority_digest:
                    write_receipt(
                        receipt_path,
                        {
                            "schema_version": 1,
                            "status": "rejected",
                            "provider": provider,
                            "expected_model": expected_model,
                            "expected_effort": expected_effort,
                            "reason": "task_authority_digest_changed",
                        },
                    )
                    print("task-authority guard rejected receipt replacement", file=sys.stderr)
                    terminate_group(process)
                    return 92
            provider_exited = process.poll() is not None
            for path in sorted(transcript_root.rglob("*.jsonl")):
                offset = offsets.get(path, 0)
                try:
                    path_info = path.stat()
                    size = path_info.st_size
                    identity = (path_info.st_dev, path_info.st_ino)
                    previous_identity = transcript_identities.setdefault(path, identity)
                    if identity != previous_identity:
                        write_receipt(
                            receipt_path,
                            {
                                "schema_version": 1,
                                "status": "rejected",
                                "provider": provider,
                                "expected_model": expected_model,
                                "expected_effort": expected_effort,
                                "transcript": str(path),
                                "reason": "transcript_replaced",
                            },
                        )
                        print("model guard rejected transcript replacement", file=sys.stderr)
                        terminate_group(process)
                        return 90
                    if size < offset:
                        write_receipt(
                            receipt_path,
                            {
                                "schema_version": 1,
                                "status": "rejected",
                                "provider": provider,
                                "expected_model": expected_model,
                                "expected_effort": expected_effort,
                                "transcript": str(path),
                                "reason": "transcript_truncated",
                            },
                        )
                        print("model guard rejected transcript truncation", file=sys.stderr)
                        terminate_group(process)
                        return 90
                    with path.open("rb") as stream:
                        stream.seek(offset)
                        while True:
                            line_start = stream.tell()
                            line = stream.readline()
                            if not line:
                                break
                            if not line.endswith(b"\n") and not provider_exited:
                                stream.seek(line_start)
                                break
                            try:
                                event = json.loads(line.decode("utf-8"))
                            except (UnicodeDecodeError, json.JSONDecodeError):
                                write_receipt(
                                    receipt_path,
                                    {
                                        "schema_version": 1,
                                        "status": "rejected",
                                        "provider": provider,
                                        "expected_model": expected_model,
                                        "expected_effort": expected_effort,
                                        "transcript": str(path),
                                        "reason": "invalid_transcript_jsonl",
                                    },
                                )
                                print(
                                    f"model guard rejected malformed {provider} transcript",
                                    file=sys.stderr,
                                )
                                terminate_group(process)
                                return 90
                            if not isinstance(event, dict):
                                write_receipt(
                                    receipt_path,
                                    {
                                        "schema_version": 1,
                                        "status": "rejected",
                                        "provider": provider,
                                        "expected_model": expected_model,
                                        "expected_effort": expected_effort,
                                        "transcript": str(path),
                                        "reason": "invalid_transcript_record",
                                    },
                                )
                                terminate_group(process)
                                return 90
                            refusal_fallback = is_claude_refusal_fallback(provider, event)
                            receipt = extract_receipt(provider, event)
                            if refusal_fallback:
                                fallback_model = event.get("fallbackModel")
                                observed_model = (
                                    fallback_model
                                    if isinstance(fallback_model, str)
                                    else "model_refusal_fallback"
                                )
                                observed_effort = None
                                observed_path = path
                                observed_event_sha256 = hashlib.sha256(line).hexdigest()
                                receipt = (observed_model, None)
                            if receipt is None and is_model_receipt_event(provider, event):
                                write_receipt(
                                    receipt_path,
                                    {
                                        "schema_version": 1,
                                        "status": "rejected",
                                        "provider": provider,
                                        "expected_model": expected_model,
                                        "expected_effort": expected_effort,
                                        "transcript": str(path),
                                        "reason": "model_receipt_event_lacks_metadata",
                                    },
                                )
                                print(
                                    f"model guard rejected incomplete {provider} receipt event",
                                    file=sys.stderr,
                                )
                                terminate_group(process)
                                return 91
                            if receipt is None:
                                continue
                            observed_model, observed_effort = receipt
                            observed_path = path
                            observed_event_sha256 = hashlib.sha256(line).hexdigest()
                            valid = not refusal_fallback and observed_model == expected_model
                            if expected_effort is not None:
                                valid = valid and observed_effort == expected_effort
                            if not valid:
                                write_receipt(
                                    receipt_path,
                                    {
                                        "schema_version": 1,
                                        "status": "rejected",
                                        "provider": provider,
                                        "expected_model": expected_model,
                                        "expected_effort": expected_effort,
                                        "observed_model": observed_model,
                                        "observed_effort": observed_effort,
                                        "transcript": str(path),
                                        "reason": (
                                            "model_refusal_fallback"
                                            if refusal_fallback
                                            else "model_or_effort_mismatch"
                                        ),
                                    },
                                )
                                print(
                                    f"model guard rejected {provider}: "
                                    f"model={observed_model!r} effort={observed_effort!r}",
                                    file=sys.stderr,
                                )
                                terminate_group(process)
                                return 86
                            verified = True
                        offsets[path] = stream.tell()
                except (FileNotFoundError, OSError):
                    continue

            if process.poll() is not None:
                snapshot = transcript_snapshot(transcript_root)
                now = time.monotonic()
                if snapshot != stable_snapshot:
                    stable_snapshot = snapshot
                    stable_since = now
                elif stable_since is not None and now - stable_since >= final_drain_seconds:
                    break
                time.sleep(0.1)
                continue
            if not verified and time.monotonic() - started >= timeout:
                write_receipt(
                    receipt_path,
                    {
                        "schema_version": 1,
                        "status": "rejected",
                        "provider": provider,
                        "expected_model": expected_model,
                        "expected_effort": expected_effort,
                        "reason": "model_receipt_timeout",
                    },
                )
                print(f"model guard timed out waiting for a {provider} receipt", file=sys.stderr)
                terminate_group(process)
                return 87
            time.sleep(0.2)

        return_code = process.wait()
        provider_exit_code = (
            return_code if return_code >= 0 else min(255, 128 + abs(return_code))
        )
        if not verified:
            write_receipt(
                receipt_path,
                {
                    "schema_version": 1,
                    "status": "rejected",
                    "provider": provider,
                    "expected_model": expected_model,
                    "expected_effort": expected_effort,
                    "reason": "provider_exited_without_model_receipt",
                    "provider_exit_code": provider_exit_code,
                },
            )
            return 88

        assert observed_path is not None and observed_event_sha256 is not None
        try:
            transcript_content = observed_path.read_bytes()
            if not any(
                hashlib.sha256(line).hexdigest() == observed_event_sha256
                for line in transcript_content.splitlines(keepends=True)
            ):
                raise RuntimeError("verified model event is absent from final transcript")
            digest = hashlib.sha256(transcript_content).hexdigest()
        except (OSError, RuntimeError) as exc:
            write_receipt(
                receipt_path,
                {
                    "schema_version": 1,
                    "status": "rejected",
                    "provider": provider,
                    "expected_model": expected_model,
                    "expected_effort": expected_effort,
                    "reason": "verified_transcript_unavailable",
                    "error": str(exc),
                },
            )
            return 89
        if evidence_channel is not None:
            try:
                evidence_channel.send_evidence(
                    expected_model=expected_model,
                    expected_effort=expected_effort,
                    observed_model=observed_model,
                    observed_effort=observed_effort,
                    provider_exit_code=provider_exit_code,
                    event_sha256=observed_event_sha256,
                    transcript_sha256=digest,
                    transcript_locator=str(observed_path),
                    tool_free=False,
                )
            except (OSError, RuntimeError) as exc:
                print(f"host model evidence delivery failed: {exc}", file=sys.stderr)
                return 94
        write_receipt(
            receipt_path,
            {
                "schema_version": 1,
                "status": "verified",
                "provider": provider,
                "expected_model": expected_model,
                "expected_effort": expected_effort,
                "observed_model": observed_model,
                "observed_effort": observed_effort,
                "transcript": str(observed_path),
                "transcript_sha256": digest,
                "provider_exit_code": provider_exit_code,
            },
        )
        return provider_exit_code
    finally:
        terminate_group(process)
        try:
            credential_sync.sync(final=True)
        except RuntimeError as exc:
            write_receipt(
                receipt_path,
                {
                    "schema_version": 1,
                    "status": "rejected",
                    "provider": provider,
                    "expected_model": expected_model,
                    "expected_effort": expected_effort,
                    "reason": "provider_credential_final_sync_failed",
                    "error": str(exc),
                },
            )
            print("provider credential final synchronization failed", file=sys.stderr)
            return 93
        finally:
            if evidence_channel is not None:
                evidence_channel.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
