#!/usr/bin/env python3
"""Fail-closed pre-provider bridge for one Aegis Gas Town polecat.

The provider must never choose its source work from ``GC_BEAD_ID``.  Gas City
atomically claims a formula step; this bridge proves the claimed graph back to
its single durable source task, prepares the existing outer polecat worktree,
and starts Aegis from that explicit Bead before an AI process is launched.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any, Callable, Mapping, Sequence


HELPER_PATH = Path("/opt/gas-city/aegis-polecat-startup.py")
GC_PATH = Path("/usr/local/bin/gc")
BD_PATH = Path("/usr/local/bin/bd")
GIT_PATH = Path("/usr/bin/git")
PYTHON_PATH = Path("/usr/bin/python3")
RIG_ROOT = Path("/home/loucmane/codex")
GIT_COMMON_DIR = Path("/run/gas-city-git/private.git")
CITY_ROOT = Path("/home/loucmane/gas-city")
POLECAT_WORKTREE_ROOT = CITY_ROOT / ".gc/worktrees/aegis/polecats"
RECEIPT_PATH = Path("/run/gas-city/aegis-startup-receipt.json")
GIT_BROKER_RECEIPT_PATH = Path("/run/gas-city-trusted/git-broker.json")
AUTHORITY_PATH = Path("/run/gas-city/authority/aegis.json")
TASK_AUTHORITY_RUNTIME_PATH = Path("/opt/gas-city/task-authority.py")
AEGIS_RUNTIME_ARTIFACT_PATH = Path("/opt/gas-city/aegis-runtime.whl")
AEGIS_RUNTIME_SHIM_PATH = Path("/opt/gas-city/aegis-runtime-shim.py")

EXPECTED_RIG = "aegis"
EXPECTED_PREFIX = "ags"
EXPECTED_DATABASE = "aegis_beads"
EXPECTED_TEMPLATE = "aegis/gastown.polecat"
EXPECTED_ROUTE = "aegis/gastown.polecat"
EXPECTED_BASE_BRANCH = "main"
EXPECTED_FORMULA = "mol-polecat-work"
EXPECTED_CORE_PACK_COMMIT = "f895c0ff47d6ee9334ed282a416387eb5b084d24"
EXPECTED_GASTOWN_PACK_COMMIT = "33d3a430a67d1782ad364556cb566bdb01d0afe3"
EXPECTED_UPSTREAM_FORMULA_SHA256 = (
    "86878dd7ae180e02905d88ac092944d2fece075ac22dab86dc54b59c10f6319e"
)

MAX_TOOL_BYTES = 256 * 1024 * 1024
MAX_HELPER_BYTES = 1024 * 1024
MAX_RUNTIME_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_RUNTIME_SHIM_BYTES = 256 * 1024
MAX_COMMAND_OUTPUT_BYTES = 1024 * 1024
MAX_STATE_BYTES = 1024 * 1024
CLAIM_ATTEMPTS = 3
CLAIM_RETRY_SECONDS = 2.0
NO_WORK_EXIT = 75

SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
BEAD_ID_RE = re.compile(r"ags-[A-Za-z0-9][A-Za-z0-9._-]{0,126}\Z")
SAFE_IDENTITY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}\Z")
POLECAT_ALIAS_RE = re.compile(
    r"aegis/gastown\.polecat_[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z"
)


class StartupError(RuntimeError):
    """The provider launch must stop because startup proof failed."""


@dataclass(frozen=True)
class RuntimePaths:
    helper: Path = HELPER_PATH
    gc: Path = GC_PATH
    bd: Path = BD_PATH
    git: Path = GIT_PATH
    python: Path = PYTHON_PATH
    city_root: Path = CITY_ROOT
    rig_root: Path = RIG_ROOT
    git_common_dir: Path = GIT_COMMON_DIR
    worktree_root: Path = POLECAT_WORKTREE_ROOT
    receipt: Path = RECEIPT_PATH
    git_broker_receipt: Path = GIT_BROKER_RECEIPT_PATH
    authority: Path = AUTHORITY_PATH
    task_authority_runtime: Path = TASK_AUTHORITY_RUNTIME_PATH
    runtime_artifact: Path = AEGIS_RUNTIME_ARTIFACT_PATH
    runtime_shim: Path = AEGIS_RUNTIME_SHIM_PATH
    image_uid: int = 0
    helper_mode: int = 0o444
    tool_mode: int = 0o555


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes


Runner = Callable[[Sequence[str], Path, set[int], int], CommandResult]


def _required(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name, "")
    if not value:
        raise StartupError(f"missing required Aegis polecat startup environment: {name}")
    return value


def _exact_environment(environment: Mapping[str, str], name: str, expected: str) -> str:
    value = _required(environment, name)
    if value != expected:
        raise StartupError(
            f"Aegis polecat startup identity mismatch for {name}: expected {expected!r}"
        )
    return value


def _digest(environment: Mapping[str, str], name: str) -> str:
    value = _required(environment, name)
    if SHA256_RE.fullmatch(value) is None:
        raise StartupError(f"{name} must be one lowercase SHA-256")
    return value


def _strict_json(content: bytes, label: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            if key in value:
                raise StartupError(f"{label} contains duplicate JSON key {key!r}")
            value[key] = item
        return value

    try:
        return json.loads(
            content.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda item: (_ for _ in ()).throw(
                StartupError(f"{label} contains non-finite JSON {item!r}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise StartupError(f"{label} is not strict UTF-8 JSON") from exc


def _verified_image_file(
    path: Path,
    expected_digest: str,
    *,
    expected_uid: int,
    expected_mode: int,
    maximum_bytes: int,
    label: str,
) -> str:
    if not path.is_absolute() or ".." in path.parts:
        raise StartupError(f"{label} path is not one safe absolute path")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production workers are Linux.
        raise StartupError(f"{label} cannot be opened without symlink protection")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | no_follow)
    except OSError as exc:
        raise StartupError(f"{label} cannot be opened") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != expected_uid
            or stat.S_IMODE(before.st_mode) != expected_mode
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > maximum_bytes
        ):
            raise StartupError(
                f"{label} ownership, mode, link count, type, or size is invalid"
            )
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > maximum_bytes:
                raise StartupError(f"{label} exceeds its bounded size")
            digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
    if identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise StartupError(f"{label} changed while it was verified")
    observed = digest.hexdigest()
    if observed != expected_digest:
        raise StartupError(f"{label} SHA-256 does not match the deployment lock")
    return observed


def _subprocess_runner(
    command: Sequence[str],
    cwd: Path,
    allowed_codes: set[int],
    timeout: int,
) -> CommandResult:
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise StartupError(f"startup command could not execute: {command[0]}") from exc
    if len(result.stdout) > MAX_COMMAND_OUTPUT_BYTES or len(result.stderr) > MAX_COMMAND_OUTPUT_BYTES:
        raise StartupError(f"startup command exceeded its bounded output: {command[0]}")
    if result.returncode not in allowed_codes:
        detail = result.stderr.decode("utf-8", errors="replace").strip().splitlines()
        suffix = detail[0][:300] if detail else f"exit {result.returncode}"
        raise StartupError(f"startup command failed: {command[0]}: {suffix}")
    return CommandResult(result.returncode, result.stdout, result.stderr)


def _run_text(
    runner: Runner,
    command: Sequence[str],
    cwd: Path,
    *,
    allowed_codes: set[int] | None = None,
    timeout: int = 30,
) -> tuple[int, str]:
    result = runner(command, cwd, allowed_codes or {0}, timeout)
    try:
        text = result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StartupError(f"startup command returned non-UTF-8 output: {command[0]}") from exc
    return result.returncode, text.strip()


def _bd_show(runner: Runner, paths: RuntimePaths, cwd: Path, bead_id: str) -> dict[str, Any]:
    if BEAD_ID_RE.fullmatch(bead_id) is None:
        raise StartupError(f"unsafe Aegis Bead ID in startup graph: {bead_id!r}")
    _, output = _run_text(
        runner,
        [
            str(paths.bd),
            "--json",
            "--readonly",
            "-C",
            str(cwd),
            "show",
            "--id",
            bead_id,
        ],
        cwd,
        timeout=20,
    )
    payload = _strict_json(output.encode("utf-8"), f"read-only bd show for {bead_id}")
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise StartupError("read-only bd show must return exactly one issue object")
    issue = payload[0]
    if type(issue.get("id")) is not str or issue["id"] != bead_id:
        raise StartupError("read-only bd show returned a different issue identity")
    return issue


def _metadata(issue: Mapping[str, Any], label: str) -> dict[str, Any]:
    value = issue.get("metadata")
    if not isinstance(value, dict):
        raise StartupError(f"{label} must carry one metadata object")
    if any(type(key) is not str for key in value):
        raise StartupError(f"{label} metadata has a non-string key")
    return value


def _validate_identity(environment: Mapping[str, str], cwd: Path, paths: RuntimePaths) -> str:
    _exact_environment(environment, "GC_CITY_ROOT", str(paths.city_root))
    _exact_environment(environment, "GC_RIG", EXPECTED_RIG)
    _exact_environment(environment, "GC_RIG_ROOT", str(paths.rig_root))
    _exact_environment(environment, "GC_BEADS_PREFIX", EXPECTED_PREFIX)
    _exact_environment(environment, "GC_DOLT_DATABASE", EXPECTED_DATABASE)
    _exact_environment(environment, "BEADS_DOLT_SERVER_DATABASE", EXPECTED_DATABASE)
    _exact_environment(environment, "GC_TEMPLATE", EXPECTED_TEMPLATE)
    _exact_environment(environment, "GC_SESSION_ORIGIN", "ephemeral")
    _exact_environment(environment, "AEGIS_TASK_AUTHORITY_FILE", str(paths.authority))
    _exact_environment(
        environment,
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE",
        str(paths.task_authority_runtime),
    )
    _exact_environment(environment, "AEGIS_GC_EXECUTABLE", str(paths.gc))
    _exact_environment(environment, "AEGIS_BD_EXECUTABLE", str(paths.bd))
    _exact_environment(environment, "AEGIS_STARTUP_HELPER_FILE", str(paths.helper))
    _exact_environment(environment, "AEGIS_STARTUP_RECEIPT_PATH", str(paths.receipt))
    _exact_environment(
        environment,
        "AEGIS_GIT_BROKER_RECEIPT_PATH",
        str(paths.git_broker_receipt),
    )
    _exact_environment(
        environment,
        "AEGIS_RUNTIME_ARTIFACT_FILE",
        str(paths.runtime_artifact),
    )
    _exact_environment(environment, "AEGIS_RUNTIME_SHIM_FILE", str(paths.runtime_shim))
    _exact_environment(environment, "AEGIS_BASE_BRANCH", EXPECTED_BASE_BRANCH)
    _exact_environment(environment, "AEGIS_POLECAT_ROUTE", EXPECTED_ROUTE)
    _exact_environment(
        environment,
        "AEGIS_GASCITY_CORE_PACK_COMMIT",
        EXPECTED_CORE_PACK_COMMIT,
    )
    _exact_environment(
        environment,
        "AEGIS_GASTOWN_PACK_COMMIT",
        EXPECTED_GASTOWN_PACK_COMMIT,
    )
    _exact_environment(
        environment,
        "AEGIS_POLECAT_UPSTREAM_FORMULA_SHA256",
        EXPECTED_UPSTREAM_FORMULA_SHA256,
    )

    alias = _required(environment, "GC_ALIAS")
    if POLECAT_ALIAS_RE.fullmatch(alias) is None:
        raise StartupError("GC_ALIAS is not one exact Aegis Gastown polecat pool identity")
    session = _required(environment, "GC_SESSION_NAME")
    if SAFE_IDENTITY_RE.fullmatch(session) is None:
        raise StartupError("GC_SESSION_NAME has an unsafe identity shape")
    if _required(environment, "GC_AGENT") != session:
        raise StartupError("GC_AGENT and GC_SESSION_NAME do not identify the same polecat")
    if _required(environment, "BEADS_ACTOR") != session:
        raise StartupError("BEADS_ACTOR and GC_SESSION_NAME do not identify the same polecat")
    if not _required(environment, "GC_SESSION_ID"):
        raise StartupError("GC_SESSION_ID is required for an Aegis polecat")
    _exact_environment(environment, "GIT_DIR", str(paths.git_common_dir))
    _exact_environment(environment, "GIT_WORK_TREE", str(cwd))
    _exact_environment(environment, "GIT_CONFIG_NOSYSTEM", "1")
    _exact_environment(environment, "GIT_CONFIG_GLOBAL", "/dev/null")

    expected_worktree = paths.worktree_root / alias.rsplit("/", 1)[1]
    try:
        resolved = cwd.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise StartupError("Aegis polecat outer worktree does not exist") from exc
    if resolved != expected_worktree:
        raise StartupError(
            f"Aegis polecat outer worktree is {resolved}, expected {expected_worktree}"
        )
    return session


def _validate_git_broker(
    environment: Mapping[str, str], cwd: Path, paths: RuntimePaths
) -> dict[str, Any]:
    """Validate the host-generated receipt for the private Git boundary."""

    expected_digest = _digest(environment, "AEGIS_GIT_BROKER_RECEIPT_SHA256")
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:  # pragma: no cover - production workers are Linux.
        raise StartupError("Git broker receipt cannot be read without symlink protection")
    try:
        descriptor = os.open(
            paths.git_broker_receipt,
            os.O_RDONLY | os.O_CLOEXEC | no_follow,
        )
    except OSError as exc:
        raise StartupError("Git broker receipt cannot be opened") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) != 0o400
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > MAX_STATE_BYTES
        ):
            raise StartupError("Git broker receipt has unsafe file metadata")
        content = os.read(descriptor, MAX_STATE_BYTES + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        len(content) != after.st_size
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    ):
        raise StartupError("Git broker receipt changed while it was read")
    if hashlib.sha256(content).hexdigest() != expected_digest:
        raise StartupError("Git broker receipt digest does not match its host binding")
    value = _strict_json(content, "Git broker receipt")
    if not isinstance(value, dict):
        raise StartupError("Git broker receipt must be one JSON object")
    expected_keys = {
        "agent",
        "base_branch",
        "base_oid",
        "base_ref",
        "broker_id",
        "container_private_git_dir",
        "container_receipt_path",
        "created_at",
        "frozen_startup_receipt_path",
        "host_private_git_dir",
        "kind",
        "schema_version",
        "session_id_sha256",
        "source_branch",
        "source_common_dir",
        "source_git_dir",
        "source_ref",
        "source_refs_sha256",
        "starting_oid",
        "status",
        "worktree",
        "worktree_marker_sha256",
    }
    if set(value) != expected_keys:
        raise StartupError("Git broker receipt has an unexpected schema")
    session_digest = hashlib.sha256(
        _required(environment, "GC_SESSION_ID").encode("utf-8")
    ).hexdigest()
    expected = {
        "schema_version": 1,
        "kind": "aegis-private-git-broker",
        "status": "prepared",
        "agent": _required(environment, "GC_AGENT"),
        "session_id_sha256": session_digest,
        "worktree": str(cwd),
        "source_common_dir": str(paths.rig_root / ".git"),
        "base_branch": EXPECTED_BASE_BRANCH,
        "base_ref": "refs/remotes/origin/main",
        "container_private_git_dir": str(paths.git_common_dir),
        "container_receipt_path": str(paths.git_broker_receipt),
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise StartupError("Git broker receipt does not bind this exact worker")
    for name in (
        "base_oid",
        "starting_oid",
    ):
        if not isinstance(value.get(name), str) or GIT_SHA_RE.fullmatch(value[name]) is None:
            raise StartupError(f"Git broker receipt {name} is not one Git object")
    for name in ("source_refs_sha256", "worktree_marker_sha256"):
        if not isinstance(value.get(name), str) or SHA256_RE.fullmatch(value[name]) is None:
            raise StartupError(f"Git broker receipt {name} is not one SHA-256")
    source_branch = value.get("source_branch")
    if (
        not isinstance(source_branch, str)
        or not source_branch.startswith("gc-")
        or value.get("source_ref") != f"refs/heads/{source_branch}"
    ):
        raise StartupError("Git broker source branch is not one Gas City pool branch")
    if not isinstance(value.get("broker_id"), str):
        raise StartupError("Git broker identity is missing")
    try:
        if str(uuid.UUID(value["broker_id"])) != value["broker_id"]:
            raise ValueError("non-canonical UUID")
    except (ValueError, AttributeError) as exc:
        raise StartupError("Git broker identity is not one canonical UUID") from exc
    return {**value, "receipt_sha256": expected_digest}


def _verify_runtime(environment: Mapping[str, str], paths: RuntimePaths) -> dict[str, str]:
    helper_digest = _digest(environment, "AEGIS_STARTUP_HELPER_SHA256")
    gc_digest = _digest(environment, "AEGIS_GC_SHA256")
    bd_digest = _digest(environment, "AEGIS_BD_SHA256")
    formula_digest = _digest(environment, "AEGIS_POLECAT_FORMULA_SHA256")
    authority_digest = _digest(environment, "AEGIS_TASK_AUTHORITY_RECEIPT_SHA256")
    runtime_artifact_digest = _digest(environment, "AEGIS_RUNTIME_ARTIFACT_SHA256")
    runtime_shim_digest = _digest(environment, "AEGIS_RUNTIME_SHIM_SHA256")
    local_launcher_digest = _digest(environment, "AEGIS_LOCAL_LAUNCHER_SHA256")
    _digest(environment, "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256")
    _verified_image_file(
        paths.helper,
        helper_digest,
        expected_uid=paths.image_uid,
        expected_mode=paths.helper_mode,
        maximum_bytes=MAX_HELPER_BYTES,
        label="immutable Aegis polecat startup helper",
    )
    _verified_image_file(
        paths.gc,
        gc_digest,
        expected_uid=paths.image_uid,
        expected_mode=paths.tool_mode,
        maximum_bytes=MAX_TOOL_BYTES,
        label="pinned gc executable",
    )
    _verified_image_file(
        paths.bd,
        bd_digest,
        expected_uid=paths.image_uid,
        expected_mode=paths.tool_mode,
        maximum_bytes=MAX_TOOL_BYTES,
        label="pinned bd executable",
    )
    _verified_image_file(
        paths.runtime_artifact,
        runtime_artifact_digest,
        expected_uid=paths.image_uid,
        expected_mode=paths.helper_mode,
        maximum_bytes=MAX_RUNTIME_ARTIFACT_BYTES,
        label="immutable offline Aegis runtime artifact",
    )
    _verified_image_file(
        paths.runtime_shim,
        runtime_shim_digest,
        expected_uid=paths.image_uid,
        expected_mode=paths.helper_mode,
        maximum_bytes=MAX_RUNTIME_SHIM_BYTES,
        label="immutable Aegis runtime shim",
    )
    return {
        "helper_sha256": helper_digest,
        "gc_sha256": gc_digest,
        "bd_sha256": bd_digest,
        "formula_sha256": formula_digest,
        "authority_sha256": authority_digest,
        "runtime_artifact_sha256": runtime_artifact_digest,
        "runtime_shim_sha256": runtime_shim_digest,
        "local_launcher_sha256": local_launcher_digest,
    }


def _claim_formula_step(
    runner: Runner,
    paths: RuntimePaths,
    cwd: Path,
    session: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    last_error: StartupError | None = None
    for attempt in range(1, CLAIM_ATTEMPTS + 1):
        try:
            result = runner(
                [str(paths.gc), "hook", "--claim", "--json"],
                cwd,
                {0, 1},
                20,
            )
            if len(result.stdout) > MAX_COMMAND_OUTPUT_BYTES:
                raise StartupError("gc hook claim output exceeded its bound")
            payload = _strict_json(result.stdout, "gc hook claim result")
            if not isinstance(payload, dict):
                raise StartupError("gc hook claim result must be one JSON object")
            required = {
                "schema_version": "1",
                "ok": True,
                "command": "hook",
            }
            if any(payload.get(key) != value for key, value in required.items()):
                raise StartupError("gc hook claim result has an unexpected protocol identity")
            action = payload.get("action")
            if action == "drain":
                if payload.get("reason") != "no_work" or result.returncode not in {0, 1}:
                    raise StartupError("gc hook drain result has an invalid reason or exit code")
                return None, payload
            if action != "work" or result.returncode != 0:
                raise StartupError("gc hook claim did not return one successful work action")
            bead_id = payload.get("bead_id")
            if type(bead_id) is not str or BEAD_ID_RE.fullmatch(bead_id) is None:
                raise StartupError("gc hook claim returned an unsafe or missing Bead ID")
            if payload.get("assignee") != session:
                raise StartupError("gc hook claim assigned the formula step to another identity")
            if payload.get("route") != EXPECTED_ROUTE:
                raise StartupError("gc hook claim escaped the exact Aegis polecat route")
            if payload.get("reason") not in {
                "claimed",
                "existing_assignment",
                "ready_assignment",
            }:
                raise StartupError("gc hook claim returned an unsupported work reason")
            return payload, payload
        except StartupError as exc:
            last_error = exc
            if attempt < CLAIM_ATTEMPTS:
                time.sleep(CLAIM_RETRY_SECONDS)
    raise StartupError(f"gc hook claim failed after {CLAIM_ATTEMPTS} attempts: {last_error}")


def _validate_formula_graph(
    runner: Runner,
    paths: RuntimePaths,
    cwd: Path,
    claim: Mapping[str, Any],
    session: str,
    formula_digest: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    step_id = str(claim["bead_id"])
    step = _bd_show(runner, paths, cwd, step_id)
    step_metadata = _metadata(step, "claimed formula step")
    step_ref = step_metadata.get("gc.step_ref")
    root_id = step_metadata.get("gc.root_bead_id")
    expected_step_status = (
        "open" if claim.get("reason") == "ready_assignment" else "in_progress"
    )
    if (
        step.get("status") != expected_step_status
        or step.get("assignee") != session
        or step.get("issue_type") != "task"
        or type(step_ref) is not str
        or not step_ref.startswith(f"{EXPECTED_FORMULA}.")
        or type(root_id) is not str
        or BEAD_ID_RE.fullmatch(root_id) is None
        or step_metadata.get("gc.routed_to") != EXPECTED_ROUTE
    ):
        raise StartupError(
            "claimed Bead does not have the exact status/owner/metadata for its "
            "Aegis mol-polecat-work claim reason"
        )
    if step.get("ephemeral") is True or step.get("no_history") is True:
        raise StartupError("claimed formula step has an unsupported storage class")

    root = _bd_show(runner, paths, cwd, root_id)
    root_metadata = _metadata(root, "formula root")
    input_convoy_id = root_metadata.get("gc.input_convoy_id")
    if (
        root.get("issue_type") != "task"
        or root.get("title") != EXPECTED_FORMULA
        or root_metadata.get("gc.kind") != "workflow"
        or root_metadata.get("gc.formula_contract") != "graph.v2"
        or root_metadata.get("gc.formula_hash") != formula_digest
        or type(input_convoy_id) is not str
        or BEAD_ID_RE.fullmatch(input_convoy_id) is None
    ):
        raise StartupError("claimed step does not belong to the pinned mol-polecat-work graph")

    convoy = _bd_show(runner, paths, cwd, input_convoy_id)
    if convoy.get("issue_type") != "convoy":
        raise StartupError("formula root input is not a convoy")
    _, convoy_output = _run_text(
        runner,
        [str(paths.gc), "convoy", "status", input_convoy_id, "--json"],
        cwd,
        timeout=20,
    )
    convoy_status = _strict_json(
        convoy_output.encode("utf-8"), "input convoy status"
    )
    if (
        not isinstance(convoy_status, dict)
        or convoy_status.get("schema_version") != "1"
        or convoy_status.get("ok") is not True
        or not isinstance(convoy_status.get("convoy"), dict)
        or convoy_status["convoy"].get("id") != input_convoy_id
        or not isinstance(convoy_status.get("children"), list)
        or len(convoy_status["children"]) != 1
        or not isinstance(convoy_status["children"][0], dict)
    ):
        raise StartupError("mol-polecat-work input convoy must have exactly one child")
    source_id = convoy_status["children"][0].get("id")
    if type(source_id) is not str or BEAD_ID_RE.fullmatch(source_id) is None:
        raise StartupError("input convoy child is not one safe Aegis source-work ID")

    source = _bd_show(runner, paths, cwd, source_id)
    if (
        source.get("issue_type") != "task"
        or source.get("status") != "in_progress"
        or source.get("assignee") != session
        or source.get("ephemeral", False) is not False
        or source.get("no_history", False) is not False
        or type(source.get("title")) is not str
        or not source["title"].strip()
    ):
        raise StartupError(
            "input convoy child is not one durable in_progress source task owned by this polecat"
        )
    _metadata(source, "source work task")
    return step, root, convoy, source


def _git(
    runner: Runner,
    paths: RuntimePaths,
    cwd: Path,
    *arguments: str,
    allowed_codes: set[int] | None = None,
    timeout: int = 60,
) -> tuple[int, str]:
    return _run_text(
        runner,
        [str(paths.git), "-C", str(cwd), *arguments],
        cwd,
        allowed_codes=allowed_codes,
        timeout=timeout,
    )


def _read_current_work(cwd: Path) -> dict[str, Any] | None:
    path = cwd / ".aegis/state/current-work.json"
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
        )
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise StartupError("Aegis current-work state cannot be opened safely") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > MAX_STATE_BYTES
        ):
            raise StartupError("Aegis current-work state has unsafe file metadata")
        content = os.read(descriptor, MAX_STATE_BYTES + 1)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if (
        len(content) != after.st_size
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    ):
        raise StartupError("Aegis current-work state changed while it was read")
    value = _strict_json(content, "Aegis current-work state")
    if not isinstance(value, dict):
        raise StartupError("Aegis current-work state must be one JSON object")
    return value


def _current_work_matches(value: Mapping[str, Any], source_id: str, branch: str) -> bool:
    task = value.get("task")
    branch_value = value.get("branch")
    return (
        isinstance(task, dict)
        and task.get("id") == source_id
        and task.get("source") == "beads"
        and isinstance(branch_value, dict)
        and branch_value.get("current") == branch
    )


def _git_ref_exists(
    runner: Runner, paths: RuntimePaths, cwd: Path, reference: str
) -> bool:
    code, _ = _git(
        runner,
        paths,
        cwd,
        "show-ref",
        "--verify",
        "--quiet",
        reference,
        allowed_codes={0, 1},
    )
    return code == 0


def _is_ancestor(
    runner: Runner, paths: RuntimePaths, cwd: Path, ancestor: str, descendant: str
) -> bool:
    code, _ = _git(
        runner,
        paths,
        cwd,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        allowed_codes={0, 1},
    )
    return code == 0


def _validate_git_boundary(runner: Runner, paths: RuntimePaths, cwd: Path) -> None:
    _, top = _git(runner, paths, cwd, "rev-parse", "--show-toplevel")
    _, common = _git(
        runner,
        paths,
        cwd,
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
    )
    try:
        top_path = Path(top).resolve(strict=True)
        common_path = Path(common).resolve(strict=True)
        expected_common = paths.git_common_dir.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise StartupError("could not canonicalize the Aegis git boundary") from exc
    if top_path != cwd or common_path != expected_common:
        raise StartupError("Aegis polecat worktree has the wrong top-level or git common dir")


def _prepare_branch(
    runner: Runner,
    paths: RuntimePaths,
    cwd: Path,
    source: dict[str, Any],
    session: str,
) -> tuple[str, str, bool]:
    source_id = str(source["id"])
    branch = f"polecat/{source_id}"
    metadata = _metadata(source, "source work task")
    metadata_branch = metadata.get("branch")
    metadata_workdir = metadata.get("work_dir")
    if (metadata_branch is None) != (metadata_workdir is None):
        raise StartupError("source task has a partial branch/work_dir metadata binding")
    metadata_target = metadata.get("target")
    if metadata_target not in {None, EXPECTED_BASE_BRANCH}:
        raise StartupError("source task target is not the exact Aegis base branch")
    if metadata_branch is not None and metadata_target != EXPECTED_BASE_BRANCH:
        raise StartupError("metadata-bound source task is missing the exact base target")

    _validate_git_boundary(runner, paths, cwd)
    _, current_branch = _git(runner, paths, cwd, "branch", "--show-current")
    current_work = _read_current_work(cwd)
    resume = current_work is not None
    if resume and not _current_work_matches(current_work, source_id, branch):
        raise StartupError("outer worktree contains Aegis current work for another Bead")
    if resume and current_branch != branch:
        raise StartupError("Aegis resume state and current git branch diverged")

    _, dirty = _git(
        runner,
        paths,
        cwd,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    initial_runtime_paths = {
        "?? .aegis/bin/aegis",
        "?? .aegis/bin/.runtime.lock",
    }
    dirty_without_runtime = [
        line for line in dirty.splitlines() if line not in initial_runtime_paths
    ]
    if dirty_without_runtime and not resume:
        raise StartupError("outer Gas City worktree is dirty before source-work preparation")

    _git(runner, paths, cwd, "fetch", "--prune", "origin", EXPECTED_BASE_BRANCH, timeout=120)
    base_ref = f"refs/remotes/origin/{EXPECTED_BASE_BRANCH}"
    if not _git_ref_exists(runner, paths, cwd, base_ref):
        raise StartupError("exact remote Aegis base branch is unavailable")
    _, base_head = _git(runner, paths, cwd, "rev-parse", base_ref)
    if GIT_SHA_RE.fullmatch(base_head) is None:
        raise StartupError("Aegis base branch did not resolve to one SHA-1 object")

    if metadata_branch is not None:
        if metadata_branch != branch or metadata_workdir != str(cwd):
            raise StartupError("source task branch/work_dir metadata diverges from this polecat")
        if not resume:
            local_ref = f"refs/heads/{branch}"
            remote_ref = f"refs/remotes/origin/{branch}"
            remote_exists = False
            code, _ = _git(
                runner,
                paths,
                cwd,
                "ls-remote",
                "--exit-code",
                "--heads",
                "origin",
                branch,
                allowed_codes={0, 2},
                timeout=120,
            )
            if code == 0:
                remote_exists = True
                _git(
                    runner,
                    paths,
                    cwd,
                    "fetch",
                    "origin",
                    f"+refs/heads/{branch}:{remote_ref}",
                    timeout=120,
                )
            local_exists = _git_ref_exists(runner, paths, cwd, local_ref)
            if not local_exists and not remote_exists:
                raise StartupError("metadata-bound polecat branch no longer exists")
            if local_exists:
                _git(runner, paths, cwd, "switch", branch)
            else:
                _git(runner, paths, cwd, "switch", "--track", "-c", branch, remote_ref)
            if remote_exists:
                if _is_ancestor(runner, paths, cwd, "HEAD", remote_ref):
                    _git(runner, paths, cwd, "merge", "--ff-only", remote_ref)
                elif not _is_ancestor(runner, paths, cwd, remote_ref, "HEAD"):
                    raise StartupError("local and remote polecat branches diverged")
    else:
        local_ref = f"refs/heads/{branch}"
        remote_ref = f"refs/remotes/origin/{branch}"
        remote_code, _ = _git(
            runner,
            paths,
            cwd,
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            branch,
            allowed_codes={0, 2},
            timeout=120,
        )
        if remote_code == 0:
            raise StartupError("unbound source task collides with an existing remote branch")
        if _git_ref_exists(runner, paths, cwd, remote_ref):
            raise StartupError("unbound source task collides with a cached remote branch")
        if _git_ref_exists(runner, paths, cwd, local_ref):
            _, existing_head = _git(runner, paths, cwd, "rev-parse", local_ref)
            if existing_head != base_head:
                raise StartupError("unbound source task collides with a non-base local branch")
            _git(runner, paths, cwd, "switch", branch)
        else:
            _git(runner, paths, cwd, "switch", "-c", branch, base_ref)
        _run_text(
            runner,
            [
                str(paths.gc),
                "bd",
                "update",
                source_id,
                "--set-metadata",
                f"branch={branch}",
                "--set-metadata",
                f"work_dir={cwd}",
                "--set-metadata",
                f"fork_sha={base_head}",
                "--set-metadata",
                f"target={EXPECTED_BASE_BRANCH}",
            ],
            cwd,
            timeout=20,
        )

    refreshed = _bd_show(runner, paths, cwd, source_id)
    refreshed_metadata = _metadata(refreshed, "refreshed source work task")
    if (
        refreshed.get("status") != "in_progress"
        or refreshed.get("assignee") != session
        or refreshed_metadata.get("branch") != branch
        or refreshed_metadata.get("work_dir") != str(cwd)
        or refreshed_metadata.get("target") != EXPECTED_BASE_BRANCH
    ):
        raise StartupError("source task changed during branch/work_dir compare-and-set")
    _, active_branch = _git(runner, paths, cwd, "branch", "--show-current")
    if active_branch != branch:
        raise StartupError("outer worktree did not enter the exact source-work branch")
    if not _is_ancestor(runner, paths, cwd, base_ref, "HEAD"):
        raise StartupError("polecat branch is not based on the exact Aegis base branch")
    _, head = _git(runner, paths, cwd, "rev-parse", "HEAD")
    if GIT_SHA_RE.fullmatch(head) is None:
        raise StartupError("prepared polecat branch did not resolve to one git object")
    return branch, head, resume


def _validate_local_aegis(path: Path, expected_digest: str) -> None:
    _verified_image_file(
        path,
        expected_digest,
        expected_uid=os.geteuid(),
        expected_mode=0o500,
        maximum_bytes=4096,
        label="target-local tmpfs Aegis launcher",
    )
    try:
        parent = path.parent.lstat()
    except OSError as exc:
        raise StartupError("target-local Aegis launcher directory is missing") from exc
    if (
        stat.S_ISLNK(parent.st_mode)
        or not stat.S_ISDIR(parent.st_mode)
        or parent.st_uid != os.geteuid()
        or stat.S_IMODE(parent.st_mode) != 0o700
    ):
        raise StartupError("target-local Aegis launcher directory is not private")


def _kickoff(
    runner: Runner,
    cwd: Path,
    source_id: str,
    branch: str,
    launcher_digest: str,
) -> None:
    executable = cwd / ".aegis/bin/aegis"
    _validate_local_aegis(executable, launcher_digest)
    _run_text(
        runner,
        [
            str(executable),
            "kickoff",
            "--target-dir",
            str(cwd),
            "--bead",
            source_id,
        ],
        cwd,
        timeout=120,
    )
    current = _read_current_work(cwd)
    if current is None or not _current_work_matches(current, source_id, branch):
        raise StartupError("Aegis kickoff did not bind current work to the source Bead")


def _secure_directory(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise StartupError(f"{label} is missing") from exc
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise StartupError(f"{label} must be one owner-only real directory")


def _write_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    _secure_directory(path.parent, "startup receipt directory")
    content = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(raw)
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OSError("short startup receipt write")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        if path.is_symlink():
            raise StartupError("startup receipt destination is a symlink")
        os.replace(temporary, path)
        temporary = None
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise StartupError("could not atomically write the startup receipt") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prepare(
    environment: Mapping[str, str],
    cwd: Path,
    *,
    paths: RuntimePaths = RuntimePaths(),
    runner: Runner = _subprocess_runner,
) -> dict[str, Any]:
    """Prepare one exact polecat session, returning the private receipt body."""

    session = _validate_identity(environment, cwd, paths)
    git_broker = _validate_git_broker(environment, cwd, paths)
    digests = _verify_runtime(environment, paths)
    claim, raw_claim = _claim_formula_step(runner, paths, cwd, session)
    common = {
        "schema_version": 1,
        "kind": "aegis-polecat-pre-provider-startup",
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "rig": EXPECTED_RIG,
        "template": EXPECTED_TEMPLATE,
        "route": EXPECTED_ROUTE,
        "assignee": session,
        "authority_receipt_sha256": digests["authority_sha256"],
        "gascity_core_pack_commit": EXPECTED_CORE_PACK_COMMIT,
        "gastown_pack_commit": EXPECTED_GASTOWN_PACK_COMMIT,
        "upstream_formula_sha256": EXPECTED_UPSTREAM_FORMULA_SHA256,
        "formula_sha256": digests["formula_sha256"],
        "startup_helper_sha256": digests["helper_sha256"],
        "gc_sha256": digests["gc_sha256"],
        "bd_sha256": digests["bd_sha256"],
        "runtime_artifact_sha256": digests["runtime_artifact_sha256"],
        "runtime_shim_sha256": digests["runtime_shim_sha256"],
        "local_launcher_sha256": digests["local_launcher_sha256"],
        "git_broker_id": git_broker["broker_id"],
        "git_broker_receipt_sha256": git_broker["receipt_sha256"],
        "git_source_branch": git_broker["source_branch"],
        "git_starting_oid": git_broker["starting_oid"],
        "git_source_common_dir": git_broker["source_common_dir"],
        "git_private_common_dir": git_broker["container_private_git_dir"],
    }
    if claim is None:
        receipt = {
            **common,
            "status": "no_work",
            "claim_action": raw_claim.get("action"),
            "claim_reason": raw_claim.get("reason"),
        }
        _write_receipt(paths.receipt, receipt)
        return receipt

    step, root, convoy, source = _validate_formula_graph(
        runner,
        paths,
        cwd,
        claim,
        session,
        digests["formula_sha256"],
    )
    source_id = str(source["id"])
    branch, git_head, resumed = _prepare_branch(
        runner, paths, cwd, source, session
    )
    _kickoff(
        runner,
        cwd,
        source_id,
        branch,
        digests["local_launcher_sha256"],
    )
    receipt = {
        **common,
        "status": "resumed" if resumed else "prepared",
        "claim_reason": claim.get("reason"),
        "claimed_step_id": step["id"],
        "formula_root_id": root["id"],
        "input_convoy_id": convoy["id"],
        "source_work_id": source_id,
        "source_title_sha256": hashlib.sha256(
            str(source["title"]).encode("utf-8")
        ).hexdigest(),
        "work_dir": str(cwd),
        "branch": branch,
        "base_branch": EXPECTED_BASE_BRANCH,
        "git_head": git_head,
    }
    _write_receipt(paths.receipt, receipt)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv)
    if arguments != [str(HELPER_PATH), "prepare"] and arguments != [
        "aegis-polecat-startup",
        "prepare",
    ]:
        print("aegis-polecat-startup requires the exact prepare action", file=sys.stderr)
        return 64
    try:
        receipt = prepare(os.environ, Path.cwd().resolve(strict=True))
    except Exception as exc:  # noqa: BLE001 - pre-provider startup fails closed.
        print(f"Aegis polecat pre-provider startup rejected: {exc}", file=sys.stderr)
        return 70
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return NO_WORK_EXIT if receipt.get("status") == "no_work" else 0


if __name__ == "__main__":
    raise SystemExit(main())
