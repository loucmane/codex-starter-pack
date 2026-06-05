"""Pinned Taskmaster CLI toolchain evidence for reconcile apply validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

TASKMASTER_PACKAGE_NAME = "task-master-ai"
TASKMASTER_PACKAGE_VERSION = "0.43.1"
TASKMASTER_INSTALL_SOURCE = "npm"
TASKMASTER_NODE_VERSION = "22"
TASKMASTER_CI_RUNNER_OS = "Linux"
TASKMASTER_CI_RUNNER_ARCH = "X64"
TASKMASTER_TOOLCHAIN_LOCK_VERSION = 1

_LOCK_PAYLOAD = {
    "lock_version": TASKMASTER_TOOLCHAIN_LOCK_VERSION,
    "package": TASKMASTER_PACKAGE_NAME,
    "version": TASKMASTER_PACKAGE_VERSION,
    "source": TASKMASTER_INSTALL_SOURCE,
    "node_version": TASKMASTER_NODE_VERSION,
}
TASKMASTER_PROVISIONING_LOCK_ID = hashlib.sha256(
    json.dumps(_LOCK_PAYLOAD, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

TOOLCHAIN_BINDING_FIELDS = (
    "task_master.package",
    "task_master.version",
    "task_master.source",
    "task_master.install_spec",
    "provisioning.lock_id",
    "provisioning.lock_version",
    "runtime.node_major",
    "runtime.python_major_minor",
    "runner.os",
    "runner.arch",
)


class TaskmasterToolchainError(ValueError):
    """Raised when Taskmaster toolchain evidence cannot be captured or compared."""


def taskmaster_install_spec() -> str:
    return f"{TASKMASTER_PACKAGE_NAME}@{TASKMASTER_PACKAGE_VERSION}"


def build_taskmaster_toolchain_evidence(
    env: Mapping[str, str],
    *,
    task_master_version: str,
    node_version: str = "",
    npm_version: str = "",
    python_version: str = "",
) -> dict[str, Any]:
    """Build comparable evidence for the pinned Taskmaster CLI toolchain."""

    runtime_python = python_version or platform.python_version()
    node_major = _major(node_version)
    python_major_minor = ".".join(runtime_python.split(".")[:2]) if runtime_python else ""
    return {
        "record_type": "taskmaster_toolchain_evidence",
        "task_master": {
            "package": TASKMASTER_PACKAGE_NAME,
            "version": str(task_master_version).strip(),
            "expected_version": TASKMASTER_PACKAGE_VERSION,
            "source": TASKMASTER_INSTALL_SOURCE,
            "install_spec": taskmaster_install_spec(),
        },
        "provisioning": {
            "lock_id": TASKMASTER_PROVISIONING_LOCK_ID,
            "lock_version": TASKMASTER_TOOLCHAIN_LOCK_VERSION,
            "lock_payload": dict(_LOCK_PAYLOAD),
        },
        "runtime": {
            "node_version": str(node_version).strip(),
            "node_major": node_major,
            "expected_node_version": TASKMASTER_NODE_VERSION,
            "npm_version": str(npm_version).strip(),
            "python_version": runtime_python,
            "python_major_minor": python_major_minor,
        },
        "runner": {
            "provider": "github_actions" if env.get("GITHUB_ACTIONS") == "true" else "local",
            "os": str(env.get("RUNNER_OS") or platform.system()),
            "arch": str(env.get("RUNNER_ARCH") or platform.machine()),
            "image_os": str(env.get("ImageOS") or ""),
            "image_version": str(env.get("ImageVersion") or ""),
            "image_release": str(env.get("ImageRelease") or ""),
            "workflow": str(env.get("GITHUB_WORKFLOW") or ""),
            "run_id": str(env.get("GITHUB_RUN_ID") or ""),
            "run_attempt": str(env.get("GITHUB_RUN_ATTEMPT") or ""),
        },
    }


def capture_taskmaster_toolchain_evidence(
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Capture evidence from the currently provisioned CLI tools."""

    env = env or os.environ
    return build_taskmaster_toolchain_evidence(
        env,
        task_master_version=_run_version("task-master", "--version"),
        node_version=_run_version("node", "--version"),
        npm_version=_run_version("npm", "--version"),
        python_version=platform.python_version(),
    )


def build_validated_taskmaster_ci_toolchain_baseline(
    env: Mapping[str, str] | None = None,
    *,
    python_version: str = "",
) -> dict[str, Any]:
    """Build the source-controlled CI baseline used to detect toolchain drift."""

    baseline_env = dict(env or os.environ)
    baseline_env["RUNNER_OS"] = TASKMASTER_CI_RUNNER_OS
    baseline_env["RUNNER_ARCH"] = TASKMASTER_CI_RUNNER_ARCH
    evidence = build_taskmaster_toolchain_evidence(
        baseline_env,
        task_master_version=TASKMASTER_PACKAGE_VERSION,
        node_version=TASKMASTER_NODE_VERSION,
        python_version=python_version or platform.python_version(),
    )
    evidence["evidence_role"] = "validated_ci_baseline"
    evidence["baseline_source"] = {
        "type": "source_controlled_constants",
        "task_master_package_version": TASKMASTER_PACKAGE_VERSION,
        "task_master_install_spec": taskmaster_install_spec(),
        "task_master_node_version": TASKMASTER_NODE_VERSION,
        "runner_os": TASKMASTER_CI_RUNNER_OS,
        "runner_arch": TASKMASTER_CI_RUNNER_ARCH,
        "lock_id": TASKMASTER_PROVISIONING_LOCK_ID,
        "lock_version": TASKMASTER_TOOLCHAIN_LOCK_VERSION,
    }
    return evidence


def compare_taskmaster_toolchain_evidence(
    validated: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare validated and current toolchain evidence for future apply gating."""

    mismatches = []
    for field in TOOLCHAIN_BINDING_FIELDS:
        expected = _nested_get(validated, field)
        actual = _nested_get(current, field)
        if expected != actual:
            mismatches.append(
                {
                    "field": field,
                    "validated": expected,
                    "current": actual,
                }
            )
    return {
        "record_type": "taskmaster_toolchain_comparison",
        "matches": not mismatches,
        "mismatches": mismatches,
        "binding_fields": list(TOOLCHAIN_BINDING_FIELDS),
        "stale_if_mismatch": True,
    }


def _run_version(*args: str) -> str:
    result = subprocess.run(
        list(args),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise TaskmasterToolchainError(result.stderr or result.stdout)
    return result.stdout.strip()


def _major(version: str) -> str:
    version = version.strip().lstrip("v")
    return version.split(".", 1)[0] if version else ""


def _nested_get(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("install-spec")
    subparsers.add_parser("lock-id")
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.command == "install-spec":
        print(taskmaster_install_spec())
        return 0
    if args.command == "lock-id":
        print(TASKMASTER_PROVISIONING_LOCK_ID)
        return 0
    if args.command == "capture":
        evidence = capture_taskmaster_toolchain_evidence(os.environ)
        payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
