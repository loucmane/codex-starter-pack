from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from aegis_foundation import (
    gas_city_authority,
    gas_city_ops,
    task_authority,
    taskmaster_beads,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY = REPO_ROOT / "deploy" / "gas-city"
TEST_CONTROL_PLANE_MANIFEST = b'{"kind":"test-control-plane-manifest","schema_version":1}\n'


def _deployment_digest(relative_path: str) -> str:
    return hashlib.sha256((DEPLOY / relative_path).read_bytes()).hexdigest()


def _aegis_startup_lock() -> dict[str, object]:
    return {
        **gas_city_ops.AEGIS_POLECAT_STARTUP_FIXED_PATHS,
        "sha256": _deployment_digest("docker/aegis-polecat-startup.py"),
        "formula_sha256": _deployment_digest("formulas/aegis/mol-polecat-work.toml"),
        "upstream_formula_sha256": hashlib.sha256(b"pinned upstream formula fixture").hexdigest(),
        "runtime_artifact_sha256": _deployment_digest("artifacts/aegis-runtime.whl"),
        "runtime_shim_sha256": _deployment_digest("docker/aegis-runtime-shim.py"),
        "local_launcher_sha256": hashlib.sha256(
            gas_city_ops.AEGIS_POLECAT_LOCAL_LAUNCHER_CONTENT
        ).hexdigest(),
    }


def _write(path: Path, content: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(content)
    path.chmod(mode)
    try:
        value = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    manifest = value.get("control_plane_manifest") if type(value) is dict else None
    if type(manifest) is dict and manifest.get("path") == "control-plane-manifest.json":
        manifest_path = path.parent / "control-plane-manifest.json"
        if not manifest_path.exists():
            manifest_path.write_bytes(TEST_CONTROL_PLANE_MANIFEST)
            manifest_path.chmod(0o600)


def _lock(tool_bytes: dict[str, bytes]) -> dict[str, object]:
    return {
        "schema_version": 1,
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
            "gascity_core_bd": {"commit": "f" * 40},
            "gastown": {"commit": "3" * 40},
        },
        "task_authority_runtime": {
            "source_path": "docker/task-authority.py",
            "image_path": "/opt/gas-city/task-authority.py",
            "sha256": _deployment_digest("docker/task-authority.py"),
        },
        "aegis_polecat_startup": _aegis_startup_lock(),
        "git_worktree_broker": {
            "source_path": gas_city_ops.GIT_WORKTREE_BROKER_SOURCE_PATH,
            "deployed_path": gas_city_ops.GIT_WORKTREE_BROKER_DEPLOYED_PATH,
            "sha256": _deployment_digest("bin/git-worktree-broker"),
        },
        "model_evidence_broker": {
            "source_path": gas_city_ops.MODEL_EVIDENCE_BROKER_SOURCE_PATH,
            "deployed_path": gas_city_ops.MODEL_EVIDENCE_BROKER_DEPLOYED_PATH,
            "sha256": _deployment_digest("bin/model-evidence-broker"),
        },
        "github_delivery": {
            "broker_source_path": gas_city_ops.GITHUB_DELIVERY_BROKER_SOURCE_PATH,
            "broker_deployed_path": gas_city_ops.GITHUB_DELIVERY_BROKER_DEPLOYED_PATH,
            "broker_sha256": _deployment_digest("bin/github-app-token-broker"),
            "repository": gas_city_ops.GITHUB_DELIVERY_REPOSITORY,
            "default_branch": "main",
            "permissions": gas_city_ops.GITHUB_DELIVERY_PERMISSIONS,
            "required_default_branch_rules": gas_city_ops.GITHUB_DELIVERY_REQUIRED_RULES,
            "maximum_lifetime_seconds": 3900,
        },
        "codex_preflight_catalog": {
            "source_path": gas_city_ops.CODEX_PREFLIGHT_CATALOG_SOURCE_PATH,
            "image_path": gas_city_ops.CODEX_PREFLIGHT_CATALOG_IMAGE_PATH,
            "sha256": _deployment_digest("config/codex-preflight-models.json"),
            "upstream_source_tag": gas_city_ops.CODEX_PREFLIGHT_UPSTREAM_TAG,
            "upstream_source_commit": gas_city_ops.CODEX_PREFLIGHT_UPSTREAM_COMMIT,
            "advertised_tools": ["update_plan", "view_image"],
            "tool_invocation_policy": "zero",
        },
        "control_plane_manifest": {
            "path": "control-plane-manifest.json",
            "sha256": hashlib.sha256(TEST_CONTROL_PLANE_MANIFEST).hexdigest(),
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
            "canary": {
                "path": "runtime/evidence/promotion/canary-manifest.json",
                "sha256": None,
            },
            "production": {
                "path": "runtime/evidence/promotion/production-manifest.json",
                "sha256": None,
            },
        },
        "providers": {
            "claude": {
                "cli_version": "2.1.210",
                "binary_sha256": "a" * 64,
                "requested_model": "claude-fable-5",
                "observed_model": None,
                "receipt_sha256": None,
                "receipt_path": "runtime/evidence/providers/claude-model-receipt.json",
            },
            "codex": {
                "cli_version": "0.144.4",
                "package": "@openai/codex@0.144.4-linux-x64",
                "package_sri": "sha512-" + "A" * 86 + "==",
                "archive_sha256": "b" * 64,
                "binary_sha256": "c" * 64,
                "helper_sha256": {
                    "codex-code-mode-host": "d" * 64,
                    "rg": "e" * 64,
                    "zsh": "f" * 64,
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


def _image_build_receipt(image_ids: dict[str, str]) -> dict[str, object]:
    lock = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    return {
        "schema_version": 1,
        "kind": "immutable-image-build",
        "status": "pass",
        "built_at": "2026-07-15T18:00:00Z",
        "source_lock_sha256": "1" * 64,
        "lock_schema_version": 1,
        "source_artifacts": gas_city_ops._locked_build_source_artifacts(lock),
        "build_context": {
            "manifest_sha256": "2" * 64,
            "file_count": len(gas_city_ops.BUILD_CONTEXT_FILES),
            "dockerfile_sha256": "3" * 64,
            "dockerignore_sha256": "4" * 64,
        },
        "docker": {
            "binary": "/usr/bin/docker",
            "binary_sha256": "5" * 64,
            "client_version": "25.0.3",
            "tagged": False,
            "pull": False,
            "no_cache": True,
        },
        "targets": dict(gas_city_ops.LOCK_IMAGE_TARGETS),
        "images": image_ids,
    }


def test_runtime_lock_and_installed_toolchain_are_exact(tmp_path: Path) -> None:
    city = tmp_path / "city"
    tool_bytes = {name: f"{name}-binary".encode() for name in ("gc", "bd", "dolt")}
    for name, content in tool_bytes.items():
        _write(city / "bin" / name, content, 0o555)
    lock_path = tmp_path / "runtime-lock.json"
    _write(lock_path, (json.dumps(_lock(tool_bytes)) + "\n").encode())

    versions = {"gc": "gc 1.3.5", "bd": "bd version 1.1.0", "dolt": "dolt version 2.2.0"}
    version_arguments = {
        "gc": ("version",),
        "bd": ("--version",),
        "dolt": ("version",),
    }

    def runner(argv, cwd, environment):
        name = Path(argv[0]).name
        assert argv[1:] == version_arguments[name]
        return subprocess.CompletedProcess(argv, 0, versions[name], "")

    result = gas_city_ops.verify_installed_toolchain(city, lock_path, runner=runner)
    assert result["status"] == "pass"
    assert set(result["tools"]) == {"gc", "bd", "dolt"}

    _write(city / "bin" / "bd", b"tampered", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="digest mismatch"):
        gas_city_ops.verify_installed_toolchain(city, lock_path, runner=runner)


def test_operation_toolchain_attestation_rejects_same_version_substitutes(
    tmp_path: Path,
) -> None:
    city = tmp_path / "city"
    tool_bytes = {name: f"{name}-binary".encode() for name in ("gc", "bd", "dolt")}
    for name, content in tool_bytes.items():
        _write(city / "bin" / name, content, 0o555)
    lock_path = city / "runtime-lock.json"
    _write(lock_path, (json.dumps(_lock(tool_bytes)) + "\n").encode())

    versions = {
        "gc": "gc 1.3.5",
        "bd": "bd version 1.1.0 (same-version)",
        "dolt": "dolt version 2.2.0",
    }

    def runner(argv, cwd, environment):
        return subprocess.CompletedProcess(argv, 0, versions[Path(argv[0]).name], "")

    attestation = gas_city_ops.locked_operation_toolchain_attestation(
        lock_path,
        {"bd": city / "bin" / "bd", "dolt": city / "bin" / "dolt"},
        runner=runner,
    )
    assert attestation == {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock_path.as_posix(),
        "runtime_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "tools": {
            "bd": {
                "path": (city / "bin" / "bd").as_posix(),
                "version": "1.1.0",
                "binary_sha256": hashlib.sha256(tool_bytes["bd"]).hexdigest(),
            },
            "dolt": {
                "path": (city / "bin" / "dolt").as_posix(),
                "version": "2.2.0",
                "binary_sha256": hashlib.sha256(tool_bytes["dolt"]).hexdigest(),
            },
        },
    }

    substitute = tmp_path / "substitute" / "bd"
    _write(substitute, b"different-binary-with-the-same-version", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="exact lock-bound"):
        gas_city_ops.locked_operation_toolchain_attestation(
            lock_path,
            {"bd": substitute, "dolt": city / "bin" / "dolt"},
            runner=runner,
        )


def test_runtime_lock_rehashes_one_exact_private_control_plane_manifest(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "runtime-lock.json"
    value = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    _write(lock_path, (json.dumps(value, sort_keys=True) + "\n").encode())
    manifest = tmp_path / "control-plane-manifest.json"
    assert (
        gas_city_ops.load_runtime_lock(lock_path)["control_plane_manifest"]
        == value["control_plane_manifest"]
    )

    _write(manifest, TEST_CONTROL_PLANE_MANIFEST + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="content digest mismatch"):
        gas_city_ops.load_runtime_lock(lock_path)

    _write(manifest, TEST_CONTROL_PLANE_MANIFEST, 0o620)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="group/world writable"):
        gas_city_ops.load_runtime_lock(lock_path)

    manifest.unlink()
    symlink_target = tmp_path / "manifest-target.json"
    _write(symlink_target, TEST_CONTROL_PLANE_MANIFEST)
    manifest.symlink_to(symlink_target)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="must not be a symlink"):
        gas_city_ops.load_runtime_lock(lock_path)

    manifest.unlink()
    with pytest.raises(gas_city_ops.GasCityOpsError, match="must be a regular file"):
        gas_city_ops.load_runtime_lock(lock_path)

    value["control_plane_manifest"]["sha256"] = value["control_plane_manifest"]["sha256"].upper()
    _write(lock_path, (json.dumps(value, sort_keys=True) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="manifest binding is invalid"):
        gas_city_ops.load_runtime_lock(lock_path)

    value["control_plane_manifest"]["sha256"] = hashlib.sha256(
        TEST_CONTROL_PLANE_MANIFEST
    ).hexdigest()
    value["control_plane_manifest"]["path"] = "runtime/control-plane-manifest.json"
    _write(lock_path, (json.dumps(value, sort_keys=True) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="manifest binding is invalid"):
        gas_city_ops.load_runtime_lock(lock_path)


class StoppedWorkerRunner:
    def __init__(self, city: Path) -> None:
        self.city = city
        self.active_container_environment: list[str] | None = None
        self.calls: list[tuple[str, ...]] = []
        self.environments: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        self.calls.append(command)
        self.environments.append((command, dict(environment)))
        if command[-3:] == ("supervisor", "status", "--json"):
            runtime = Path(environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
            home = Path(environment["HOME"])
            output = {
                "schema_version": "1",
                "ok": True,
                "checked_paths": [
                    str(runtime / "gc" / "supervisor.sock"),
                    str(home / ".gc" / "supervisor.sock"),
                ],
                "pid": 0,
                "running": False,
                "socket_path": "",
            }
        elif command[-4:] == ("rig", "status", "aegis", "--json"):
            output = {
                "schema_version": "1",
                "ok": True,
                "city_path": self.city.as_posix(),
                "city_name": "gas-city",
                "rig": {
                    "name": "aegis",
                    "path": (self.city / "rigs" / "aegis").as_posix(),
                    "prefix": "ags",
                    "suspended": False,
                    "beads": (self.city / "rigs" / "aegis" / ".beads").as_posix(),
                },
                "agents": [],
            }
        elif "session" in command and "list" in command:
            output = {
                "schema_version": "1",
                "ok": True,
                "filters": {"state": "active"},
                "sessions": [],
                "summary": {"total": 0, "active": 0, "suspended": 0, "closed": 0},
            }
        elif "ps" in command:
            if self.active_container_environment is None:
                return subprocess.CompletedProcess(command, 0, "", "")
            return subprocess.CompletedProcess(command, 0, "a" * 12 + "\n", "")
        elif "inspect" in command:
            output = {
                "Name": "/gc-claude-aegis-1",
                "Config": {
                    "Env": self.active_container_environment,
                    "Labels": {"com.gascity.boundary": "isolated-worker"},
                },
                "State": {"Running": True},
            }
        else:  # pragma: no cover - catches probe command drift.
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")


class ObsidianBuildRunner:
    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        assert ("vault", "build") == (
            command[command.index("vault")],
            command[command.index("vault") + 1],
        )
        output = Path(command[command.index("--output") + 1])
        output.mkdir(mode=0o700)
        note = b"# Deterministic Aegis projection\n"
        _write(output / "Home.md", note)
        manifest = {
            "schema_version": "2",
            "generator": "aegis-foundation:obsidian-vault",
            "managed_root": True,
            "task_authority": "beads/dolt",
            "task_export_command": "bd --readonly -C <repository> export",
            "task_bd_binary": command[command.index("--bd-executable") + 1],
            "task_bd_binary_sha256": command[command.index("--expected-bd-sha256") + 1],
            "task_bd_version": "bd version 1.1.0 (8e4e59d39)",
            "task_raw_export_sha256": "1" * 64,
            "task_dolt_main_head": "c" * 32,
            "repository_identity": "test:aegis",
            "repository_name": "aegis",
            "source_branch": "main",
            "source_head": "2" * 40,
            "source_digest": "3" * 64,
            "latest_evidence_ts": "2026-07-15T11:00:00Z",
            "counts": {
                "files": 1,
                "high_signal_events": 0,
                "identity_relationships": 0,
                "legacy_documents": 0,
                "task_relationships": 0,
                "tasks": 1,
            },
            "files": {"Home.md": hashlib.sha256(note).hexdigest()},
        }
        _write(
            output / ".aegis-vault.json",
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
        )
        result = {
            "status": "built",
            "changed": True,
            "output": output.as_posix(),
            "source_digest": manifest["source_digest"],
            "file_count": 1,
            "counts": manifest["counts"],
            "authority": "derived-read-only",
            "ledger": "available",
            "next_action": "check",
        }
        return subprocess.CompletedProcess(command, 0, json.dumps(result), "")


class ControlledCanaryRunner:
    RUN_ID = "d" * 32
    BASE = "4" * 40
    HEAD = "5" * 40
    MERGE = "6" * 40

    def __init__(self, primary: Path, worktree: Path, *, run_id: str | None = None) -> None:
        self.primary = primary.resolve()
        self.worktree = worktree.resolve()
        self.common = (self.primary / ".git").resolve()
        self.run_id = run_id or self.RUN_ID
        self.bead_exports = 0
        self.base_reads = 0
        self.pr_head = self.HEAD
        self.remote_merge = self.MERGE
        self.final_assignee = "aegis/gastown.refinery"
        self.final_status = "closed"
        self.worktree_branch = "polecat/ags-canary"
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        self.calls.append(command)
        executable = Path(command[0]).name
        if executable == "gh":
            assert environment.get("GH_TOKEN") == "t" * 40
        else:
            assert "GH_TOKEN" not in environment
        if executable == "bd":
            self.bead_exports += 1
            final = self.bead_exports > 1
            record = {
                "id": "ags-canary",
                "title": "Prove controlled delivery",
                "status": self.final_status if final else "in_progress",
                "assignee": (self.final_assignee if final else "aegis/gastown.polecat_canary"),
                "metadata": {
                    "branch": "polecat/ags-canary",
                    "work_dir": self.worktree.as_posix(),
                    **(
                        {
                            "target": "main",
                            "pr_url": "https://github.com/loucmane/codex/pull/256",
                        }
                        if final
                        else {}
                    ),
                },
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(record) + "\n", "")
        if executable == "gh":
            if command[1:] == ("--version",):
                return subprocess.CompletedProcess(command, 0, "gh version 2.76.2\n", "")
            if command[1:4] == ("auth", "status", "--hostname"):
                return subprocess.CompletedProcess(command, 0, "github.com authenticated\n", "")
            if command[1:3] == ("repo", "view"):
                value = {
                    "nameWithOwner": "loucmane/codex",
                    "url": "https://github.com/loucmane/codex",
                    "viewerPermission": "WRITE",
                    "defaultBranchRef": {"name": "main"},
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
            if command[1] == "api":
                self.base_reads += 1
                oid = self.BASE if self.base_reads == 1 else self.remote_merge
                value = {
                    "ref": "refs/heads/main",
                    "object": {"sha": oid, "type": "commit"},
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
            if command[1:3] == ("pr", "view"):
                value = {
                    "number": 256,
                    "url": "https://github.com/loucmane/codex/pull/256",
                    "state": "MERGED",
                    "isDraft": False,
                    "headRefName": self.worktree_branch,
                    "headRefOid": self.pr_head,
                    "baseRefName": "main",
                    "mergeCommit": {"oid": self.MERGE},
                    "mergedAt": "2026-07-15T11:15:00Z",
                    "mergedBy": {"login": "release-operator"},
                }
                return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
            if command[1:3] == ("pr", "checks"):
                value = [
                    {
                        "name": "test",
                        "state": "SUCCESS",
                        "bucket": "pass",
                        "link": "https://github.com/loucmane/codex/actions/runs/1",
                        "workflow": "CI",
                    }
                ]
                return subprocess.CompletedProcess(command, 0, json.dumps(value), "")
            if command[1:3] == ("repo", "clone"):
                clone = Path(command[4])
                clone.mkdir(mode=0o700)
                (clone / ".git").mkdir(mode=0o700)
                return subprocess.CompletedProcess(command, 0, "", "")
            raise AssertionError(command)
        if executable == "git":
            if command[1:] == ("--version",):
                return subprocess.CompletedProcess(command, 0, "git version 2.43.0\n", "")
            assert command[1] == "-C"
            repo = Path(command[2]).resolve()
            arguments = command[3:]
            is_primary = repo == self.primary
            is_worktree = repo == self.worktree
            is_clone = repo.name == "verification-clone"
            if arguments == ("rev-parse", "HEAD"):
                output = self.BASE if is_primary else self.HEAD if is_worktree else self.MERGE
            elif arguments == ("symbolic-ref", "--quiet", "--short", "HEAD"):
                output = "main" if is_primary else self.worktree_branch
            elif arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
                output = ""
            elif arguments == ("remote", "get-url", "origin"):
                output = "git@github.com:loucmane/codex.git"
            elif arguments == (
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ):
                output = self.common.as_posix()
            elif arguments[:2] == ("checkout", "--detach") and is_clone:
                output = ""
            elif arguments == ("fsck", "--full", "--strict") and is_clone:
                output = ""
            else:
                raise AssertionError(command)
            return subprocess.CompletedProcess(command, 0, output + ("\n" if output else ""), "")
        raise AssertionError(command)


class SoakProbeRunner:
    def __init__(self, city: Path, vault: Path) -> None:
        self.city = city
        self.vault = vault

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        if "vault" in command and "check" in command:
            output = {
                "status": "passed",
                "ok": True,
                "fresh": True,
                "output": self.vault.as_posix(),
                "source_digest": "3" * 64,
                "file_count": 1,
                "problems": [],
                "authority": "derived-read-only",
                "ledger": "available",
            }
        elif Path(command[0]).name == "bd" and "sql" in command:
            output = {"rows": [{"head": "c" * 32}]}
        elif Path(command[0]).name == "bd" and "export" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps({"id": "ags-1", "title": "live canary"}) + "\n",
                "",
            )
        elif Path(command[0]).name == "gc" and "supervisor" in command:
            runtime = Path(environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
            home = Path(environment["HOME"])
            socket_path = home / ".gc" / "supervisor.sock"
            output = {
                "schema_version": "1",
                "ok": True,
                "checked_paths": [
                    str(runtime / "gc" / "supervisor.sock"),
                    str(socket_path),
                ],
                "pid": 4242,
                "running": True,
                "socket_path": str(socket_path),
            }
        else:  # pragma: no cover - catches live-probe command drift.
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")


def _stopped_worker_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, StoppedWorkerRunner]:
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    gc = city / "bin" / "gc"
    docker = tmp_path / "bin" / "docker"
    _write(gc, b"gc", 0o555)
    _write(docker, b"docker", 0o555)
    lock = city / "runtime-lock.json"
    _write(
        lock,
        (
            json.dumps(
                _lock({"gc": b"gc", "bd": b"bd", "dolt": b"dolt"}),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode(),
    )
    proc = tmp_path / "proc"
    proc.mkdir()
    _write(
        city / ".gc" / "runtime" / "suspension-state.json",
        (
            json.dumps(
                {
                    "city": {"suspended": True},
                    "rigs": {"aegis": {"suspended": True}},
                    "updated_at": "2026-07-15T11:59:00Z",
                },
                sort_keys=True,
            )
            + "\n"
        ).encode(),
        0o644,
    )
    return city, lock, docker, proc, StoppedWorkerRunner(city)


def test_real_pinned_gc_machine_supervisor_socket_contract(tmp_path: Path) -> None:
    city = tmp_path / "city"
    home = tmp_path / "home"
    runtime = tmp_path / "run-user"
    for directory in (city, home, runtime):
        directory.mkdir(mode=0o700)
    environment = {
        **os.environ,
        "HOME": home.as_posix(),
        "XDG_RUNTIME_DIR": runtime.as_posix(),
    }
    result = subprocess.run(
        [
            (DEPLOY / "artifacts" / "gc").as_posix(),
            "--city",
            city.as_posix(),
            "supervisor",
            "status",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["checked_paths"] == [
        (runtime / "gc" / "supervisor.sock").as_posix(),
        (home / ".gc" / "supervisor.sock").as_posix(),
    ]
    gas_city_ops._validate_supervisor_stopped(value, environment=environment)


def test_stopped_worker_evidence_and_hook_reprobe_real_state(tmp_path: Path) -> None:
    city, lock, docker, proc, runner = _stopped_worker_fixture(tmp_path)
    output = city / "runtime" / "evidence" / "workers" / "generation-1.json"
    result = gas_city_ops.capture_aegis_stopped_workers_evidence(
        city,
        lock,
        output,
        docker_binary=docker,
        runner=runner,
        environment={
            **os.environ,
            "BEADS_DOLT_PASSWORD": "hq-secret",
            "DOLT_CLI_PASSWORD": "hq-secret",
            "GC_DOLT_PASSWORD": "hq-secret",
            "GAS_CITY_HQ_DOLT_PASSWORD_FILE": "/run/operator/hq-secret",
        },
        proc_root=proc,
        clock=lambda: dt.datetime(2026, 7, 15, 12, tzinfo=dt.timezone.utc),
    )
    assert result["rig"] == "aegis"
    assert result["observed_at"] == "2026-07-15T12:00:00Z"
    assert output.stat().st_mode & 0o777 == 0o600
    gc_environments = [
        environment
        for command, environment in runner.environments
        if Path(command[0]).name == "gc"
    ]
    docker_environments = [
        environment
        for command, environment in runner.environments
        if Path(command[0]).name == "docker"
    ]
    assert gc_environments
    assert all(
        environment["BEADS_DOLT_PASSWORD"] == "hq-secret"
        for environment in gc_environments
    )
    assert all(
        environment["PATH"] == f"{city / 'bin'}:/usr/bin:/bin"
        for environment in gc_environments
    )
    assert docker_environments
    assert all(
        not {
            "BEADS_DOLT_PASSWORD",
            "DOLT_CLI_PASSWORD",
            "GC_DOLT_PASSWORD",
            "GAS_CITY_HQ_DOLT_PASSWORD_FILE",
        }
        & set(environment)
        for environment in docker_environments
    )

    hook = gas_city_ops.AegisStoppedWorkersHook(
        city,
        lock,
        docker_binary=docker,
        runner=runner,
        proc_root=proc,
    )
    evidence = json.loads(output.read_text())
    for phase in ("before-attempt", "before-transition", "after-transition"):
        assert hook(phase, output, evidence) is True
    assert sum(command[-3:] == ("supervisor", "status", "--json") for command in runner.calls) == 4

    runner.active_container_environment = [
        "GC_RIG=aegis",
        "GC_BEADS_PREFIX=ags",
        "GC_DOLT_DATABASE=aegis_beads",
    ]
    with pytest.raises(gas_city_ops.GasCityOpsError, match="active Aegis provider"):
        hook("before-transition", output, evidence)


def test_stopped_worker_probe_rejects_partial_container_and_live_process_identity(
    tmp_path: Path,
) -> None:
    city, lock, docker, proc, runner = _stopped_worker_fixture(tmp_path)
    output = city / "runtime" / "evidence" / "workers" / "partial.json"
    runner.active_container_environment = ["GC_RIG=aegis", "GC_BEADS_PREFIX=wrong"]
    with pytest.raises(gas_city_ops.GasCityOpsError, match="ambiguous partial Aegis"):
        gas_city_ops.capture_aegis_stopped_workers_evidence(
            city,
            lock,
            output,
            docker_binary=docker,
            runner=runner,
            proc_root=proc,
        )

    runner.active_container_environment = None
    process = proc / "200"
    process.mkdir()
    (process / "cmdline").write_bytes(b"python\0provider-supervisor.py\0")
    (process / "environ").write_bytes(
        b"GC_RIG=aegis\0GC_BEADS_PREFIX=ags\0GC_DOLT_DATABASE=aegis_beads\0"
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="active Aegis provider process"):
        gas_city_ops.capture_aegis_stopped_workers_evidence(
            city,
            lock,
            output,
            docker_binary=docker,
            runner=runner,
            proc_root=proc,
        )


def test_stopped_worker_probe_tolerates_process_exit_between_proc_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, lock, docker, proc, runner = _stopped_worker_fixture(tmp_path)
    process = proc / "200"
    process.mkdir()
    cmdline = process / "cmdline"
    environment = process / "environ"
    cmdline.write_bytes(b"python\0provider-supervisor.py\0")
    environment.write_bytes(
        b"GC_RIG=aegis\0GC_BEADS_PREFIX=ags\0GC_DOLT_DATABASE=aegis_beads\0"
    )
    original_read_bytes = Path.read_bytes

    def read_bytes(path: Path) -> bytes:
        content = original_read_bytes(path)
        if path == cmdline:
            environment.unlink()
        return content

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    result = gas_city_ops.capture_aegis_stopped_workers_evidence(
        city,
        lock,
        city / "runtime" / "evidence" / "workers" / "exited.json",
        docker_binary=docker,
        runner=runner,
        proc_root=proc,
    )

    assert result["status"] == "pass"


def test_stopped_worker_probe_ignores_provider_names_embedded_in_arguments(
    tmp_path: Path,
) -> None:
    city, lock, docker, proc, runner = _stopped_worker_fixture(tmp_path)
    process = proc / "200"
    process.mkdir()
    (process / "cmdline").write_bytes(
        b"python\0-c\0run tests mentioning provider-supervisor.py and provider-container\0"
    )

    result = gas_city_ops.capture_aegis_stopped_workers_evidence(
        city,
        lock,
        city / "runtime" / "evidence" / "workers" / "embedded-argument.json",
        docker_binary=docker,
        runner=runner,
        proc_root=proc,
    )

    assert result["status"] == "pass"


def test_runtime_lock_rejects_secrets_exclusions_and_unproven_receipts(tmp_path: Path) -> None:
    content = {name: name.encode() for name in ("gc", "bd", "dolt")}
    value = _lock(content)
    value["database_password"] = "leak"
    path = tmp_path / "lock.json"
    _write(path, json.dumps(value).encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="secret material"):
        gas_city_ops.load_runtime_lock(path)

    value.pop("database_password")
    value["exclusions"] = ["cognee"]
    _write(path, json.dumps(value).encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="must exclude"):
        gas_city_ops.load_runtime_lock(path)

    value["exclusions"] = ["graphiti", "cognee", "ollama"]
    _write(path, json.dumps(value).encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="lacks an exact model receipt"):
        gas_city_ops.load_runtime_lock(path, require_observed_models=True)


def test_promoted_runtime_lock_rehashes_exact_model_receipt_files(tmp_path: Path) -> None:
    content = {name: name.encode() for name in ("gc", "bd", "dolt")}
    value = _lock(content)
    value["status"] = "provisioned_pending_canary"
    lock_path = tmp_path / "runtime-lock.json"
    image_ids = {
        name: f"sha256:{index:064x}"
        for index, name in enumerate(gas_city_ops.LOCK_IMAGE_TARGETS, start=1)
    }
    for name, image_id in image_ids.items():
        value["images"][name]["image_id"] = image_id
    image_receipt = _image_build_receipt(image_ids)
    image_receipt_bytes = (json.dumps(image_receipt, sort_keys=True) + "\n").encode()
    _write(tmp_path / value["image_receipt"]["path"], image_receipt_bytes)
    value["image_receipt"]["sha256"] = hashlib.sha256(image_receipt_bytes).hexdigest()
    for provider, model, effort in (
        ("claude", "claude-fable-5", None),
        ("codex", "gpt-5.6-sol", "xhigh"),
    ):
        receipt = {
            "schema_version": 1,
            "status": "verified",
            "provider": provider,
            "expected_model": model,
            "observed_model": model,
            "expected_effort": effort,
            "observed_effort": effort,
            "reasoning_effort": effort,
            "transcript_sha256": "9" * 64,
        }
        receipt_path = tmp_path / value["providers"][provider]["receipt_path"]
        receipt_bytes = (json.dumps(receipt, sort_keys=True) + "\n").encode()
        _write(receipt_path, receipt_bytes)
        value["providers"][provider]["observed_model"] = model
        value["providers"][provider]["receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    _write(lock_path, (json.dumps(value) + "\n").encode())

    assert (
        gas_city_ops.load_runtime_lock(lock_path, require_observed_models=True)["status"]
        == "provisioned_pending_canary"
    )

    claude_receipt = tmp_path / value["providers"]["claude"]["receipt_path"]
    _write(claude_receipt, claude_receipt.read_bytes() + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="content digest mismatch"):
        gas_city_ops.load_runtime_lock(lock_path, require_observed_models=True)


def test_snapshot_is_external_atomic_and_private(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    _write(tasks, b'{"master":{"tasks":[],"metadata":{}}}\n')
    output = tmp_path / "rollback" / "snapshot"
    manifest = gas_city_ops.capture_taskmaster_snapshot(
        repo,
        output,
        captured_at="2026-07-15T18:00:00Z",
        git_head="a" * 40,
        dirty_paths=["z.txt", "a.txt", "a.txt"],
        health_evidence="Taskmaster health: OK\n",
        expected_source_sha256=hashlib.sha256(tasks.read_bytes()).hexdigest(),
    )
    assert manifest["source"]["sha256"] == hashlib.sha256(tasks.read_bytes()).hexdigest()
    assert manifest["git"]["dirty_paths"] == ["a.txt", "z.txt"]
    for name in ("tasks.json", "taskmaster-health.txt", "snapshot-manifest.json"):
        assert (output / name).stat().st_mode & 0o777 == 0o600
    assert output.stat().st_mode & 0o777 == 0o700

    with pytest.raises(gas_city_ops.GasCityOpsError, match="disjoint"):
        gas_city_ops.capture_taskmaster_snapshot(
            repo,
            repo / "snapshot",
            captured_at="2026-07-15T18:00:00Z",
            git_head="a" * 40,
            dirty_paths=[],
            health_evidence="OK",
            expected_source_sha256=hashlib.sha256(tasks.read_bytes()).hexdigest(),
        )

    with pytest.raises(gas_city_ops.GasCityOpsError, match="already exists"):
        gas_city_ops.capture_taskmaster_snapshot(
            repo,
            output,
            captured_at="2026-07-15T18:00:00Z",
            git_head="a" * 40,
            dirty_paths=[],
            health_evidence="OK",
            expected_source_sha256=hashlib.sha256(tasks.read_bytes()).hexdigest(),
        )

    with pytest.raises(gas_city_ops.GasCityOpsError, match="changed while"):
        gas_city_ops.capture_taskmaster_snapshot(
            repo,
            tmp_path / "rollback" / "different-snapshot",
            captured_at="2026-07-15T18:00:00Z",
            git_head="a" * 40,
            dirty_paths=[],
            health_evidence="OK",
            expected_source_sha256="0" * 64,
        )


def test_snapshot_loader_rehashes_source_and_health_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    _write(tasks, b'{"master":{"tasks":[],"metadata":{}}}\n')
    snapshot = tmp_path / "rollback" / "snapshot"
    manifest = gas_city_ops.capture_taskmaster_snapshot(
        repo,
        snapshot,
        captured_at="2026-07-15T18:00:00Z",
        git_head="b" * 40,
        dirty_paths=[],
        health_evidence="Taskmaster health: OK\n",
        expected_source_sha256=hashlib.sha256(tasks.read_bytes()).hexdigest(),
    )

    source_bytes, loaded = gas_city_ops.load_taskmaster_snapshot(snapshot)

    assert source_bytes == tasks.read_bytes()
    assert loaded == manifest

    _write(snapshot / "taskmaster-health.txt", b"Taskmaster health: tampered\n")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="health evidence"):
        gas_city_ops.load_taskmaster_snapshot(snapshot)


def test_private_secret_and_evidence_files_are_guarded(tmp_path: Path) -> None:
    secret = tmp_path / "secret"
    _write(secret, ("a" * 32 + "\n").encode())
    assert (
        gas_city_ops.read_private_secret_file_from_environment(
            {"PASSWORD_FILE": str(secret)}, "PASSWORD_FILE"
        )
        == "a" * 32
    )

    secret.chmod(0o644)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="group/world permissions"):
        gas_city_ops.read_private_secret_file_from_environment(
            {"PASSWORD_FILE": str(secret)}, "PASSWORD_FILE"
        )

    report = tmp_path / "evidence" / "migration.json"
    digest = gas_city_ops.write_private_json_evidence(report, {"status": "pass"})
    assert digest == hashlib.sha256(report.read_bytes()).hexdigest()
    assert report.stat().st_mode & 0o777 == 0o600
    with pytest.raises(gas_city_ops.GasCityOpsError, match="append-only"):
        gas_city_ops.write_private_json_evidence(
            report,
            {"status": "replaced"},
            exclusive=True,
        )

    run = gas_city_ops.create_private_evidence_directory(tmp_path / "evidence-run")
    artifact_digest = gas_city_ops.write_private_evidence_bytes(
        run,
        "conversion/issues.jsonl",
        b'{"id":"ags-1"}\n',
    )
    artifact = run / "conversion" / "issues.jsonl"
    assert artifact_digest == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert artifact.stat().st_mode & 0o777 == 0o600
    with pytest.raises(gas_city_ops.GasCityOpsError, match="append-only"):
        gas_city_ops.write_private_evidence_bytes(
            run,
            "conversion/issues.jsonl",
            b"replacement",
        )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="safe and relative"):
        gas_city_ops.write_private_evidence_bytes(run, "../escape", b"bad")


def test_model_admin_derives_expectation_and_output_from_lock(tmp_path: Path) -> None:
    content = {name: name.encode() for name in ("gc", "bd", "dolt")}
    lock_path = tmp_path / "runtime-lock.json"
    _write(lock_path, (json.dumps(_lock(content)) + "\n").encode())
    transcript = tmp_path / "claude.jsonl"
    _write(
        transcript,
        b'{"type":"assistant","message":{"model":"claude-opus-4-8"}}\n',
    )
    command = [
        str(Path(__file__).parents[2] / "scripts" / "gas-city-admin"),
        "verify-model",
        "--provider",
        "claude",
        "--transcript",
        str(transcript),
        "--lock",
        str(lock_path),
    ]
    rejected = subprocess.run(command, text=True, capture_output=True, check=False)
    assert rejected.returncode == 1
    assert "model mismatch" in rejected.stderr

    _write(
        transcript,
        b'{"type":"assistant","message":{"model":"claude-fable-5"}}\n',
    )
    accepted = subprocess.run(command, text=True, capture_output=True, check=False)
    assert accepted.returncode == 0
    output = json.loads(accepted.stdout)
    receipt_path = tmp_path / _lock(content)["providers"]["claude"]["receipt_path"]
    assert output["receipt_path"] == str(receipt_path)
    assert output["receipt_sha256"] == hashlib.sha256(receipt_path.read_bytes()).hexdigest()


def test_claude_receipt_fails_closed_on_fallback_or_model_drift(tmp_path: Path) -> None:
    transcript = tmp_path / "claude.jsonl"
    _write(
        transcript,
        (json.dumps({"type": "assistant", "message": {"model": "claude-fable-5"}}) + "\n").encode(),
    )
    receipt = gas_city_ops.verify_model_transcript(
        "claude", transcript, expected_model="claude-fable-5"
    )
    assert receipt["observed_model"] == "claude-fable-5"
    assert receipt["observations"] == 1

    _write(transcript, b'{"type":"user","message":{"model":"claude-fable-5"}}\n')
    with pytest.raises(gas_city_ops.GasCityOpsError, match="no verifiable"):
        gas_city_ops.verify_model_transcript("claude", transcript, expected_model="claude-fable-5")

    _write(transcript, b'{"type":"assistant","message":{}}\n')
    with pytest.raises(gas_city_ops.GasCityOpsError, match="lacks a model"):
        gas_city_ops.verify_model_transcript("claude", transcript, expected_model="claude-fable-5")

    _write(transcript, b'{"type":"system","subtype":"model_refusal_fallback"}\n')
    with pytest.raises(gas_city_ops.GasCityOpsError, match="fallback event"):
        gas_city_ops.verify_model_transcript("claude", transcript, expected_model="claude-fable-5")

    _write(transcript, b'{"type":"assistant","message":{"model":"claude-opus-4-8"}}\n')
    with pytest.raises(gas_city_ops.GasCityOpsError, match="model mismatch"):
        gas_city_ops.verify_model_transcript("claude", transcript, expected_model="claude-fable-5")


def test_codex_receipt_requires_sol_and_xhigh_on_every_turn(tmp_path: Path) -> None:
    transcript = tmp_path / "codex.jsonl"
    records = [
        {
            "type": "turn_context",
            "payload": {
                "model": "gpt-5.6-sol",
                "collaboration_mode": {"settings": {"reasoning_effort": "xhigh"}},
            },
        },
        {"type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "xhigh"}},
    ]
    _write(transcript, "".join(json.dumps(item) + "\n" for item in records).encode())
    receipt = gas_city_ops.verify_model_transcript(
        "codex",
        transcript,
        expected_model="gpt-5.6-sol",
        expected_effort="xhigh",
    )
    assert receipt["observations"] == 2

    records[1]["payload"]["effort"] = "high"
    _write(transcript, "".join(json.dumps(item) + "\n" for item in records).encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="receipt mismatch"):
        gas_city_ops.verify_model_transcript(
            "codex",
            transcript,
            expected_model="gpt-5.6-sol",
            expected_effort="xhigh",
        )


class BackupRunner:
    def __init__(
        self,
        source: Path,
        restore: Path,
        *,
        mismatched: bool = False,
        nonempty_restore: bool = False,
        image_id: str = "3" * 64,
        backup_root: Path | None = None,
    ) -> None:
        self.source = source
        self.restore = restore
        self.mismatched = mismatched
        self.nonempty_restore = nonempty_restore
        self.image_id = image_id.removeprefix("sha256:")
        self.backup_root = backup_root or source.parent
        self.backup: Path | None = None
        self.restored = False
        self.calls: list[tuple[tuple[str, ...], Path, dict[str, str]]] = []

    def __call__(self, argv, cwd, environment):
        argv = tuple(argv)
        self.calls.append((argv, cwd, dict(environment)))
        if argv[1:4] == ("inspect", "--type", "container"):
            container = argv[-1]
            source = container == "source-dolt"
            inspected = [
                {
                    "Id": ("1" if source else "2") * 64,
                    "Image": self.image_id,
                    "Name": f"/{container}",
                    "State": {"Running": True},
                    "Mounts": [
                        {
                            "Type": "volume",
                            "Source": f"/var/lib/docker/volumes/{container}/_data",
                            "Name": f"{container}-data",
                            "Destination": gas_city_ops.DOLT_DATA_MOUNT_DESTINATION,
                        },
                        {
                            "Type": "bind",
                            "Source": self.backup_root.as_posix(),
                            "Destination": self.backup_root.as_posix(),
                            "RW": source,
                        },
                    ],
                    "NetworkSettings": {
                        "Ports": {
                            "3306/tcp": [
                                {
                                    "HostIp": "127.0.0.1",
                                    "HostPort": "3306" if source else "3307",
                                }
                            ]
                        },
                        "Networks": {f"{container}-network": {}},
                    },
                    "HostConfig": {
                        "ReadonlyRootfs": True,
                        "CapDrop": ["ALL"],
                        "SecurityOpt": ["no-new-privileges:true"],
                    },
                    "Config": {"Cmd": None},
                }
            ]
            return subprocess.CompletedProcess(argv, 0, json.dumps(inspected), "")
        if "backup" in argv and "init" in argv:
            self.backup = Path(argv[-1])
            assert self.backup.is_relative_to(self.backup_root)
            self.backup.mkdir(parents=True)
            return subprocess.CompletedProcess(argv, 0, '{"status":"initialized"}\n', "")
        if "backup" in argv and "sync" in argv:
            assert self.backup is not None
            _write(self.backup / "native" / "manifest.json", b'{"backup":true}\n')
            return subprocess.CompletedProcess(argv, 0, '{"status":"current"}\n', "")
        if "backup" in argv and "restore" in argv:
            self.restored = True
            return subprocess.CompletedProcess(argv, 0, '{"status":"restored"}\n', "")
        if "init" in argv and "backup" not in argv:
            (self.restore / ".beads").mkdir()
            return subprocess.CompletedProcess(argv, 0, '{"status":"initialized"}\n', "")
        if "status" in argv:
            return subprocess.CompletedProcess(argv, 0, '{"status":"current"}\n', "")
        if any("DOLT_HASHOF('main') AS head" in argument for argument in argv):
            head = "a" * 32 if cwd == self.restore and not self.restored else "b" * 32
            if self.mismatched and cwd == self.restore:
                head = "c" * 32
            return subprocess.CompletedProcess(argv, 0, json.dumps({"rows": [{"head": head}]}), "")
        if "export" in argv:
            if cwd == self.restore and not self.restored:
                output = '{"id":"stale-1","title":"not empty"}\n' if self.nonempty_restore else ""
                return subprocess.CompletedProcess(argv, 0, output, "")
            dependencies = [
                {"issue_id": "ags-1", "depends_on_id": "ags-2", "type": "blocks"},
                {"issue_id": "ags-1", "depends_on_id": "ags-3", "type": "parent-child"},
            ]
            if cwd == self.restore:
                dependencies.reverse()
            output = json.dumps(
                {"id": "ags-1", "title": "one", "dependencies": dependencies}
            ) + "\n"
            return subprocess.CompletedProcess(argv, 0, output, "")
        return subprocess.CompletedProcess(argv, 0, '{"ok":true}\n', "")


def test_dolt_identity_binds_hardened_loopback_relay_without_publishing_server(
    tmp_path: Path,
) -> None:
    docker = tmp_path / "docker"
    _write(docker, b"docker", 0o555)
    backup_root = tmp_path / "backups"
    backup_root.mkdir()
    server_id = "1" * 64
    server_image = "2" * 64
    relay_id = "3" * 64
    relay_image = "4" * 64
    relay_command = [
        "/usr/bin/socat",
        "TCP4-LISTEN:3306,reuseaddr,fork,nodelay",
        "TCP4:aegis-dolt:3306,nodelay",
    ]

    def runner(argv, cwd, environment):
        del cwd, environment
        name = argv[-1]
        common = {
            "State": {"Running": True},
            "HostConfig": {
                "ReadonlyRootfs": True,
                "CapDrop": ["ALL"],
                "SecurityOpt": ["no-new-privileges:true"],
            },
        }
        if name == "gas-city-aegis-dolt":
            value = {
                **common,
                "Id": server_id,
                "Image": server_image,
                "Name": "/gas-city-aegis-dolt",
                "Mounts": [
                    {
                        "Type": "volume",
                        "Source": "/var/lib/docker/volumes/aegis/_data",
                        "Name": "aegis",
                        "Destination": gas_city_ops.DOLT_DATA_MOUNT_DESTINATION,
                    },
                    {
                        "Type": "bind",
                        "Source": backup_root.as_posix(),
                        "Destination": backup_root.as_posix(),
                        "RW": True,
                    },
                ],
                "NetworkSettings": {
                    "Ports": {"3306/tcp": None},
                    "Networks": {
                        "gas-city-aegis-control": {},
                        "gas-city-hq-control": {},
                    },
                },
                "Config": {"Cmd": None},
            }
        elif name == "gas-city-aegis-dolt-loopback":
            value = {
                **common,
                "Id": relay_id,
                "Image": relay_image,
                "Name": "/gas-city-aegis-dolt-loopback",
                "Mounts": [],
                "NetworkSettings": {
                    "Ports": {"3306/tcp": [{"HostIp": "127.0.0.1", "HostPort": "33071"}]},
                    "Networks": {
                        "gas-city-aegis-control": {},
                        "gas-city-aegis-loopback-ingress": {},
                    },
                },
                "Config": {"Cmd": relay_command},
            }
        else:  # pragma: no cover - the verifier constrains both inspect names.
            raise AssertionError(name)
        return subprocess.CompletedProcess(argv, 0, json.dumps([value]), "")

    result = gas_city_ops._docker_dolt_server_identity(
        docker,
        "gas-city-aegis-dolt",
        gas_city_ops.DoltEndpoint("127.0.0.1", 33071, "aegis_beads", "aegis_beads"),
        runner=runner,
        environment={},
        cwd=tmp_path,
        expected_image_id=server_image,
        expected_relay_image_id=relay_image,
        allow_relay=True,
    )

    assert result["published_endpoint"] == {"host": "loopback", "port": 33071}
    assert result["endpoint_publisher"] == {
        "mode": "relay",
        "container_name": "gas-city-aegis-dolt-loopback",
        "container_id": relay_id,
        "image_id": relay_image,
        "published_endpoint": {"host": "loopback", "port": 33071},
        "target_container_id": server_id,
        "target_service": "aegis-dolt",
        "shared_networks": ["gas-city-aegis-control"],
        "read_only_rootfs": True,
        "cap_drop": ["ALL"],
        "no_new_privileges": True,
        "command": relay_command,
    }


def test_native_backup_restore_drill_uses_distinct_endpoint_and_env_secrets(tmp_path: Path) -> None:
    source = tmp_path / "source"
    restore = tmp_path / "restore"
    backup = tmp_path / "offsite" / "backup"
    (source / ".beads").mkdir(parents=True)
    restore.mkdir()
    lock_path, lock = _provisioned_runtime(tmp_path)
    bd = lock_path.parent / "bin" / "bd"
    docker = tmp_path / "bin" / "docker"
    _write(docker, b"docker", 0o555)
    runner = BackupRunner(
        source,
        restore,
        image_id=lock["images"]["dolt_server"]["image_id"],
    )
    result = gas_city_ops.native_backup_restore_drill(
        source,
        restore,
        backup,
        lock_path=lock_path,
        locked_toolchain=_recorded_toolchain(lock_path, lock),
        source_endpoint=gas_city_ops.DoltEndpoint("127.0.0.1", 3306, "hq_user", "hq_tasks"),
        restore_endpoint=gas_city_ops.DoltEndpoint("127.0.0.1", 3307, "restore_user", "hq_tasks"),
        bd_binary=bd,
        docker_binary=docker,
        source_container="source-dolt",
        restore_container="restore-dolt",
        source_password="source-secret",
        restore_password="restore-secret",
        runner=runner,
        base_environment={"PATH": "/usr/bin"},
        clock=lambda: dt.datetime(2026, 7, 15, 12, tzinfo=dt.timezone.utc),
    )
    assert result["status"] == "pass"
    assert result["secrets_included"] is False
    assert result["captured_at"] == result["verified_at"] == "2026-07-15T12:00:00Z"
    assert result["backup_server_path"] == backup.as_posix()
    flattened = "\n".join(" ".join(call[0]) for call in runner.calls)
    assert "source-secret" not in flattened
    assert "restore-secret" not in flattened
    source_calls = [
        call for call in runner.calls if call[1] == source and "BEADS_DOLT_PASSWORD" in call[2]
    ]
    restore_calls = [
        call for call in runner.calls if call[1] == restore and "BEADS_DOLT_PASSWORD" in call[2]
    ]
    assert all(call[2]["BEADS_DOLT_PASSWORD"] == "source-secret" for call in source_calls)
    assert all(call[2]["BEADS_DOLT_PASSWORD"] == "restore-secret" for call in restore_calls)
    assert all(call[2]["BD_BACKUP_ENABLED"] == "false" for call in source_calls)
    assert all(call[2]["BD_BACKUP_ENABLED"] == "false" for call in restore_calls)
    assert all(call[2]["BEADS_DOLT_SERVER_HOST"] == "127.0.0.1" for call in source_calls)
    assert all(call[2]["BEADS_DOLT_SERVER_PORT"] == "3306" for call in source_calls)
    assert all(call[2]["BEADS_DOLT_SERVER_USER"] == "hq_user" for call in source_calls)
    assert all(call[2]["BEADS_DOLT_SERVER_DATABASE"] == "hq_tasks" for call in source_calls)
    assert all(call[2]["BEADS_DOLT_SERVER_HOST"] == "127.0.0.1" for call in restore_calls)
    [restore_init] = [
        call
        for call in runner.calls
        if "init" in call[0] and "backup" not in call[0]
    ]
    assert restore_init[1] == restore
    assert "-C" not in restore_init[0]
    assert result["source_server"]["container_id"] != result["restore_server"]["container_id"]
    assert result["restore_preflight"]["empty_issue_count"] == 0
    assert gas_city_ops.validate_native_restore_evidence(lock_path, result) == result

    same_container = json.loads(json.dumps(result))
    same_container["restore_server"]["container_id"] = same_container["source_server"][
        "container_id"
    ]
    same_container["restore_server"]["endpoint_publisher"]["container_id"] = same_container[
        "source_server"
    ]["container_id"]
    same_container["restore_server"]["endpoint_publisher"]["target_container_id"] = same_container[
        "source_server"
    ]["container_id"]
    with pytest.raises(gas_city_ops.GasCityOpsError, match="isolated containers"):
        gas_city_ops.validate_native_restore_evidence(lock_path, same_container)

    alias_replay = json.loads(json.dumps(result))
    alias_replay["source_endpoint"]["host"] = "localhost"
    alias_replay["restore_endpoint"]["host"] = "127.0.0.1"
    alias_replay["restore_endpoint"]["port"] = 3306
    alias_replay["restore_server"]["published_endpoint"]["port"] = 3306
    alias_replay["restore_server"]["endpoint_publisher"]["published_endpoint"]["port"] = 3306
    with pytest.raises(gas_city_ops.GasCityOpsError, match="distinct-server restore"):
        gas_city_ops.validate_native_restore_evidence(lock_path, alias_replay)

    _write(backup / "native" / "manifest.json", b"tampered")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="backup bytes or metadata drifted"):
        gas_city_ops.validate_native_restore_evidence(lock_path, result)


def test_native_restore_canonicalization_matches_migration_identity_order() -> None:
    export = (
        '{"aaa":"first-lexically","id":"ags-2","title":"two"}\n'
        '{"aaa":"second-lexically","id":"ags-1","title":"one"}\n'
    ).encode()

    assert gas_city_ops._canonical_jsonl(export.decode(), label="native restore") == (
        taskmaster_beads._canonical_operational_export(export, step="migration")
    )


def test_native_backup_restore_drill_rejects_same_database_under_another_user(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    restore = tmp_path / "restore"
    (source / ".beads").mkdir(parents=True)
    restore.mkdir()
    lock_path, lock = _provisioned_runtime(tmp_path)
    bd = lock_path.parent / "bin" / "bd"
    docker = tmp_path / "docker"
    _write(docker, b"docker", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="distinct server"):
        gas_city_ops.native_backup_restore_drill(
            source,
            restore,
            tmp_path / "backup",
            lock_path=lock_path,
            locked_toolchain=_recorded_toolchain(lock_path, lock),
            source_endpoint=gas_city_ops.DoltEndpoint("dolt", 3306, "source_user", "tasks"),
            restore_endpoint=gas_city_ops.DoltEndpoint("dolt", 3306, "restore_user", "tasks"),
            bd_binary=bd,
            docker_binary=docker,
            source_container="source-dolt",
            restore_container="restore-dolt",
            source_password="source-secret",
            restore_password="restore-secret",
            runner=BackupRunner(
                source,
                restore,
                image_id=lock["images"]["dolt_server"]["image_id"],
            ),
            base_environment={},
        )

    with pytest.raises(gas_city_ops.GasCityOpsError, match="distinct server"):
        gas_city_ops.native_backup_restore_drill(
            source,
            restore,
            tmp_path / "another-backup",
            lock_path=lock_path,
            locked_toolchain=_recorded_toolchain(lock_path, lock),
            source_endpoint=gas_city_ops.DoltEndpoint("dolt", 3306, "source_user", "tasks"),
            restore_endpoint=gas_city_ops.DoltEndpoint(
                "dolt", 3306, "restore_user", "different_database"
            ),
            bd_binary=bd,
            docker_binary=docker,
            source_container="source-dolt",
            restore_container="restore-dolt",
            source_password="source-secret",
            restore_password="restore-secret",
            runner=BackupRunner(
                source,
                restore,
                image_id=lock["images"]["dolt_server"]["image_id"],
            ),
            base_environment={},
        )


def test_native_backup_restore_drill_rejects_head_drift(tmp_path: Path) -> None:
    source = tmp_path / "source"
    restore = tmp_path / "restore"
    (source / ".beads").mkdir(parents=True)
    restore.mkdir()
    lock_path, lock = _provisioned_runtime(tmp_path)
    bd = lock_path.parent / "bin" / "bd"
    docker = tmp_path / "docker"
    _write(docker, b"docker", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="Dolt head mismatch"):
        gas_city_ops.native_backup_restore_drill(
            source,
            restore,
            tmp_path / "backup",
            lock_path=lock_path,
            locked_toolchain=_recorded_toolchain(lock_path, lock),
            source_endpoint=gas_city_ops.DoltEndpoint("127.0.0.1", 3306, "user_one", "tasks"),
            restore_endpoint=gas_city_ops.DoltEndpoint("127.0.0.1", 3307, "user_two", "tasks"),
            bd_binary=bd,
            docker_binary=docker,
            source_container="source-dolt",
            restore_container="restore-dolt",
            source_password="source-secret",
            restore_password="restore-secret",
            runner=BackupRunner(
                source,
                restore,
                mismatched=True,
                image_id=lock["images"]["dolt_server"]["image_id"],
            ),
            base_environment={},
        )


def test_native_backup_restore_drill_rejects_nonempty_restore_database(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    restore = tmp_path / "restore"
    (source / ".beads").mkdir(parents=True)
    restore.mkdir()
    lock_path, lock = _provisioned_runtime(tmp_path)
    docker = tmp_path / "docker"
    _write(docker, b"docker", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="not empty before restore"):
        gas_city_ops.native_backup_restore_drill(
            source,
            restore,
            tmp_path / "backup",
            lock_path=lock_path,
            locked_toolchain=_recorded_toolchain(lock_path, lock),
            source_endpoint=gas_city_ops.DoltEndpoint("127.0.0.1", 3306, "user_one", "tasks"),
            restore_endpoint=gas_city_ops.DoltEndpoint(
                "127.0.0.1", 3307, "user_two", "tasks_restore"
            ),
            bd_binary=lock_path.parent / "bin" / "bd",
            docker_binary=docker,
            source_container="source-dolt",
            restore_container="restore-dolt",
            source_password="source-secret",
            restore_password="restore-secret",
            runner=BackupRunner(
                source,
                restore,
                nonempty_restore=True,
                image_id=lock["images"]["dolt_server"]["image_id"],
            ),
            base_environment={},
        )


class ImageRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.ids = {
            target: f"sha256:{index:064x}"
            for index, target in enumerate(gas_city_ops.LOCK_IMAGE_TARGETS.values(), start=1)
        }

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        self.calls.append(command)
        if len(command) > 1 and command[1] == "version":
            return subprocess.CompletedProcess(command, 0, "25.0.3\n", "")
        if len(command) > 1 and command[1] == "build":
            target = command[command.index("--target") + 1]
            return subprocess.CompletedProcess(command, 0, self.ids[target] + "\n", "")
        if command[1:3] == ("image", "inspect"):
            return subprocess.CompletedProcess(command, 0, command[-1] + "\n", "")
        raise AssertionError(command)


class ColdCaptureRunner:
    def __init__(self, *, dirty: bool = True, running: bool = False, branch: str = "main") -> None:
        self.dirty = dirty
        self.running = running
        self.branch = branch
        self.calls: list[tuple[tuple[str, ...], Path]] = []

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        self.calls.append((command, cwd))
        binary = Path(command[0]).name
        if binary == "docker":
            if command[1] == "version":
                return subprocess.CompletedProcess(command, 0, "25.0.3\n", "")
            if command[1] == "inspect":
                return subprocess.CompletedProcess(
                    command, 0, ("true" if self.running else "false") + "\n", ""
                )
        if binary == "dolt":
            if command[1] == "version":
                return subprocess.CompletedProcess(command, 0, "dolt version 2.2.0\n", "")
            if command[1] == "status":
                suffix = (
                    "Changes not staged for commit:\n\tmodified: config\n"
                    if self.dirty
                    else "nothing to commit, working tree clean\n"
                )
                return subprocess.CompletedProcess(
                    command, 0, f"On branch {self.branch}\n\n" + suffix, ""
                )
            if command[1:3] == ("branch", "--show-current"):
                return subprocess.CompletedProcess(command, 0, self.branch + "\n", "")
            if command[1] == "sql":
                return subprocess.CompletedProcess(
                    command,
                    0,
                    '{"rows":[{"head":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}]}\n',
                    "",
                )
            if command[1] == "diff":
                tables = (
                    [{"name": "config", "data_diff": []}]
                    if self.dirty and "--staged" not in command
                    else []
                )
                return subprocess.CompletedProcess(
                    command,
                    0,
                    json.dumps({"tables": tables}) + "\n",
                    "",
                )
        raise AssertionError(command)


def test_image_build_receipt_and_promotion_use_only_exact_immutable_ids(
    tmp_path: Path,
) -> None:
    context = Path(__file__).parents[2] / "deploy" / "gas-city"
    lock_path = tmp_path / "runtime-lock.json"
    _write(
        lock_path,
        (json.dumps(_lock({name: name.encode() for name in ("gc", "bd", "dolt")})) + "\n").encode(),
    )
    docker = tmp_path / "bin" / "docker"
    _write(docker, b"docker-binary", 0o555)
    runner = ImageRunner()

    built = gas_city_ops.build_locked_images(
        lock_path,
        context,
        docker_binary=docker,
        runner=runner,
        environment={},
        clock=lambda: dt.datetime(2026, 7, 15, 18, tzinfo=dt.timezone.utc),
    )

    assert built["status"] == "built_pending_promotion"
    assert set(built["images"].values()) == set(runner.ids.values())
    build_calls = [call for call in runner.calls if call[1] == "build"]
    assert len(build_calls) == 4
    assert all("--quiet" in call and "--no-cache" in call for call in build_calls)
    assert all("--tag" not in call and "-t" not in call for call in build_calls)
    receipt = json.loads(Path(built["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["source_artifacts"] == gas_city_ops._locked_build_source_artifacts(
        _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    )

    promoted = gas_city_ops.promote_locked_images(
        lock_path,
        docker_binary=docker,
        runner=runner,
        environment={},
    )
    assert promoted["status"] == "provisioned_pending_canary"
    loaded = gas_city_ops.load_runtime_lock(lock_path)
    assert {name: record["image_id"] for name, record in loaded["images"].items()} == {
        name: runner.ids[target] for name, target in gas_city_ops.LOCK_IMAGE_TARGETS.items()
    }


def test_cold_backup_is_private_exact_and_detects_payload_tampering(tmp_path: Path) -> None:
    source = tmp_path / "hq-dolt"
    _write(source / "hq" / ".dolt" / "noms" / "manifest", b"head-and-working-set")
    _write(source / "config.json", b'{"version":1}\n')
    (source / "hq" / "empty-directory").mkdir()
    source.chmod(0o700)
    dolt = tmp_path / "bin" / "dolt"
    docker = tmp_path / "bin" / "docker"
    _write(dolt, b"dolt", 0o555)
    _write(docker, b"docker", 0o555)
    lock = _lock({"gc": b"gc", "bd": b"bd", "dolt": b"dolt"})
    lock_path = tmp_path / "runtime-lock.json"
    _write(lock_path, (json.dumps(lock) + "\n").encode())
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    output = tmp_path / "backups" / "hq-cold"
    runner = ColdCaptureRunner()

    captured = gas_city_ops.capture_cold_dolt_backup(
        source,
        output,
        lock_path=lock_path,
        dolt_binary=dolt,
        docker_binary=docker,
        runner=runner,
        port_probe=lambda host, port, timeout: False,
        proc_root=proc_root,
        clock=lambda: dt.datetime(2026, 7, 15, 19, tzinfo=dt.timezone.utc),
    )

    verified = gas_city_ops.verify_cold_dolt_backup(Path(captured["manifest_path"]))
    assert verified["status"] == "pass"
    assert verified["file_count"] == 2
    assert verified["directory_count"] >= 3
    assert captured["hq_working_set_dirty"] is True
    assert (output / "data" / "hq" / "empty-directory").is_dir()
    assert output.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o077 == 0 for path in output.iterdir() if path.name != "data")
    assert (output / "data" / "hq").stat().st_mode & 0o777 == (source / "hq").stat().st_mode & 0o777
    dolt_calls = [cwd for command, cwd in runner.calls if Path(command[0]).name == "dolt"]
    assert dolt_calls
    assert all(cwd == output / "data" / "hq" for cwd in dolt_calls)
    payload = output / "data" / "config.json"
    _write(payload, b"tampered")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="digest mismatch"):
        gas_city_ops.verify_cold_dolt_backup(Path(captured["manifest_path"]))


def test_cold_backup_derives_strict_state_and_rejects_live_or_invalid_probes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "hq-dolt"
    _write(source / "hq" / "data.bin", b"data")
    source.chmod(0o700)
    dolt = tmp_path / "bin" / "dolt"
    docker = tmp_path / "bin" / "docker"
    _write(dolt, b"dolt", 0o555)
    _write(docker, b"docker", 0o555)
    lock_path = tmp_path / "runtime-lock.json"
    _write(
        lock_path,
        (json.dumps(_lock({"gc": b"gc", "bd": b"bd", "dolt": b"dolt"})) + "\n").encode(),
    )
    proc_root = tmp_path / "proc"
    proc_root.mkdir()
    kwargs = {
        "lock_path": lock_path,
        "dolt_binary": dolt,
        "docker_binary": docker,
        "port_probe": lambda host, port, timeout: False,
        "proc_root": proc_root,
        "clock": lambda: dt.datetime(2026, 7, 15, 19, tzinfo=dt.timezone.utc),
    }

    with pytest.raises(gas_city_ops.GasCityOpsError, match="still running"):
        gas_city_ops.capture_cold_dolt_backup(
            source,
            tmp_path / "live-container",
            runner=ColdCaptureRunner(running=True),
            **kwargs,
        )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="listener"):
        gas_city_ops.capture_cold_dolt_backup(
            source,
            tmp_path / "live-listener",
            runner=ColdCaptureRunner(),
            **{**kwargs, "port_probe": lambda host, port, timeout: True},
        )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="required main branch"):
        gas_city_ops.capture_cold_dolt_backup(
            source,
            tmp_path / "wrong-branch",
            runner=ColdCaptureRunner(branch="other"),
            **kwargs,
        )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="exact locked HQ Dolt identity"):
        gas_city_ops.capture_cold_dolt_backup(
            source,
            tmp_path / "wrong-identity",
            runner=ColdCaptureRunner(),
            endpoint_port=33071,
            **kwargs,
        )


def test_stopped_probe_detects_deleted_open_and_mapped_source_files(tmp_path: Path) -> None:
    source = (tmp_path / "hq-data").resolve()
    source.mkdir()
    proc = tmp_path / "proc"
    deleted_fd = proc / "41001"
    (deleted_fd / "fd").mkdir(parents=True)
    (deleted_fd / "cmdline").write_bytes(b"worker\0")
    (deleted_fd / "fd" / "7").symlink_to(f"{source}/chunk (deleted)")
    mapped = proc / "41002"
    (mapped / "fd").mkdir(parents=True)
    (mapped / "cmdline").write_bytes(b"worker\0")
    (mapped / "maps").write_text(
        f"7f00-7f10 r--p 00000000 00:00 0 {source}/mapped-file (deleted)\n"
    )
    assert gas_city_ops._source_process_holders(source, proc) == ["41001", "41002"]


def test_runtime_lock_requires_exact_archive_provenance_for_every_tool(tmp_path: Path) -> None:
    value = _lock({"gc": b"gc", "bd": b"bd", "dolt": b"dolt"})
    path = tmp_path / "runtime-lock.json"
    del value["tools"]["gc"]["archive_sha256"]
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="must contain exactly"):
        gas_city_ops.load_runtime_lock(path)

    value = _lock({"gc": b"gc", "bd": b"bd", "dolt": b"dolt"})
    value["tools"]["bd"]["unexpected"] = True
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="must contain exactly"):
        gas_city_ops.load_runtime_lock(path)


def test_runtime_lock_rejects_unexpected_root_fields(tmp_path: Path) -> None:
    value = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    value["network_override"] = {"allow": "all"}
    path = tmp_path / "runtime-lock.json"
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="fields must be exact"):
        gas_city_ops.load_runtime_lock(path)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record.update({"unexpected": True}),
        lambda record: record.update({"source_path": "bin/./git-worktree-broker"}),
        lambda record: record.update({"deployed_path": "bin/other-broker"}),
        lambda record: record.update({"sha256": "A" * 64}),
    ),
)
def test_runtime_lock_strictly_validates_git_worktree_broker_contract(
    tmp_path: Path, mutation
) -> None:
    value = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    mutation(value["git_worktree_broker"])
    path = tmp_path / "runtime-lock.json"
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="Git worktree broker"):
        gas_city_ops.load_runtime_lock(path)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record.update({"unexpected": True}),
        lambda record: record.update({"source_path": "bin/./model-evidence-broker"}),
        lambda record: record.update({"deployed_path": "bin/other-broker"}),
        lambda record: record.update({"sha256": "A" * 64}),
    ),
)
def test_runtime_lock_strictly_validates_model_evidence_broker_contract(
    tmp_path: Path, mutation
) -> None:
    value = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    mutation(value["model_evidence_broker"])
    path = tmp_path / "runtime-lock.json"
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match="model evidence broker"):
        gas_city_ops.load_runtime_lock(path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        (lambda record: record.update({"unexpected": True}), "fields are not exact"),
        (lambda record: record.pop("receipt_path"), "fields are not exact"),
        (
            lambda record: record.update({"source_path": "docker/./aegis-polecat-startup.py"}),
            "paths are invalid",
        ),
        (
            lambda record: record.update({"image_path": "/tmp/aegis-startup.py"}),
            "paths are invalid",
        ),
        (
            lambda record: record.update(
                {"runtime_artifact_source_path": "artifacts/../artifacts/aegis-runtime.whl"}
            ),
            "paths are invalid",
        ),
        (
            lambda record: record.update({"runtime_shim_sha256": "A" * 64}),
            "digest is invalid",
        ),
        (
            lambda record: record.update(
                {"local_launcher_sha256": hashlib.sha256(b"other launcher").hexdigest()}
            ),
            "local launcher does not match",
        ),
    ),
)
def test_runtime_lock_strictly_validates_aegis_polecat_startup_contract(
    tmp_path: Path,
    mutation,
    message: str,
) -> None:
    value = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    mutation(value["aegis_polecat_startup"])
    path = tmp_path / "runtime-lock.json"
    _write(path, (json.dumps(value) + "\n").encode())
    with pytest.raises(gas_city_ops.GasCityOpsError, match=message):
        gas_city_ops.load_runtime_lock(path)


def test_image_receipt_source_artifacts_are_exact_and_alias_free() -> None:
    lock = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    expected = gas_city_ops._locked_build_source_artifacts(lock)
    image_ids = {
        name: f"sha256:{index:064x}"
        for index, name in enumerate(gas_city_ops.LOCK_IMAGE_TARGETS, start=1)
    }
    receipt = _image_build_receipt(image_ids)
    gas_city_ops._validate_image_build_receipt_shape(
        receipt,
        expected_images=image_ids,
        expected_source_artifacts=expected,
    )

    for mutate in (
        lambda artifacts: artifacts.update({"docker/unexpected.py": "9" * 64}),
        lambda artifacts: artifacts.pop("docker/aegis-polecat-startup.py"),
        lambda artifacts: artifacts.update(
            {
                "docker/aegis-polecat-startup.py": "9" * 64,
            }
        ),
        lambda artifacts: artifacts.update(
            {"docker/./aegis-polecat-startup.py": artifacts.pop("docker/aegis-polecat-startup.py")}
        ),
    ):
        candidate = json.loads(json.dumps(receipt))
        mutate(candidate["source_artifacts"])
        with pytest.raises(gas_city_ops.GasCityOpsError, match="does not prove"):
            gas_city_ops._validate_image_build_receipt_shape(
                candidate,
                expected_images=image_ids,
                expected_source_artifacts=expected,
            )


def test_image_build_rejects_locked_source_artifact_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = _lock({name: name.encode() for name in ("gc", "bd", "dolt")})
    lock_path = tmp_path / "runtime-lock.json"
    _write(lock_path, (json.dumps(lock) + "\n").encode())
    context = tmp_path / "context"
    context.mkdir()
    for relative_path in gas_city_ops._locked_build_source_artifacts(lock):
        _write(
            context / relative_path,
            (DEPLOY / relative_path).read_bytes(),
            0o444,
        )
    _write(context / "docker/Dockerfile", b"FROM scratch\n", 0o444)
    _write(context / ".dockerignore", b"**\n", 0o444)
    docker = tmp_path / "docker"
    _write(docker, b"docker", 0o555)
    monkeypatch.setattr(
        gas_city_ops,
        "_build_context_fingerprint",
        lambda _context: {
            "manifest_sha256": "1" * 64,
            "file_count": len(gas_city_ops.BUILD_CONTEXT_FILES),
            "dockerfile_sha256": "2" * 64,
            "dockerignore_sha256": "3" * 64,
        },
    )
    tampered = context / "docker/aegis-polecat-startup.py"
    tampered.chmod(0o600)
    tampered.write_bytes(b"tampered")
    tampered.chmod(0o444)

    with pytest.raises(gas_city_ops.GasCityOpsError, match="does not match.*startup"):
        gas_city_ops.build_locked_images(
            lock_path,
            context,
            docker_binary=docker,
            runner=lambda argv, cwd, environment: (_ for _ in ()).throw(
                AssertionError("Docker must not run after source tampering")
            ),
            environment={},
        )


def _write_json_evidence(path: Path, value: dict[str, object]) -> Path:
    gas_city_ops.write_private_json_evidence(path, value, exclusive=True)
    return path


def _recorded_toolchain(
    lock_path: Path,
    value: dict[str, object],
) -> dict[str, object]:
    city = lock_path.parent
    return {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": lock_path.as_posix(),
        "runtime_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "tools": {
            name: {
                "path": (city / "bin" / name).as_posix(),
                "version": value["tools"][name]["version"],
                "binary_sha256": value["tools"][name]["binary_sha256"],
            }
            for name in ("bd", "dolt")
        },
    }


def _recorded_restore_server(
    name: str,
    *,
    identity: str,
    port: int,
    backup_source: Path,
    backup_read_write: bool,
    image_id: str = "f" * 64,
    relay_image_id: str | None = None,
) -> dict[str, object]:
    normalized_image = image_id.removeprefix("sha256:")
    endpoint = {"host": "loopback", "port": port}
    if relay_image_id is None:
        publisher: dict[str, object] = {
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


def _provisioned_runtime(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    tool_bytes = {name: name.encode() for name in ("gc", "bd", "dolt")}
    for name, content in tool_bytes.items():
        _write(city / "bin" / name, content, 0o555)
    value = _lock(tool_bytes)
    value["status"] = "provisioned_pending_canary"
    image_ids = {
        name: f"sha256:{index:064x}"
        for index, name in enumerate(gas_city_ops.LOCK_IMAGE_TARGETS, start=10)
    }
    for name, image_id in image_ids.items():
        value["images"][name]["image_id"] = image_id
    image_receipt = _image_build_receipt(image_ids)
    receipt_path = city / value["image_receipt"]["path"]
    receipt_digest = gas_city_ops.write_private_json_evidence(
        receipt_path,
        image_receipt,
        exclusive=True,
    )
    value["image_receipt"]["sha256"] = receipt_digest
    lock_path = city / "runtime-lock.json"
    _write(lock_path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    return lock_path, value


def _write_soak_session_receipt(
    lock_path: Path,
    *,
    provider: str,
    recorded_at: dt.datetime,
    sequence: int,
) -> Path:
    lock = json.loads(lock_path.read_text())
    agent = {"claude": "witness", "codex": "polecat"}[provider]
    session = f"soak-{provider}-{sequence}"
    receipt_path = (
        lock_path.parent
        / "runtime"
        / "state"
        / "git-broker"
        / "rig-aegis"
        / agent
        / session
        / "model-evidence"
        / "session-receipt.json"
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    for directory in (
        lock_path.parent / "runtime" / "state" / "git-broker" / "rig-aegis",
        lock_path.parent / "runtime" / "state" / "git-broker" / "rig-aegis" / agent,
        receipt_path.parents[1],
        receipt_path.parent,
    ):
        directory.chmod(0o700)
    model = lock["providers"][provider]["requested_model"]
    effort = lock["providers"][provider].get("reasoning_effort")
    seed = hashlib.sha256(f"{provider}:{sequence}".encode()).hexdigest()
    receipt = {
        "schema_version": 1,
        "kind": "host-model-evidence-receipt",
        "status": "verified",
        "phase": "session",
        "provider": provider,
        "expected_model": model,
        "expected_effort": effort,
        "observed_model": model,
        "observed_effort": effort,
        "provider_exit_code": 0,
        "event_sha256": seed,
        "transcript_sha256": hashlib.sha256((seed + "t").encode()).hexdigest(),
        "transcript_locator": f"/home/worker/.{provider}/sessions/soak.jsonl",
        "tool_free": False,
        "challenge_sha256": hashlib.sha256((seed + "c").encode()).hexdigest(),
        "container_name": f"gc-{provider}-soak-{sequence}",
        "container_image_id": lock["images"][f"{provider}_worker"]["image_id"],
        "container_boundary": "isolated-worker",
        "model_source_phase": "preflight",
        "model_attestation_scope": gas_city_ops.HOST_MODEL_ATTESTATION_SCOPE,
        "evidence_id": seed[:32],
        "run_generation": 1,
        "run_id_sha256": hashlib.sha256((seed + "r").encode()).hexdigest(),
        "session_id_sha256": hashlib.sha256(session.encode()).hexdigest(),
        "git_broker_id": f"00000000-0000-4000-8000-{sequence:012x}",
        "git_broker_receipt_sha256": hashlib.sha256((seed + "g").encode()).hexdigest(),
        "git_startup_receipt_sha256": hashlib.sha256((seed + "s").encode()).hexdigest(),
        "git_source_starting_oid": "a" * 40,
        "git_authorized_ref": f"refs/heads/polecat/ags-soak-{sequence}",
        "container_init_host_pid": 2000 + sequence,
        "supervisor_host_pid": 3000 + sequence,
        "supervisor_host_uid": os.getuid(),
        "supervisor_host_gid": os.getgid(),
        "supervisor_starttime_ticks": 4000 + sequence,
        "preflight_receipt_sha256": hashlib.sha256((seed + "p").encode()).hexdigest(),
        "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
    }
    _write(
        receipt_path,
        (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode(),
        0o400,
    )
    return receipt_path


def test_recorded_operation_toolchain_is_reverified_against_lock_and_bytes(
    tmp_path: Path,
) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    city = lock_path.parent
    recorded = _recorded_toolchain(lock_path, value)
    assert (
        gas_city_ops.validate_locked_operation_toolchain_evidence(lock_path, recorded) == recorded
    )

    substituted = json.loads(json.dumps(recorded))
    substituted["tools"]["bd"]["path"] = (tmp_path / "same-version" / "bd").as_posix()
    with pytest.raises(gas_city_ops.GasCityOpsError, match="city/bin/bd"):
        gas_city_ops.validate_locked_operation_toolchain_evidence(lock_path, substituted)

    _write(city / "bin" / "dolt", b"tampered", 0o555)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="installed dolt digest mismatch"):
        gas_city_ops.validate_locked_operation_toolchain_evidence(lock_path, recorded)


def _promotion_evidence(
    tmp_path: Path,
    lock_path: Path,
    value: dict[str, object],
    *,
    canary_mutator=None,
    capture_time: dt.datetime | None = None,
) -> tuple[dict[str, Path], Path]:
    city = lock_path.parent
    provider_session_artifacts: dict[str, tuple[Path, Path]] = {}
    for provider, model, effort in (
        ("claude", "claude-fable-5", None),
        ("codex", "gpt-5.6-sol", "xhigh"),
    ):
        agent = {"claude": "witness", "codex": "polecat"}[provider]
        session = f"{provider}-canary"
        overlay = {"claude": "projects", "codex": "sessions"}[provider]
        transcript_path = (
            city
            / "runtime"
            / "state"
            / "provider-sessions"
            / "rig-aegis"
            / agent
            / provider
            / session
            / overlay
            / "canary.jsonl"
        )
        transcript_event = (
            {"type": "assistant", "message": {"model": model}}
            if provider == "claude"
            else {
                "type": "turn_context",
                "payload": {"model": model, "effort": effort},
            }
        )
        transcript_content = (json.dumps(transcript_event) + "\n").encode()
        _write(transcript_path, transcript_content)
        transcript_path.parent.chmod(0o700)
        transcript_sha = hashlib.sha256(transcript_content).hexdigest()
        receipt = {
            "schema_version": 1,
            "status": "verified",
            "provider": provider,
            "expected_model": model,
            "observed_model": model,
            "expected_effort": effort,
            "observed_effort": effort,
            "reasoning_effort": effort,
            "transcript_sha256": transcript_sha,
        }
        provider_path = city / value["providers"][provider]["receipt_path"]
        gas_city_ops.write_private_json_evidence(provider_path, receipt, exclusive=True)
        supervisor_path = (
            city
            / "runtime"
            / "state"
            / "model-receipts"
            / "rig-aegis"
            / agent
            / provider
            / session
            / "model-receipt.json"
        )
        _write_json_evidence(
            supervisor_path,
            {
                "schema_version": 1,
                "status": "verified",
                "provider": provider,
                "expected_model": model,
                "expected_effort": effort,
                "observed_model": model,
                "observed_effort": effort,
                "transcript": f"/home/worker/.{provider}/{overlay}/canary.jsonl",
                "transcript_sha256": transcript_sha,
                "provider_exit_code": 0,
            },
        )
        provider_session_artifacts[provider] = (supervisor_path, transcript_path)

    source = tmp_path / "hq-data"
    _write(source / "hq" / "data.bin", b"hq-data")
    source.chmod(0o700)
    dolt = tmp_path / "cold-bin" / "dolt"
    docker = tmp_path / "cold-bin" / "docker"
    _write(dolt, b"dolt", 0o555)
    _write(docker, b"docker", 0o555)
    proc_root = tmp_path / "cold-proc"
    proc_root.mkdir()
    backup = gas_city_ops.capture_cold_dolt_backup(
        source,
        city / "runtime" / "evidence" / "backup" / "hq-cold",
        lock_path=lock_path,
        dolt_binary=dolt,
        docker_binary=docker,
        runner=ColdCaptureRunner(),
        port_probe=lambda host, port, timeout: False,
        proc_root=proc_root,
        clock=lambda: dt.datetime(2026, 7, 15, 10, tzinfo=dt.timezone.utc),
    )

    taskmaster_repo = tmp_path / "taskmaster-source"
    source_bytes = (
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": "1",
                            "title": "Migrate one task",
                            "description": "production fixture",
                            "details": "preserve the exact task",
                            "testStrategy": "exact reconciliation",
                            "priority": "high",
                            "dependencies": [],
                            "status": "pending",
                            "subtasks": [],
                        }
                    ],
                    "metadata": {
                        "version": "1.0.0",
                        "lastModified": "2026-07-15T08:00:00.000Z",
                        "taskCount": 1,
                        "completedCount": 0,
                        "tags": ["master"],
                    },
                }
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    _write(taskmaster_repo / ".taskmaster" / "tasks" / "tasks.json", source_bytes)
    snapshot_dir = city / "runtime" / "evidence" / "snapshots" / "aegis-cutover"
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    gas_city_ops.capture_taskmaster_snapshot(
        taskmaster_repo,
        snapshot_dir,
        captured_at="2026-07-15T08:00:00Z",
        git_head="1" * 40,
        dirty_paths=[],
        health_evidence="Taskmaster health: PASS\n",
        expected_source_sha256=source_sha,
    )

    migration_root = gas_city_ops.create_private_evidence_directory(
        city / "runtime" / "evidence" / "migration" / "run-1"
    )
    conversion = taskmaster_beads.build_artifacts(
        source_bytes,
        tag="master",
        prefix="ags",
        expected_source_sha256=source_sha,
    )
    export = conversion.artifacts["issues.jsonl"]
    verification = taskmaster_beads.verify_export(
        export,
        source_bytes=source_bytes,
        artifacts=conversion.artifacts,
        expected_source_sha256=source_sha,
    )
    issue_count = conversion.manifest["counts"]["issues"]
    empty_attestation = {
        "issue_count": 0,
        "working_set_changes": 1,
        "expected_config_changes": 1,
        "unexpected_working_changes": 0,
        "branch_count": 1,
        "main_branch_count": 1,
        "commit_count": 1,
    }
    summary_fields = {
        "schema_version": 1,
        "created": issue_count,
        "skipped": 0,
        "stale_skipped_ids_count": 0,
        "tie_kept_local_ids_count": 0,
        "updated_issues_count": 0,
    }
    dry_run = {**summary_fields, "dry_run": True, "ids_count": 0}
    imported = {**summary_fields, "dry_run": False, "ids_count": issue_count}
    preflight_head = "a" * 32
    imported_head = "b" * 32
    canonical_export = taskmaster_beads._canonical_operational_export(
        export,
        step="test promotion export",
    )
    target_repo = tmp_path / "aegis-isolated-target"
    target_repo.mkdir(mode=0o700)
    (target_repo / ".git").mkdir(mode=0o700)
    report = {
        "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
        "status": "pass",
        "source": {"sha256": source_sha, "tag": "master"},
        "target": {
            "directory": target_repo.as_posix(),
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
        "dry_run": dry_run,
        "first_import": imported,
        "first_verification": verification,
        "second_import": imported,
        "final_verification": verification,
        "idempotency": {
            "status": "pass",
            "canonical_export_sha256": hashlib.sha256(canonical_export).hexdigest(),
            "first_raw_export_sha256": hashlib.sha256(export).hexdigest(),
            "final_raw_export_sha256": hashlib.sha256(export).hexdigest(),
            "preflight_dolt_main_head": preflight_head,
            "post_dry_run_dolt_main_head": preflight_head,
            "first_dolt_main_head": imported_head,
            "final_dolt_main_head": imported_head,
            "dry_run_head_unchanged": True,
            "first_import_advanced_main": True,
            "export_unchanged": True,
            "raw_export_unchanged": True,
            "dolt_main_head_unchanged": True,
        },
        "credential_transport": "runner-environment-only",
        "locked_toolchain": _recorded_toolchain(lock_path, value),
    }
    migration_artifacts = {
        **{f"conversion/{name}": content for name, content in conversion.artifacts.items()},
        "checkpoints/empty-target.json": (
            json.dumps(
                {
                    "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                    "status": "pass",
                    "phase": "empty-target",
                    **empty_attestation,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode(),
        "checkpoints/first-import.json": (
            json.dumps(
                {
                    "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                    "status": "mutation-observed",
                    "phase": "first-import",
                    "source_sha256": source_sha,
                    "preflight_dolt_main_head": preflight_head,
                    "first_dolt_main_head": imported_head,
                    "import": imported,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode(),
        "checkpoints/second-import.json": (
            json.dumps(
                {
                    "schema_version": taskmaster_beads.MIGRATION_RUN_SCHEMA,
                    "status": "mutation-observed",
                    "phase": "second-import",
                    "source_sha256": source_sha,
                    "first_dolt_main_head": imported_head,
                    "final_dolt_main_head": imported_head,
                    "import": imported,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode(),
        "exports/first.jsonl": export,
        "exports/final.jsonl": export,
        "migration-report.json": (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(),
    }
    assert set(migration_artifacts) == gas_city_ops.MIGRATION_REQUIRED_ARTIFACTS
    migration_digests = {
        name: gas_city_ops.write_private_evidence_bytes(migration_root, name, content)
        for name, content in migration_artifacts.items()
    }
    migration_path = _write_json_evidence(
        migration_root / "evidence-manifest.json",
        {
            "schema_version": "taskmaster-beads-migration-evidence/v1",
            "status": "pass",
            "source_sha256": source_sha,
            "artifacts": migration_digests,
        },
    )
    native_backup = city / "runtime" / "evidence" / "recovery" / "native-backup"
    _write(native_backup / "native" / "backup.json", b'{"backup":true}\n')
    native_backup_manifest = gas_city_ops._native_backup_manifest_bytes(
        gas_city_ops._file_tree_manifest(native_backup, label="test native backup")
    )
    native_backup_manifest_path = native_backup.parent / (
        native_backup.name + gas_city_ops.NATIVE_BACKUP_MANIFEST_SUFFIX
    )
    _write(native_backup_manifest_path, native_backup_manifest)
    recovery_path = _write_json_evidence(
        city / "runtime" / "evidence" / "recovery" / "restore.json",
        {
            "schema_version": gas_city_ops.NATIVE_RESTORE_SCHEMA_VERSION,
            "kind": "dolt-native-restore-drill",
            "status": "pass",
            "captured_at": "2026-07-15T11:00:00Z",
            "verified_at": "2026-07-15T11:05:00Z",
            "backup_path": native_backup.as_posix(),
            "backup_server_path": native_backup.as_posix(),
            "backup_manifest_path": native_backup_manifest_path.as_posix(),
            "backup_manifest_sha256": hashlib.sha256(native_backup_manifest).hexdigest(),
            "source_endpoint": {
                "host": "127.0.0.1",
                "port": gas_city_ops.AEGIS_BEADS_INIT_PORT,
                "user": gas_city_ops.AEGIS_RECOVERY_USER,
                "database": "aegis_beads",
            },
            "restore_endpoint": {
                "host": "127.0.0.1",
                "port": 33072,
                "user": "restore_user",
                "database": "aegis_beads",
            },
            "source_server": _recorded_restore_server(
                "gas-city-aegis-dolt",
                identity="1",
                port=gas_city_ops.AEGIS_BEADS_INIT_PORT,
                backup_source=native_backup.parent,
                backup_read_write=True,
                image_id=value["images"]["dolt_server"]["image_id"],
                relay_image_id=value["images"]["egress_proxy"]["image_id"],
            ),
            "restore_server": _recorded_restore_server(
                "restore-dolt",
                identity="2",
                port=33072,
                backup_source=native_backup.parent,
                backup_read_write=False,
            ),
            "restore_preflight": {
                "empty_issue_count": 0,
                "empty_export_sha256": hashlib.sha256(b"").hexdigest(),
                "dolt_head": "a" * 32,
            },
            "dolt_head": "b" * 32,
            "canonical_export_sha256": hashlib.sha256(canonical_export).hexdigest(),
            "backup_status": {"status": "current"},
            "locked_toolchain": _recorded_toolchain(lock_path, value),
            "secrets_included": False,
        },
    )
    stopped_gen1 = _write_json_evidence(
        city / "runtime" / "evidence" / "workers" / "generation-1.json",
        {
            "schema_version": 1,
            "kind": "gas-city-workers-stopped",
            "status": "pass",
            "rig": "aegis",
            "observed_at": "2026-07-15T11:05:00Z",
            "supervisor_running": False,
            "active_provider_containers": [],
            "active_sessions": [],
            "suspension_state": {
                "path": ".gc/runtime/suspension-state.json",
                "sha256": "9" * 64,
                "city_suspended": True,
                "aegis_suspended": True,
                "updated_at": "2026-07-15T11:04:00Z",
            },
        },
    )
    gas_city_authority.initialize_production_authority(
        city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        snapshot_dir=snapshot_dir,
        migration_evidence_path=migration_path,
        recovery_evidence_path=recovery_path,
        expected_target_directory=target_repo,
        stopped_workers_path=stopped_gen1,
        stopped_workers_hook=lambda phase, path, evidence: True,
        activated_at="2026-07-15T11:06:00Z",
    )
    stopped_gen2 = _write_json_evidence(
        city / "runtime" / "evidence" / "workers" / "generation-2.json",
        {
            "schema_version": 1,
            "kind": "gas-city-workers-stopped",
            "status": "pass",
            "rig": "aegis",
            "observed_at": "2026-07-15T11:07:00Z",
            "supervisor_running": False,
            "active_provider_containers": [],
            "active_sessions": [],
            "suspension_state": {
                "path": ".gc/runtime/suspension-state.json",
                "sha256": "9" * 64,
                "city_suspended": True,
                "aegis_suspended": True,
                "updated_at": "2026-07-15T11:07:00Z",
            },
        },
    )
    gas_city_authority.activate_beads_authority(
        city,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        stopped_workers_path=stopped_gen2,
        stopped_workers_hook=lambda phase, path, evidence: True,
        activated_at="2026-07-15T11:08:00Z",
    )
    authority_promotion = gas_city_ops.capture_authority_evidence(
        lock_path,
        snapshot_dir,
        city / "runtime" / "evidence" / "canary" / "authority.json",
        clock=lambda: dt.datetime(2026, 7, 15, 11, 10, tzinfo=dt.timezone.utc),
    )
    authority_promotion_path = Path(authority_promotion["evidence_path"])
    provider_capture = gas_city_ops.capture_provider_evidence(
        lock_path,
        claude_supervisor_receipt=provider_session_artifacts["claude"][0],
        claude_transcript=provider_session_artifacts["claude"][1],
        codex_supervisor_receipt=provider_session_artifacts["codex"][0],
        codex_transcript=provider_session_artifacts["codex"][1],
        output_path=city / "runtime" / "evidence" / "canary" / "providers.json",
        clock=lambda: dt.datetime(2026, 7, 15, 11, 9, tzinfo=dt.timezone.utc),
    )
    provider_path = Path(provider_capture["evidence_path"])
    _write(city / "bin" / "bd", b"bd", 0o555)
    _write(city / "bin" / "gc", b"gc", 0o555)
    aegis_source = tmp_path / "aegis-source"
    aegis_source.mkdir(mode=0o700)
    obsidian_capture = gas_city_ops.capture_obsidian_evidence(
        lock_path,
        target_repo=target_repo,
        first_vault=city / "runtime" / "evidence" / "obsidian" / "build-1",
        second_vault=city / "runtime" / "evidence" / "obsidian" / "build-2",
        output_path=city / "runtime" / "evidence" / "canary" / "obsidian.json",
        source_root=aegis_source,
        runner=ObsidianBuildRunner(),
        clock=lambda: dt.datetime(2026, 7, 15, 11, 9, 30, tzinfo=dt.timezone.utc),
    )
    obsidian_path = Path(obsidian_capture["evidence_path"])
    canary_worktree = tmp_path / "aegis-canary-worktree"
    canary_worktree.mkdir(mode=0o700)
    canary_bin = tmp_path / "canary-bin"
    git_binary = canary_bin / "git"
    gh_binary = canary_bin / "gh"
    _write(git_binary, b"git", 0o555)
    _write(gh_binary, b"gh", 0o555)
    canary_runner = ControlledCanaryRunner(target_repo, canary_worktree)
    intent = gas_city_ops.start_controlled_canary(
        lock_path,
        target_repo=target_repo,
        bead_id="ags-canary",
        git_binary=git_binary,
        gh_binary=gh_binary,
        runner=canary_runner,
        environment={"GH_TOKEN": "t" * 40},
        clock=lambda: dt.datetime(2026, 7, 15, 11, 11, tzinfo=dt.timezone.utc),
        nonce_factory=lambda: ControlledCanaryRunner.RUN_ID,
    )
    if canary_mutator is not None:
        canary_mutator(canary_runner)
    captured_at = capture_time or dt.datetime(2026, 7, 15, 11, 20, tzinfo=dt.timezone.utc)
    canary_capture = gas_city_ops.capture_controlled_canary(
        lock_path,
        intent_path=Path(intent["intent_path"]),
        canary_worktree=canary_worktree,
        git_binary=git_binary,
        gh_binary=gh_binary,
        runner=canary_runner,
        environment={"GH_TOKEN": "t" * 40},
        clock=lambda: captured_at,
    )
    github_path = Path(canary_capture["github_evidence_path"])
    canary_path = Path(canary_capture["canary_evidence_path"])
    return (
        {
            "backup": Path(backup["manifest_path"]),
            "migration": migration_path,
            "recovery": recovery_path,
            "authority": authority_promotion_path,
            "provider": provider_path,
            "github": github_path,
            "obsidian": obsidian_path,
            "canary": canary_path,
        },
        github_path,
    )


def test_production_promotion_requires_all_evidence_and_full_continuous_24h_soak(
    tmp_path: Path,
) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, github_path = _promotion_evidence(tmp_path, lock_path, value)
    started = dt.datetime(2026, 7, 15, 12, tzinfo=dt.timezone.utc)

    promoted = gas_city_ops.promote_canary_runtime(
        lock_path,
        evidence,
        clock=lambda: started,
    )
    assert promoted["status"] == "canary_passed_soaking"
    soak_root = lock_path.parent / "runtime" / "evidence" / "soak"
    start_path = soak_root / "start.json"
    soak_start = gas_city_ops.start_soak(lock_path, start_path, clock=lambda: started)
    observations_path = soak_root / "observations.jsonl"
    vault = lock_path.parent / "runtime" / "evidence" / "obsidian" / "build-1"
    runner = SoakProbeRunner(lock_path.parent, vault)
    for hour in range(25):
        if hour in {0, 6, 12, 18}:
            for provider in ("claude", "codex"):
                _write_soak_session_receipt(
                    lock_path,
                    provider=provider,
                    recorded_at=started + dt.timedelta(hours=hour),
                    sequence=hour + (0 if provider == "claude" else 100),
                )
        gas_city_ops.capture_soak_observation(
            lock_path,
            target_repo=tmp_path / "aegis-isolated-target",
            vault=vault,
            observations_path=observations_path,
            source_root=tmp_path / "aegis-source",
            runner=runner,
            clock=lambda hour=hour: started + dt.timedelta(hours=hour),
        )

    drifted_records = [json.loads(line) for line in observations_path.read_text().splitlines()]
    drifted_records[12]["authority"]["receipt_sha256"] = "0" * 64
    drifted_path = soak_root / "authority-drift.jsonl"
    _write(
        drifted_path,
        b"".join(
            (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
            for record in drifted_records
        ),
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="chained live-probe"):
        gas_city_ops.finish_soak(
            lock_path,
            start_path,
            drifted_path,
            soak_root / "authority-drift-finish.json",
            clock=lambda: started + dt.timedelta(hours=24),
        )

    with pytest.raises(gas_city_ops.GasCityOpsError, match="required 24 hours"):
        gas_city_ops.finish_soak(
            lock_path,
            start_path,
            observations_path,
            soak_root / "too-early.json",
            clock=lambda: started + dt.timedelta(hours=23),
        )

    finish_path = soak_root / "finish.json"
    finished = gas_city_ops.finish_soak(
        lock_path,
        start_path,
        observations_path,
        finish_path,
        clock=lambda: started + dt.timedelta(hours=24),
    )
    assert finished["duration_seconds"] == 24 * 60 * 60
    production = gas_city_ops.promote_runtime_production(
        lock_path,
        finish_path,
        clock=lambda: started + dt.timedelta(hours=24, minutes=1),
    )
    assert production["status"] == "production"
    assert gas_city_ops.load_runtime_lock(lock_path)["status"] == "production"

    _write(github_path, github_path.read_bytes() + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="content digest mismatch"):
        gas_city_ops.load_runtime_lock(lock_path)


def test_canary_rejects_rehashed_but_fabricated_migration_artifacts(tmp_path: Path) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, _ = _promotion_evidence(tmp_path, lock_path, value)
    migration_manifest_path = evidence["migration"]
    migration_manifest = json.loads(migration_manifest_path.read_text())
    conversion_path = migration_manifest_path.parent / "conversion" / "manifest.json"
    conversion = json.loads(conversion_path.read_text())
    conversion["fabricated_pass"] = True
    _write(
        conversion_path,
        (json.dumps(conversion, indent=2, sort_keys=True) + "\n").encode(),
    )
    migration_manifest["artifacts"]["conversion/manifest.json"] = hashlib.sha256(
        conversion_path.read_bytes()
    ).hexdigest()
    _write(
        migration_manifest_path,
        (json.dumps(migration_manifest, indent=2, sort_keys=True) + "\n").encode(),
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="artifact drift|not deterministic"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)


def test_canary_requires_complete_untampered_authority_history(tmp_path: Path) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, _ = _promotion_evidence(tmp_path, lock_path, value)
    receipt = lock_path.parent / gas_city_ops.LIVE_AUTHORITY_RECEIPT_PATH
    assert (
        task_authority.load_authority_receipt(
            receipt,
            expected_rig="aegis",
            expected_beads_prefix="ags",
            expected_database="aegis_beads",
        ).generation
        == 2
    )

    generation_one = (
        lock_path.parent
        / "runtime"
        / "authority"
        / "history"
        / "aegis"
        / "generation-00000001.json"
    )
    _write(generation_one, generation_one.read_bytes() + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="lifecycle is invalid"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)


def test_provider_and_obsidian_evidence_rehash_real_artifacts(tmp_path: Path) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, _ = _promotion_evidence(tmp_path, lock_path, value)
    provider = json.loads(evidence["provider"].read_text())
    transcript = lock_path.parent / provider["sessions"]["codex"]["transcript"]["path"]
    _write(
        transcript,
        transcript.read_bytes()
        + b'{"type":"turn_context","payload":{"model":"gpt-5.6-sol","effort":"high"}}\n',
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="supervisor receipt|receipt drift"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)

    # Recreate a clean fixture so the projection failure is independently proven.
    second_root = tmp_path / "projection"
    second_root.mkdir()
    lock_path, value = _provisioned_runtime(second_root)
    evidence, _ = _promotion_evidence(second_root, lock_path, value)
    obsidian = json.loads(evidence["obsidian"].read_text())
    vault = lock_path.parent / obsidian["builds"][0]["directory"]
    _write(vault / "caller-authored-pass.md", b"pass\n")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="valid Beads projection"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)


def test_obsidian_and_canary_bind_the_generation_one_primary_repository(
    tmp_path: Path,
) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, _ = _promotion_evidence(tmp_path, lock_path, value)
    city = lock_path.parent
    target = tmp_path / "aegis-isolated-target"
    identity = task_authority.repository_identity(target)
    generation_path = (
        city / "runtime" / "authority" / "history" / "aegis" / "generation-00000001.json"
    )
    expected_target = {
        "generation": 1,
        "generation_record_sha256": hashlib.sha256(generation_path.read_bytes()).hexdigest(),
        "repository_root": identity.repository_root.as_posix(),
        "git_common_dir": identity.git_common_dir.as_posix(),
        "repository_key": identity.repository_key,
    }
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    assert generation["baseline_evidence"]["migration"]["target_directory"] == target.as_posix()

    obsidian = json.loads(evidence["obsidian"].read_text(encoding="utf-8"))
    canary = json.loads(evidence["canary"].read_text(encoding="utf-8"))
    intent_path = city / canary["intent"]["path"]
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    assert obsidian["schema_version"] == gas_city_ops.OBSIDIAN_EVIDENCE_SCHEMA_VERSION
    assert intent["schema_version"] == gas_city_ops.CANARY_RUN_SCHEMA
    assert canary["schema_version"] == gas_city_ops.CANARY_EVIDENCE_SCHEMA_VERSION
    assert obsidian["authority_target"] == expected_target
    assert intent["authority_target"] == expected_target
    assert canary["authority_target"] == expected_target
    assert intent["primary"]["path"] == expected_target["repository_root"]
    assert canary["primary"]["common_git_dir"] == expected_target["git_common_dir"]

    copied = tmp_path / "identical-aegis-copy"
    copied.mkdir(mode=0o700)
    (copied / ".git").mkdir(mode=0o700)

    def forbidden_runner(argv, cwd, environment):  # pragma: no cover - must fail earlier.
        raise AssertionError((argv, cwd, environment))

    with pytest.raises(
        gas_city_ops.GasCityOpsError,
        match="generation-1 canonical Aegis migration target",
    ):
        gas_city_ops.capture_obsidian_evidence(
            lock_path,
            target_repo=copied,
            first_vault=city / "runtime" / "evidence" / "obsidian" / "wrong-1",
            second_vault=city / "runtime" / "evidence" / "obsidian" / "wrong-2",
            output_path=city / "runtime" / "evidence" / "canary" / "wrong-obsidian.json",
            source_root=tmp_path,
            runner=forbidden_runner,
        )
    with pytest.raises(
        gas_city_ops.GasCityOpsError,
        match="generation-1 canonical Aegis migration target",
    ):
        gas_city_ops.start_controlled_canary(
            lock_path,
            target_repo=copied,
            bead_id="ags-canary",
            git_binary=tmp_path / "canary-bin" / "git",
            gh_binary=tmp_path / "canary-bin" / "gh",
            runner=forbidden_runner,
            environment={"GH_TOKEN": "t" * 40},
        )

    tampered_obsidian = json.loads(evidence["obsidian"].read_text(encoding="utf-8"))
    tampered_obsidian["authority_target"]["repository_root"] = copied.as_posix()
    with pytest.raises(gas_city_ops.GasCityOpsError, match="deterministic rebuild"):
        gas_city_ops._validate_obsidian_evidence(
            tampered_obsidian,
            gas_city_ops.load_runtime_lock(lock_path),
            lock_root=city,
        )

    records = {
        kind: gas_city_ops._evidence_record_for_path(
            city,
            path,
            label=f"test {kind} evidence",
        )
        for kind, path in evidence.items()
    }
    tampered_canary = json.loads(evidence["canary"].read_text(encoding="utf-8"))
    tampered_canary["authority_target"]["repository_key"] = "0" * 64
    with pytest.raises(gas_city_ops.GasCityOpsError, match="controlled Aegis receipt"):
        gas_city_ops._validate_canary_evidence(
            tampered_canary,
            lock_root=city,
            evidence_path=evidence["canary"],
            evidence_records=records,
        )

    tampered_intent = json.loads(intent_path.read_text(encoding="utf-8"))
    tampered_intent["authority_target"]["repository_key"] = "0" * 64
    _write(
        intent_path,
        (json.dumps(tampered_intent, indent=2, sort_keys=True) + "\n").encode(),
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="not bound to live Aegis authority"):
        gas_city_ops._validated_canary_intent(city, intent_path)


def test_controlled_canary_rejects_fabrication_mismatch_staleness_and_replay(
    tmp_path: Path,
) -> None:
    lock_path, value = _provisioned_runtime(tmp_path)
    evidence, _ = _promotion_evidence(tmp_path, lock_path, value)
    city = lock_path.parent

    fabricated_github = _write_json_evidence(
        city / "runtime" / "evidence" / "canary" / "fabricated-github.json",
        {
            "schema_version": 1,
            "kind": "github-delivery-canary",
            "status": "pass",
            "operations": {
                "auth_status": True,
                "read": True,
                "push": True,
                "draft_pr": True,
            },
            "remote_unchanged": True,
        },
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="run-bound delivery"):
        gas_city_ops._validate_github_evidence(
            json.loads(fabricated_github.read_text()),
            lock_root=city,
            evidence_path=fabricated_github,
        )

    fabricated_canary = _write_json_evidence(
        city / "runtime" / "evidence" / "canary" / "fabricated-aegis.json",
        {
            "schema_version": 1,
            "kind": "aegis-controlled-canary",
            "status": "pass",
            "isolated_worktree": True,
            "primary_checkout_untouched": True,
            "checks": {name: "pass" for name in gas_city_ops.CANARY_REQUIRED_CHECKS},
        },
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="controlled Aegis receipt"):
        gas_city_ops._validate_canary_evidence(
            json.loads(fabricated_canary.read_text()),
            lock_root=city,
            evidence_path=fabricated_canary,
            evidence_records={},
        )

    primary = tmp_path / "aegis-isolated-target"
    git_binary = tmp_path / "canary-bin" / "git"
    gh_binary = tmp_path / "canary-bin" / "gh"

    def start_case(character: str):
        run_id = character * 32
        worktree = tmp_path / f"negative-worktree-{character}"
        worktree.mkdir(mode=0o700)
        runner = ControlledCanaryRunner(primary, worktree, run_id=run_id)
        intent = gas_city_ops.start_controlled_canary(
            lock_path,
            target_repo=primary,
            bead_id="ags-canary",
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 15, 11, 11, tzinfo=dt.timezone.utc),
            nonce_factory=lambda: run_id,
        )
        return worktree, runner, intent

    worktree, runner, intent = start_case("1")
    runner.pr_head = "7" * 40
    with pytest.raises(gas_city_ops.GasCityOpsError, match="exact merged canary branch"):
        gas_city_ops.capture_controlled_canary(
            lock_path,
            intent_path=Path(intent["intent_path"]),
            canary_worktree=worktree,
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 15, 11, 20, tzinfo=dt.timezone.utc),
        )

    worktree, runner, intent = start_case("2")
    runner.remote_merge = "7" * 40
    with pytest.raises(gas_city_ops.GasCityOpsError, match="base ref is not"):
        gas_city_ops.capture_controlled_canary(
            lock_path,
            intent_path=Path(intent["intent_path"]),
            canary_worktree=worktree,
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 15, 11, 20, tzinfo=dt.timezone.utc),
        )

    worktree, runner, intent = start_case("3")
    runner.final_assignee = "different-owner"
    with pytest.raises(gas_city_ops.GasCityOpsError, match="refinery owner"):
        gas_city_ops.capture_controlled_canary(
            lock_path,
            intent_path=Path(intent["intent_path"]),
            canary_worktree=worktree,
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 15, 11, 20, tzinfo=dt.timezone.utc),
        )

    worktree, runner, intent = start_case("4")
    runner.worktree_branch = "polecat/ags-other-run"
    with pytest.raises(gas_city_ops.GasCityOpsError, match="run-bound isolated branch"):
        gas_city_ops.capture_controlled_canary(
            lock_path,
            intent_path=Path(intent["intent_path"]),
            canary_worktree=worktree,
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 15, 11, 20, tzinfo=dt.timezone.utc),
        )

    worktree, runner, intent = start_case("5")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="intent is stale"):
        gas_city_ops.capture_controlled_canary(
            lock_path,
            intent_path=Path(intent["intent_path"]),
            canary_worktree=worktree,
            git_binary=git_binary,
            gh_binary=gh_binary,
            runner=runner,
            environment={"GH_TOKEN": "t" * 40},
            clock=lambda: dt.datetime(2026, 7, 16, 11, 12, tzinfo=dt.timezone.utc),
        )

    github_value = json.loads(evidence["github"].read_text())
    pr_artifact = city / github_value["artifacts"]["github_pr"]["path"]
    original_pr_artifact = pr_artifact.read_bytes()
    _write(pr_artifact, original_pr_artifact + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="artifact digest mismatch"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)
    _write(pr_artifact, original_pr_artifact)

    intact_canary_value = json.loads(evidence["canary"].read_text())
    bead_artifact = city / intact_canary_value["artifacts"]["beads_final"]["path"]
    original_bead_artifact = bead_artifact.read_bytes()
    _write(bead_artifact, original_bead_artifact + b" ")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="artifact digest mismatch"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)
    _write(bead_artifact, original_bead_artifact)

    canary_value = json.loads(evidence["canary"].read_text())
    canary_value["rig"] = "other-rig"
    _write(
        evidence["canary"],
        (json.dumps(canary_value, indent=2, sort_keys=True) + "\n").encode(),
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="controlled Aegis receipt"):
        gas_city_ops.promote_canary_runtime(lock_path, evidence)


def test_soak_rejects_caller_authored_pass_rows(tmp_path: Path) -> None:
    started = dt.datetime(2026, 7, 15, 12, tzinfo=dt.timezone.utc)
    rows = [
        {
            "observed_at": (started + dt.timedelta(hours=hour)).isoformat().replace("+00:00", "Z"),
            "status": "pass",
            "checks": {name: "pass" for name in gas_city_ops.SOAK_REQUIRED_CHECKS},
            "authority": {"receipt_sha256": "a" * 64},
        }
        for hour in (0, 24)
    ]
    content = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in rows
    )
    with pytest.raises(gas_city_ops.GasCityOpsError, match="chained live-probe"):
        gas_city_ops._validate_soak_observations(
            content,
            started=started,
            ended=started + dt.timedelta(hours=24),
            expected_authority=rows[0]["authority"],
            lock_root=tmp_path,
        )
