from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

import pytest

from aegis_foundation import (
    gas_city_authority,
    gas_city_ops,
    task_authority,
    taskmaster_beads,
)

UTC = dt.timezone.utc


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _private_dir(path: Path) -> Path:
    if not path.exists():
        _private_dir(path.parent)
        path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _private_file(path: Path, content: bytes) -> Path:
    _private_dir(path.parent)
    path.write_bytes(content)
    path.chmod(0o600)
    return path


def _provision_runtime_lock(city: Path) -> dict[str, Any]:
    tool_bytes = {name: name.encode() for name in ("gc", "bd", "dolt")}
    for name, content in tool_bytes.items():
        tool = _private_file(city / "bin" / name, content)
        tool.chmod(0o555)
    control_plane_manifest = b'{"kind":"authority-test-control-plane","schema_version":1}\n'
    _private_file(city / "control-plane-manifest.json", control_plane_manifest)
    startup = {
        **gas_city_ops.AEGIS_POLECAT_STARTUP_FIXED_PATHS,
        "sha256": "1" * 64,
        "formula_sha256": "2" * 64,
        "upstream_formula_sha256": "3" * 64,
        "runtime_artifact_sha256": "4" * 64,
        "runtime_shim_sha256": "5" * 64,
        "local_launcher_sha256": hashlib.sha256(
            gas_city_ops.AEGIS_POLECAT_LOCAL_LAUNCHER_CONTENT
        ).hexdigest(),
    }
    lock: dict[str, Any] = {
        "schema_version": gas_city_ops.LOCK_SCHEMA_VERSION,
        "status": "staged_pending_provisioning",
        "tools": {
            name: {
                "version": {"gc": "1.3.5", "bd": "1.1.0", "dolt": "2.2.0"}[name],
                "binary_sha256": hashlib.sha256(content).hexdigest(),
                "archive_sha256": hashlib.sha256(b"archive-" + content).hexdigest(),
            }
            for name, content in tool_bytes.items()
        },
        "packs": {
            "gascity_core_bd": {"commit": "6" * 40},
            "gastown": {"commit": "7" * 40},
        },
        "task_authority_runtime": {
            "source_path": gas_city_ops.TASK_AUTHORITY_SOURCE_PATH,
            "image_path": gas_city_ops.TASK_AUTHORITY_IMAGE_PATH,
            "sha256": "8" * 64,
        },
        "aegis_polecat_startup": startup,
        "git_worktree_broker": {
            "source_path": gas_city_ops.GIT_WORKTREE_BROKER_SOURCE_PATH,
            "deployed_path": gas_city_ops.GIT_WORKTREE_BROKER_DEPLOYED_PATH,
            "sha256": "f" * 64,
        },
        "model_evidence_broker": {
            "source_path": gas_city_ops.MODEL_EVIDENCE_BROKER_SOURCE_PATH,
            "deployed_path": gas_city_ops.MODEL_EVIDENCE_BROKER_DEPLOYED_PATH,
            "sha256": "e" * 64,
        },
        "github_delivery": {
            "broker_source_path": gas_city_ops.GITHUB_DELIVERY_BROKER_SOURCE_PATH,
            "broker_deployed_path": gas_city_ops.GITHUB_DELIVERY_BROKER_DEPLOYED_PATH,
            "broker_sha256": "c" * 64,
            "repository": gas_city_ops.GITHUB_DELIVERY_REPOSITORY,
            "default_branch": "main",
            "permissions": gas_city_ops.GITHUB_DELIVERY_PERMISSIONS,
            "required_default_branch_rules": gas_city_ops.GITHUB_DELIVERY_REQUIRED_RULES,
            "maximum_lifetime_seconds": 3900,
        },
        "codex_preflight_catalog": {
            "source_path": gas_city_ops.CODEX_PREFLIGHT_CATALOG_SOURCE_PATH,
            "image_path": gas_city_ops.CODEX_PREFLIGHT_CATALOG_IMAGE_PATH,
            "sha256": "d" * 64,
            "upstream_source_tag": gas_city_ops.CODEX_PREFLIGHT_UPSTREAM_TAG,
            "upstream_source_commit": gas_city_ops.CODEX_PREFLIGHT_UPSTREAM_COMMIT,
            "advertised_tools": ["update_plan", "view_image"],
            "tool_invocation_policy": "zero",
        },
        "control_plane_manifest": {
            "path": "control-plane-manifest.json",
            "sha256": hashlib.sha256(control_plane_manifest).hexdigest(),
        },
        "images": {
            name: {"target": target, "image_id": None}
            for name, target in gas_city_ops.LOCK_IMAGE_TARGETS.items()
        },
        "image_receipt": {
            "path": "runtime/evidence/images/build-receipt.json",
            "sha256": None,
        },
        "promotion": {
            stage: {
                "path": f"runtime/evidence/promotion/{stage}-manifest.json",
                "sha256": None,
            }
            for stage in ("canary", "production")
        },
        "providers": {
            "claude": {
                "cli_version": "2.1.210",
                "binary_sha256": "9" * 64,
                "requested_model": "claude-fable-5",
                "observed_model": None,
                "receipt_sha256": None,
                "receipt_path": "runtime/evidence/providers/claude-model-receipt.json",
            },
            "codex": {
                "cli_version": "0.144.4",
                "package": "@openai/codex@0.144.4-linux-x64",
                "package_sri": "sha512-" + "A" * 86 + "==",
                "archive_sha256": "a" * 64,
                "binary_sha256": "b" * 64,
                "helper_sha256": {
                    "codex-code-mode-host": "c" * 64,
                    "rg": "d" * 64,
                    "zsh": "e" * 64,
                },
                "requested_model": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
                "observed_model": None,
                "receipt_sha256": None,
                "receipt_path": "runtime/evidence/providers/codex-model-receipt.json",
            },
        },
        "exclusions": ["graphiti", "cognee", "ollama"],
    }
    lock_path = _private_file(city / "runtime-lock.json", _json_bytes(lock))
    return {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock_path.as_posix(),
        "runtime_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "tools": {
            name: {
                "path": (city / "bin" / name).as_posix(),
                "version": lock["tools"][name]["version"],
                "binary_sha256": lock["tools"][name]["binary_sha256"],
            }
            for name in ("bd", "dolt")
        },
    }


def _locked_toolchain_from_city(city: Path) -> dict[str, Any]:
    lock_path = city / "runtime-lock.json"
    lock = json.loads(lock_path.read_text())
    return {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock_path.as_posix(),
        "runtime_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "tools": {
            name: {
                "path": (city / "bin" / name).as_posix(),
                "version": lock["tools"][name]["version"],
                "binary_sha256": lock["tools"][name]["binary_sha256"],
            }
            for name in ("bd", "dolt")
        },
    }


def _recovery_server(
    *,
    name: str,
    identity: str,
    port: int,
    image_id: str,
    backup_source: Path,
    backup_read_write: bool,
    relay_image_id: str | None = None,
) -> dict[str, Any]:
    normalized_image = image_id.removeprefix("sha256:")
    endpoint = {"host": "loopback", "port": port}
    if relay_image_id is None:
        publisher = {
            "mode": "direct",
            "container_name": name,
            "container_id": identity * 64,
            "image_id": normalized_image,
            "published_endpoint": endpoint,
            "target_container_id": identity * 64,
            "target_service": None,
            "shared_networks": [],
            "read_only_rootfs": True,
            "cap_drop": ["ALL"],
            "no_new_privileges": True,
            "command": None,
        }
    else:
        target_service = name.removeprefix("gas-city-")
        rig = target_service.removesuffix("-dolt")
        publisher = {
            "mode": "relay",
            "container_name": f"{name}-loopback",
            "container_id": "d" * 64,
            "image_id": relay_image_id.removeprefix("sha256:"),
            "published_endpoint": endpoint,
            "target_container_id": identity * 64,
            "target_service": target_service,
            "shared_networks": [f"gas-city-{rig}-control"],
            "read_only_rootfs": True,
            "cap_drop": ["ALL"],
            "no_new_privileges": True,
            "command": [
                "/usr/bin/socat",
                "TCP4-LISTEN:3306,reuseaddr,fork,nodelay",
                f"TCP4:{target_service}:3306,nodelay",
            ],
        }
    return {
        "container_name": name,
        "container_id": identity * 64,
        "image_id": normalized_image,
        "running": True,
        "published_endpoint": endpoint,
        "endpoint_publisher": publisher,
        "data_mount": {
            "type": "volume",
            "source": f"/var/lib/docker/volumes/{name}/_data",
            "name": f"{name}-data",
            "destination": gas_city_ops.DOLT_DATA_MOUNT_DESTINATION,
        },
        "backup_mount": {
            "type": "bind",
            "source": backup_source.as_posix(),
            "name": None,
            "destination": backup_source.as_posix(),
            "read_write": backup_read_write,
        },
        "docker_binary_sha256": "e" * 64,
    }


def _source_bytes() -> bytes:
    value = {
        "master": {
            "tasks": [
                {
                    "id": "1",
                    "title": "Freeze authority",
                    "description": "Migrate the exact task graph",
                    "details": "Keep Taskmaster rollback evidence",
                    "testStrategy": "Reconcile every exported field",
                    "priority": "high",
                    "dependencies": [],
                    "status": "in-progress",
                    "subtasks": [],
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "lastModified": "2026-07-15T09:30:00Z",
                "taskCount": 1,
                "completedCount": 0,
                "tags": ["master"],
            },
        }
    }
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def _canonical_export(content: bytes) -> bytes:
    records = [json.loads(line) for line in content.decode().splitlines() if line]
    normalized: dict[str, Mapping[str, Any]] = {}
    for record in records:
        copy = dict(record)
        if "dependencies" in copy:
            copy["dependencies"] = sorted(
                copy["dependencies"],
                key=lambda item: json.dumps(
                    item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ),
            )
        normalized[copy["id"]] = copy
    return b"".join(
        (
            json.dumps(
                normalized[identity],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        for identity in sorted(normalized)
    )


@dataclasses.dataclass(frozen=True)
class Evidence:
    city: Path
    target: Path
    snapshot: Path
    migration: Path
    recovery: Path
    migration_head: str
    migration_export_sha256: str


def _build_evidence(tmp_path: Path) -> Evidence:
    city = _private_dir(tmp_path / "gas-city")
    locked_toolchain = _provision_runtime_lock(city)
    runtime = _private_dir(city / "runtime")
    evidence_root = _private_dir(runtime / "evidence")
    target = _private_dir(tmp_path / "aegis-copy")
    _private_dir(target / ".beads")

    source = _source_bytes()
    source_sha = hashlib.sha256(source).hexdigest()
    snapshot = _private_dir(evidence_root / "snapshot" / "run-1")
    tasks_path = _private_file(snapshot / "tasks.json", source)
    health = b"Taskmaster health: PASS\n"
    _private_file(snapshot / "taskmaster-health.txt", health)
    snapshot_manifest = {
        "schema_version": 1,
        "status": "frozen",
        "captured_at": "2026-07-15T09:40:00Z",
        "source": {
            "repo_root": target.as_posix(),
            "relative_path": ".taskmaster/tasks/tasks.json",
            "sha256": source_sha,
            "size_bytes": len(source),
            "mtime_ns": tasks_path.stat().st_mtime_ns,
        },
        "git": {"head": "a" * 40, "dirty_paths": []},
        "taskmaster_health_sha256": hashlib.sha256(health).hexdigest(),
    }
    _private_file(snapshot / "snapshot-manifest.json", _json_bytes(snapshot_manifest))

    conversion = taskmaster_beads.build_artifacts(
        source, prefix="ags", expected_source_sha256=source_sha
    )
    export = conversion.artifacts["issues.jsonl"]
    verification = taskmaster_beads.verify_export(
        export,
        source_bytes=source,
        artifacts=conversion.artifacts,
        expected_source_sha256=source_sha,
    )
    canonical_export = _canonical_export(export)
    canonical_sha = hashlib.sha256(canonical_export).hexdigest()
    preflight_head = "1" * 32
    migration_head = "7vse6duhku1cl388k3bl998q53iq6qeg"
    issue_count = conversion.manifest["counts"]["issues"]
    import_dry = {
        "schema_version": 1,
        "created": issue_count,
        "skipped": 0,
        "dry_run": True,
        "ids_count": 0,
        "stale_skipped_ids_count": 0,
        "tie_kept_local_ids_count": 0,
        "updated_issues_count": 0,
    }
    import_live = {
        "schema_version": 1,
        "created": issue_count,
        "skipped": 0,
        "dry_run": False,
        "ids_count": issue_count,
        "stale_skipped_ids_count": 0,
        "tie_kept_local_ids_count": 0,
        "updated_issues_count": 0,
    }
    empty_attestation = {
        "issue_count": 0,
        "working_set_changes": 1,
        "expected_config_changes": 1,
        "unexpected_working_changes": 0,
        "branch_count": 1,
        "main_branch_count": 1,
        "commit_count": 3,
    }
    report = {
        "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
        "status": "pass",
        "source": {"sha256": source_sha, "tag": "master"},
        "target": {
            "directory": target.as_posix(),
            "database": "aegis_beads",
            "beads_version": taskmaster_beads.TARGET_BEADS_VERSION,
        },
        "counts": {
            "preexisting_records": 0,
            "manifest_issues": issue_count,
            "blocker_relationships": conversion.manifest["counts"]["blocker_relationships"],
            "hierarchy_relationships": conversion.manifest["counts"]["hierarchy_relationships"],
        },
        "artifact_digests": conversion.manifest["digests"],
        "empty_target_attestation": empty_attestation,
        "dry_run": import_dry,
        "first_import": import_live,
        "first_verification": verification,
        "second_import": import_live,
        "final_verification": verification,
        "idempotency": {
            "status": "pass",
            "canonical_export_sha256": canonical_sha,
            "first_raw_export_sha256": hashlib.sha256(export).hexdigest(),
            "final_raw_export_sha256": hashlib.sha256(export).hexdigest(),
            "preflight_dolt_main_head": preflight_head,
            "post_dry_run_dolt_main_head": preflight_head,
            "first_dolt_main_head": migration_head,
            "final_dolt_main_head": migration_head,
            "dry_run_head_unchanged": True,
            "first_import_advanced_main": True,
            "export_unchanged": True,
            "raw_export_unchanged": True,
            "dolt_main_head_unchanged": True,
        },
        "credential_transport": "runner-environment-only",
        "locked_toolchain": locked_toolchain,
    }
    artifacts: dict[str, bytes] = {
        **{
            f"conversion/{name}": conversion.artifacts[name]
            for name in taskmaster_beads.ARTIFACT_NAMES
        },
        "checkpoints/empty-target.json": _json_bytes(
            {
                "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                "status": "pass",
                "phase": "empty-target",
                **empty_attestation,
            }
        ),
        "checkpoints/first-import.json": _json_bytes(
            {
                "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                "status": "mutation-observed",
                "phase": "first-import",
                "source_sha256": source_sha,
                "preflight_dolt_main_head": preflight_head,
                "first_dolt_main_head": migration_head,
                "import": import_live,
            }
        ),
        "checkpoints/second-import.json": _json_bytes(
            {
                "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                "status": "mutation-observed",
                "phase": "second-import",
                "source_sha256": source_sha,
                "first_dolt_main_head": migration_head,
                "final_dolt_main_head": migration_head,
                "import": import_live,
            }
        ),
        "exports/first.jsonl": export,
        "exports/final.jsonl": export,
        "migration-report.json": _json_bytes(report),
    }
    migration_root = _private_dir(evidence_root / "migration" / "run-1")
    artifact_digests: dict[str, str] = {}
    for name, content in artifacts.items():
        _private_file(migration_root / name, content)
        artifact_digests[name] = hashlib.sha256(content).hexdigest()
    migration_manifest = {
        "schema_version": gas_city_authority.MIGRATION_EVIDENCE_SCHEMA,
        "status": "pass",
        "source_sha256": source_sha,
        "artifacts": artifact_digests,
    }
    migration_path = _private_file(
        migration_root / "evidence-manifest.json", _json_bytes(migration_manifest)
    )
    recovery = _recovery(
        evidence_root / "recovery" / "initial.json",
        verified_at="2026-07-15T09:50:00Z",
        head=migration_head,
        export_sha256=canonical_sha,
    )
    return Evidence(
        city=city,
        target=target,
        snapshot=snapshot,
        migration=migration_path,
        recovery=recovery,
        migration_head=migration_head,
        migration_export_sha256=canonical_sha,
    )


def _recovery(
    path: Path,
    *,
    verified_at: str,
    captured_at: str | None = None,
    head: str = "c" * 32,
    export_sha256: str = "d" * 64,
    source_port: int = gas_city_ops.AEGIS_BEADS_INIT_PORT,
    restore_port: int = 33072,
) -> Path:
    runtime = next(parent for parent in path.parents if parent.name == "runtime")
    city = runtime.parent
    runtime_lock = json.loads((city / "runtime-lock.json").read_text())
    backup = _private_dir(path.parent / f"{path.stem}-native-backup")
    _private_file(backup / "native" / "backup.json", b'{"backup":true}\n')
    backup_manifest = gas_city_ops._native_backup_manifest_bytes(
        gas_city_ops._file_tree_manifest(backup, label="test native backup")
    )
    backup_manifest_path = backup.parent / (
        backup.name + gas_city_ops.NATIVE_BACKUP_MANIFEST_SUFFIX
    )
    _private_file(backup_manifest_path, backup_manifest)
    return _private_file(
        path,
        _json_bytes(
            {
                "schema_version": gas_city_ops.NATIVE_RESTORE_SCHEMA_VERSION,
                "kind": "dolt-native-restore-drill",
                "status": "pass",
                "backup_path": backup.as_posix(),
                "backup_server_path": backup.as_posix(),
                "backup_manifest_path": backup_manifest_path.as_posix(),
                "backup_manifest_sha256": hashlib.sha256(backup_manifest).hexdigest(),
                "source_endpoint": {
                    "host": "127.0.0.1",
                    "port": source_port,
                    "user": gas_city_ops.AEGIS_RECOVERY_USER,
                    "database": "aegis_beads",
                },
                "restore_endpoint": {
                    "host": "127.0.0.1",
                    "port": restore_port,
                    "user": "aegis_restore",
                    "database": "aegis_restore",
                },
                "source_server": _recovery_server(
                    name="gas-city-aegis-dolt",
                    identity="1",
                    port=source_port,
                    image_id=runtime_lock["images"]["dolt_server"]["image_id"] or "f" * 64,
                    backup_source=backup.parent,
                    backup_read_write=True,
                    relay_image_id=runtime_lock["images"]["egress_proxy"]["image_id"] or "a" * 64,
                ),
                "restore_server": _recovery_server(
                    name="restore-dolt",
                    identity="2",
                    port=restore_port,
                    image_id=runtime_lock["images"]["dolt_server"]["image_id"] or "f" * 64,
                    backup_source=backup.parent,
                    backup_read_write=False,
                ),
                "restore_preflight": {
                    "empty_issue_count": 0,
                    "empty_export_sha256": hashlib.sha256(b"").hexdigest(),
                    "dolt_head": "a" * 32,
                },
                "dolt_head": head,
                "canonical_export_sha256": export_sha256,
                "backup_status": {"status": "current", "snapshots": 1},
                "locked_toolchain": _locked_toolchain_from_city(city),
                "secrets_included": False,
                "captured_at": captured_at or verified_at,
                "verified_at": verified_at,
            }
        ),
    )


def _stopped(path: Path, *, observed_at: str) -> Path:
    return _private_file(
        path,
        _json_bytes(
            {
                "schema_version": 1,
                "kind": "gas-city-workers-stopped",
                "status": "pass",
                "rig": "aegis",
                "observed_at": observed_at,
                "supervisor_running": False,
                "active_provider_containers": [],
                "active_sessions": [],
                "suspension_state": {
                    "path": ".gc/runtime/suspension-state.json",
                    "sha256": "9" * 64,
                    "city_suspended": True,
                    "aegis_suspended": True,
                    "updated_at": observed_at,
                },
            }
        ),
    )


class Hook:
    def __init__(self, fail_phase: str | None = None) -> None:
        self.fail_phase = fail_phase
        self.calls: list[str] = []

    def __call__(self, phase: str, path: Path, value: Mapping[str, Any]) -> bool:
        assert path.is_absolute()
        assert value["active_sessions"] == []
        self.calls.append(phase)
        return phase != self.fail_phase


def _initialize(
    evidence: Evidence, hook: Hook | None = None
) -> task_authority.TaskAuthorityReceipt:
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-1.json",
        observed_at="2026-07-15T09:59:00Z",
    )
    return gas_city_authority.initialize_production_authority(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        snapshot_dir=evidence.snapshot,
        migration_evidence_path=evidence.migration,
        recovery_evidence_path=evidence.recovery,
        expected_target_directory=evidence.target,
        stopped_workers_path=stopped,
        stopped_workers_hook=hook or Hook(),
        activated_at="2026-07-15T10:00:00Z",
    )


def _activate(evidence: Evidence, hook: Hook | None = None) -> task_authority.TaskAuthorityReceipt:
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-2.json",
        observed_at="2026-07-15T10:09:00Z",
    )
    return gas_city_authority.activate_beads_authority(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        stopped_workers_path=stopped,
        stopped_workers_hook=hook or Hook(),
        activated_at="2026-07-15T10:10:00Z",
    )


def test_initialize_accepts_gas_city_rfc3339_nanoseconds(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-1.json",
        observed_at="2026-07-15T09:59:00.123456789Z",
    )

    receipt = gas_city_authority.initialize_production_authority(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        snapshot_dir=evidence.snapshot,
        migration_evidence_path=evidence.migration,
        recovery_evidence_path=evidence.recovery,
        expected_target_directory=evidence.target,
        stopped_workers_path=stopped,
        stopped_workers_hook=Hook(),
        activated_at="2026-07-15T10:00:00Z",
    )

    assert receipt.generation == 1


def test_full_three_generation_lifecycle_is_owner_only_and_reverified(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    hook = Hook()
    first = _initialize(evidence, hook)
    second = _activate(evidence, hook)
    rollback_recovery = _recovery(
        evidence.city / "runtime" / "evidence" / "recovery" / "rollback.json",
        verified_at="2026-07-15T10:15:00Z",
        head=evidence.migration_head,
        export_sha256=evidence.migration_export_sha256,
    )
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-3.json",
        observed_at="2026-07-15T10:19:00Z",
    )
    third = gas_city_authority.rollback_to_taskmaster_authority(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        stopped_workers_path=stopped,
        rollback_recovery_path=rollback_recovery,
        stopped_workers_hook=hook,
        activated_at="2026-07-15T10:20:00Z",
    )

    report = gas_city_authority.verify_authority_chain(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
    )
    assert (first.generation, first.mode) == (1, task_authority.TaskAuthorityMode.TASKMASTER)
    assert (second.generation, second.mode) == (2, task_authority.TaskAuthorityMode.BEADS)
    assert (third.generation, third.mode) == (3, task_authority.TaskAuthorityMode.TASKMASTER)
    assert report.generation == 3
    assert report.recoverable_attempt is None
    assert [record["transition"] for record in report.generation_records] == [
        "initialize-taskmaster",
        "activate-beads",
        "rollback-taskmaster",
    ]
    assert (
        hook.calls
        == [
            "before-attempt",
            "before-transition",
            "after-transition",
        ]
        * 3
    )
    layout = report.layout
    assert layout.receipt_path == evidence.city / "runtime" / "authority" / "aegis.json"
    for directory in (
        layout.authority_root,
        layout.history_root,
        layout.attempts_root,
    ):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for path in (
        layout.receipt_path,
        *layout.history_root.glob("generation-*.json"),
        *layout.attempts_root.glob("*.json"),
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.stat().st_uid == os.geteuid()


def test_post_commit_hook_failure_recovers_history_without_replaying_transition(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    _initialize(evidence)
    hook = Hook(fail_phase="after-transition")

    with pytest.raises(gas_city_authority.GasCityAuthorityCommittedError) as caught:
        _activate(evidence, hook)

    assert caught.value.receipt.generation == 2
    before = gas_city_authority.verify_authority_chain(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
    )
    assert before.generation == 2
    assert len(before.generation_records) == 1
    assert before.recoverable_attempt is not None
    recovered = gas_city_authority.recover_authority_history(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
    )
    assert recovered.generation == 2
    assert len(recovered.generation_records) == 2
    assert recovered.recoverable_attempt is None
    assert hook.calls.count("after-transition") == 1
    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="no unambiguous"):
        gas_city_authority.recover_authority_history(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
        )


def test_append_only_write_failure_never_leaves_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = _private_dir(tmp_path / "authority")
    destination = parent / "generation-00000001.json"
    real_fsync = gas_city_authority.os.fsync
    calls = 0

    def fail_first_fsync(descriptor: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("simulated data fsync failure")
        real_fsync(descriptor)

    monkeypatch.setattr(gas_city_authority.os, "fsync", fail_first_fsync)
    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="unpublished"):
        gas_city_authority._write_append_only_json(destination, {"generation": 1})

    assert not destination.exists()
    assert list(parent.iterdir()) == []

    monkeypatch.setattr(gas_city_authority.os, "fsync", real_fsync)
    digest = gas_city_authority._write_append_only_json(destination, {"generation": 1})
    expected = _json_bytes({"generation": 1})
    assert destination.read_bytes() == expected
    assert digest == hashlib.sha256(expected).hexdigest()


def test_append_only_publish_failure_never_leaves_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = _private_dir(tmp_path / "authority")
    destination = parent / "generation-00000001.json"

    def fail_link(*args: Any, **kwargs: Any) -> None:
        raise OSError("simulated atomic publish failure")

    monkeypatch.setattr(gas_city_authority.os, "link", fail_link)
    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="cannot publish"):
        gas_city_authority._write_append_only_json(destination, {"generation": 1})

    assert not destination.exists()
    assert list(parent.iterdir()) == []


def test_append_only_existing_destination_is_never_rewritten(tmp_path: Path) -> None:
    parent = _private_dir(tmp_path / "authority")
    destination = _private_file(parent / "generation-00000001.json", _json_bytes({"generation": 1}))
    before = destination.read_bytes()

    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="already exists"):
        gas_city_authority._write_append_only_json(destination, {"generation": 2})

    assert destination.read_bytes() == before
    assert list(parent.iterdir()) == [destination]


@pytest.mark.parametrize(
    "verified_at",
    [
        "2026-07-15T10:10:00Z",  # not strictly post-generation-2
        "2026-07-15T10:04:59Z",  # stale by more than 15 minutes
        "2026-07-15T10:20:01Z",  # future-dated
    ],
)
def test_rollback_rejects_nonfresh_recovery_evidence(tmp_path: Path, verified_at: str) -> None:
    evidence = _build_evidence(tmp_path)
    _initialize(evidence)
    _activate(evidence)
    rollback = _recovery(
        evidence.city / "runtime" / "evidence" / "recovery" / "rollback.json",
        verified_at=verified_at,
    )
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-3.json",
        observed_at="2026-07-15T10:19:00Z",
    )
    with pytest.raises(gas_city_authority.GasCityAuthorityError):
        gas_city_authority.rollback_to_taskmaster_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            stopped_workers_path=stopped,
            rollback_recovery_path=rollback,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:20:00Z",
        )
    report = gas_city_authority.verify_authority_chain(
        evidence.city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
    )
    assert report.generation == 2


def test_rollback_freshness_is_measured_from_backup_capture_not_verification(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    _initialize(evidence)
    _activate(evidence)
    rollback = _recovery(
        evidence.city / "runtime" / "evidence" / "recovery" / "rollback.json",
        captured_at="2026-07-15T10:11:00Z",
        verified_at="2026-07-15T10:29:00Z",
        head=evidence.migration_head,
        export_sha256=evidence.migration_export_sha256,
    )
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-3.json",
        observed_at="2026-07-15T10:29:00Z",
    )
    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="older than 15"):
        gas_city_authority.rollback_to_taskmaster_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            stopped_workers_path=stopped,
            rollback_recovery_path=rollback,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:30:00Z",
        )


@pytest.mark.parametrize("drift", ["head", "export"])
def test_rollback_rejects_post_migration_beads_drift(tmp_path: Path, drift: str) -> None:
    evidence = _build_evidence(tmp_path)
    _initialize(evidence)
    _activate(evidence)
    rollback = _recovery(
        evidence.city / "runtime" / "evidence" / "recovery" / "rollback.json",
        verified_at="2026-07-15T10:15:00Z",
        head="e" * 32 if drift == "head" else evidence.migration_head,
        export_sha256=("e" * 64 if drift == "export" else evidence.migration_export_sha256),
    )
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-3.json",
        observed_at="2026-07-15T10:19:00Z",
    )

    message = (
        "Dolt head does not match migration evidence"
        if drift == "head"
        else "export does not match migration evidence"
    )
    with pytest.raises(gas_city_authority.GasCityAuthorityError, match=message):
        gas_city_authority.rollback_to_taskmaster_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            stopped_workers_path=stopped,
            rollback_recovery_path=rollback,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:20:00Z",
        )

    assert (
        gas_city_authority.verify_authority_chain(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
        ).generation
        == 2
    )


def test_full_chain_fails_closed_when_bound_migration_artifact_changes(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    _initialize(evidence)
    artifact = evidence.migration.parent / "exports" / "final.jsonl"
    artifact.write_bytes(artifact.read_bytes() + b"{}\n")
    artifact.chmod(0o600)

    with pytest.raises(gas_city_authority.GasCityAuthorityError, match="digest mismatch"):
        gas_city_authority.verify_authority_chain(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
        )


def test_initialization_rejects_rehashed_migration_with_substituted_tool(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    report_path = evidence.migration.parent / "migration-report.json"
    report = json.loads(report_path.read_text())
    report["locked_toolchain"]["tools"]["bd"]["path"] = (
        tmp_path / "same-version-substitute" / "bd"
    ).as_posix()
    report_path.write_bytes(_json_bytes(report))
    report_path.chmod(0o600)
    manifest = json.loads(evidence.migration.read_text())
    manifest["artifacts"]["migration-report.json"] = hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()
    evidence.migration.write_bytes(_json_bytes(manifest))
    evidence.migration.chmod(0o600)

    with pytest.raises(
        gas_city_authority.GasCityAuthorityError,
        match="toolchain is not lock-bound",
    ):
        _initialize(evidence)


def test_recovery_requires_distinct_servers_and_real_utc_timestamp(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    value = json.loads(evidence.recovery.read_text())
    value["restore_endpoint"]["port"] = value["source_endpoint"]["port"]
    value["verified_at"] = "not-a-time"
    evidence.recovery.write_bytes(_json_bytes(value))
    evidence.recovery.chmod(0o600)
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-1.json",
        observed_at="2026-07-15T09:59:00Z",
    )
    with pytest.raises(gas_city_authority.GasCityAuthorityError):
        gas_city_authority.initialize_production_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            snapshot_dir=evidence.snapshot,
            migration_evidence_path=evidence.migration,
            recovery_evidence_path=evidence.recovery,
            expected_target_directory=evidence.target,
            stopped_workers_path=stopped,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:00:00Z",
        )


def test_recovery_must_originate_from_exact_aegis_authority_server(
    tmp_path: Path,
) -> None:
    evidence = _build_evidence(tmp_path)
    value = json.loads(evidence.recovery.read_text())
    value["source_endpoint"]["user"] = "gas_city_hq"
    value["source_server"]["container_name"] = "gas-city-hq-dolt"
    publisher = value["source_server"]["endpoint_publisher"]
    publisher["container_name"] = "gas-city-hq-dolt-loopback"
    publisher["target_service"] = "hq-dolt"
    publisher["shared_networks"] = ["gas-city-hq-control"]
    publisher["command"][-1] = "TCP4:hq-dolt:3306,nodelay"
    evidence.recovery.write_bytes(_json_bytes(value))
    evidence.recovery.chmod(0o600)
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-1.json",
        observed_at="2026-07-15T09:59:00Z",
    )
    with pytest.raises(
        gas_city_authority.GasCityAuthorityError,
        match="Aegis authority endpoint",
    ):
        gas_city_authority.initialize_production_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            snapshot_dir=evidence.snapshot,
            migration_evidence_path=evidence.migration,
            recovery_evidence_path=evidence.recovery,
            expected_target_directory=evidence.target,
            stopped_workers_path=stopped,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:00:00Z",
        )


def test_recovery_verification_cannot_precede_capture(tmp_path: Path) -> None:
    evidence = _build_evidence(tmp_path)
    value = json.loads(evidence.recovery.read_text())
    value["captured_at"] = "2026-07-15T09:59:30Z"
    value["verified_at"] = "2026-07-15T09:59:29Z"
    evidence.recovery.write_bytes(_json_bytes(value))
    evidence.recovery.chmod(0o600)
    stopped = _stopped(
        evidence.city / "runtime" / "evidence" / "workers" / "generation-1.json",
        observed_at="2026-07-15T09:59:00Z",
    )
    with pytest.raises(
        gas_city_authority.GasCityAuthorityError,
        match="distinct-server restore",
    ):
        gas_city_authority.initialize_production_authority(
            evidence.city,
            rig="aegis",
            beads_prefix="ags",
            database="aegis_beads",
            snapshot_dir=evidence.snapshot,
            migration_evidence_path=evidence.migration,
            recovery_evidence_path=evidence.recovery,
            expected_target_directory=evidence.target,
            stopped_workers_path=stopped,
            stopped_workers_hook=Hook(),
            activated_at="2026-07-15T10:00:00Z",
        )
