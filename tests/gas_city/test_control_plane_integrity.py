from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import py_compile


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
LOCKED_IMAGES = DEPLOY / "bin" / "locked-images"
MANIFEST_PATH = DEPLOY / "control-plane-manifest.json"
EXPECTED_SOURCES = {
    "artifacts/bd",
    "artifacts/dolt",
    "artifacts/gc",
    "aegis_foundation/__init__.py",
    "aegis_foundation/version.py",
    "aegis_foundation/gas_city_authority.py",
    "aegis_foundation/gas_city_endpoint.py",
    "aegis_foundation/gas_city_ops.py",
    "aegis_foundation/obsidian_vault.py",
    "aegis_foundation/task_authority.py",
    "aegis_foundation/taskmaster_beads.py",
    "bin/aegis-claude",
    "bin/aegis-codex",
    "bin/claude-container",
    "bin/codex-container",
    "bin/compose-locked",
    "bin/gas-city-admin",
    "bin/git-worktree-broker",
    "bin/github-app-token-broker",
    "bin/locked-images",
    "bin/model-evidence-broker",
    "bin/prepare-worker-boundary",
    "bin/provision-control-plane",
    "bin/provider-auth-bootstrap",
    "bin/provider-container",
    "bin/task-master",
    "bin/with-aegis-authority",
    "compose.yaml",
    "config/city.toml",
    "config/city.worker.toml",
    "config/claude-settings.json",
    "config/codex-preflight-models.json",
    "config/codex.toml",
    "config/pack.toml",
    "config/packs.lock",
    "config/site.example.toml",
    "docker/task-authority.py",
    "formulas/aegis/mol-polecat-work.toml",
}


def _run(*arguments: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(LOCKED_IMAGES), *map(str, arguments)],
        text=True,
        capture_output=True,
        check=False,
    )


def _materialize_deployed_control_plane(city: Path) -> tuple[Path, dict[str, object]]:
    city.mkdir(mode=0o700)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for record in manifest["entries"]:
        destination = city / record["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPLOY / record["source"], destination)
        destination.chmod(int(record["destination_mode"], 8))
    shutil.copyfile(MANIFEST_PATH, city / MANIFEST_PATH.name)
    (city / MANIFEST_PATH.name).chmod(0o644)
    lock_path = city / "runtime-lock.json"
    shutil.copyfile(DEPLOY / "runtime-lock.json", lock_path)
    lock_path.chmod(0o600)
    return lock_path, manifest


def test_manifest_is_exact_complete_and_bound_by_the_runtime_lock() -> None:
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes)
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text(encoding="utf-8"))

    assert lock["control_plane_manifest"] == {
        "path": "control-plane-manifest.json",
        "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    assert set(manifest) == {"schema_version", "kind", "entries"}
    assert manifest["schema_version"] == 1
    assert manifest["kind"] == "gas-city-control-plane"
    assert {record["source"] for record in manifest["entries"]} == EXPECTED_SOURCES
    assert len(manifest["entries"]) == len(EXPECTED_SOURCES)
    assert len({record["destination"] for record in manifest["entries"]}) == len(
        EXPECTED_SOURCES
    )
    assert [record["source"] for record in manifest["entries"]] == sorted(
        EXPECTED_SOURCES
    )

    for record in manifest["entries"]:
        assert set(record) == {
            "source",
            "destination",
            "sha256",
            "source_mode",
            "destination_mode",
        }
        source = DEPLOY / record["source"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == record["sha256"]
        assert stat.S_IMODE(source.stat().st_mode) == int(record["source_mode"], 8)

    by_source = {record["source"]: record for record in manifest["entries"]}
    assert by_source["config/site.example.toml"]["destination"] == ".gc/site.toml"
    assert by_source["config/site.example.toml"]["destination_mode"] == "0600"
    assert by_source["docker/task-authority.py"]["destination"] == (
        "runtime/authority/task-authority.py"
    )
    assert by_source["docker/task-authority.py"]["destination_mode"] == "0444"
    assert by_source["bin/model-evidence-broker"] == {
        "source": "bin/model-evidence-broker",
        "destination": "bin/model-evidence-broker",
        "sha256": lock["model_evidence_broker"]["sha256"],
        "source_mode": "0755",
        "destination_mode": "0700",
    }
    assert by_source["bin/github-app-token-broker"] == {
        "source": "bin/github-app-token-broker",
        "destination": "bin/github-app-token-broker",
        "sha256": lock["github_delivery"]["broker_sha256"],
        "source_mode": "0755",
        "destination_mode": "0700",
    }
    assert by_source["config/codex-preflight-models.json"] == {
        "source": "config/codex-preflight-models.json",
        "destination": "provider-config/codex-preflight-models.json",
        "sha256": lock["codex_preflight_catalog"]["sha256"],
        "source_mode": "0644",
        "destination_mode": "0644",
    }
    for source in sorted(
        item for item in EXPECTED_SOURCES if item.startswith("aegis_foundation/")
    ):
        assert by_source[source]["destination"] == source
        assert by_source[source]["destination_mode"] == "0444"


def test_deployed_admin_runtime_is_an_exact_copy_of_reviewed_sources() -> None:
    deployed_admin = (DEPLOY / "bin" / "gas-city-admin").read_bytes()
    assert deployed_admin == (ROOT / "scripts" / "gas-city-admin").read_bytes()
    assert deployed_admin.count(b'"BD_BACKUP_ENABLED": "false"') == 2
    assert b"def _target_beads_environment()" in deployed_admin
    assert deployed_admin.count(b"environment=target_environment") == 2
    for name in (
        "__init__.py",
        "version.py",
        "gas_city_authority.py",
        "gas_city_endpoint.py",
        "gas_city_ops.py",
        "obsidian_vault.py",
        "task_authority.py",
        "taskmaster_beads.py",
    ):
        assert (DEPLOY / "aegis_foundation" / name).read_bytes() == (
            ROOT / "aegis_foundation" / name
        ).read_bytes()


def test_deployed_admin_self_verifies_before_import_or_dispatch(tmp_path: Path) -> None:
    lock_path, _ = _materialize_deployed_control_plane(tmp_path / "city")
    admin = lock_path.parent / "bin" / "gas-city-admin"
    accepted = subprocess.run(
        [admin.as_posix(), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert accepted.returncode == 0, accepted.stderr

    module = lock_path.parent / "aegis_foundation" / "gas_city_ops.py"
    module.chmod(0o644)
    module.write_bytes(module.read_bytes() + b"\n# tampered\n")
    module.chmod(0o444)
    rejected = subprocess.run(
        [admin.as_posix(), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "deployed admin file drift: aegis_foundation/gas_city_ops.py" in rejected.stderr


def test_deployed_admin_rejects_bytecode_cache_before_import(tmp_path: Path) -> None:
    lock_path, _ = _materialize_deployed_control_plane(tmp_path / "city")
    admin = lock_path.parent / "bin" / "gas-city-admin"
    module = lock_path.parent / "aegis_foundation" / "gas_city_ops.py"
    module.chmod(0o644)
    py_compile.compile(module.as_posix(), doraise=True)
    module.chmod(0o444)

    rejected = subprocess.run(
        [admin.as_posix(), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "admin package contains missing or unverified entries" in rejected.stderr


def test_source_layout_verifies_while_runtime_lock_is_staged() -> None:
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text(encoding="utf-8"))
    assert lock["status"] == "staged_pending_provisioning"
    result = _run("--verify-source", DEPLOY)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "verified source control plane\n"


def test_deployed_layout_verifies_before_image_promotion(tmp_path: Path) -> None:
    lock_path, _ = _materialize_deployed_control_plane(tmp_path / "city")
    result = _run("--verify-deployed", lock_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "verified deployed control plane\n"


def test_deployed_layout_rejects_tampered_destination(tmp_path: Path) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    destination = city / "city.toml"
    destination.write_bytes(destination.read_bytes() + b"\n# tampered\n")
    destination.chmod(0o644)

    result = _run("--verify-deployed", lock_path)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "control-plane destination city.toml digest mismatch" in result.stderr


def test_deployed_layout_rejects_missing_destination(tmp_path: Path) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    (city / "packs.lock").unlink()

    result = _run("--verify-deployed", lock_path)
    assert result.returncode != 0
    assert "control-plane destination packs.lock must be a regular" in result.stderr


def test_deployed_layout_rejects_destination_mode_drift(tmp_path: Path) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    (city / "pack.toml").chmod(0o600)

    result = _run("--verify-deployed", lock_path)
    assert result.returncode != 0
    assert "control-plane destination pack.toml mode must be 0644" in result.stderr


def test_deployed_layout_rejects_leaf_symlink(tmp_path: Path) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    destination = city / "packs.lock"
    content = destination.read_bytes()
    destination.unlink()
    target = tmp_path / "external-packs.lock"
    target.write_bytes(content)
    target.chmod(0o644)
    destination.symlink_to(target)

    result = _run("--verify-deployed", lock_path)
    assert result.returncode != 0
    assert "control-plane destination packs.lock must be a regular non-symlink" in (
        result.stderr
    )


def test_deployed_layout_rejects_parent_directory_symlink(tmp_path: Path) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    site = city / ".gc" / "site.toml"
    content = site.read_bytes()
    site.unlink()
    site.parent.rmdir()
    target = tmp_path / "external-gc"
    target.mkdir()
    (target / "site.toml").write_bytes(content)
    (target / "site.toml").chmod(0o600)
    (city / ".gc").symlink_to(target, target_is_directory=True)

    result = _run("--verify-deployed", lock_path)
    assert result.returncode != 0
    assert "must not traverse a symlink or unsafe directory" in result.stderr


def test_deployed_layout_rehashes_manifest_and_enforces_its_mode(
    tmp_path: Path,
) -> None:
    city = tmp_path / "city"
    lock_path, _ = _materialize_deployed_control_plane(city)
    installed_manifest = city / "control-plane-manifest.json"
    installed_manifest.write_bytes(installed_manifest.read_bytes() + b" ")
    installed_manifest.chmod(0o644)

    tampered = _run("--verify-deployed", lock_path)
    assert tampered.returncode != 0
    assert "control-plane manifest digest mismatch" in tampered.stderr

    shutil.copyfile(MANIFEST_PATH, installed_manifest)
    installed_manifest.chmod(0o600)
    wrong_mode = _run("--verify-deployed", lock_path)
    assert wrong_mode.returncode != 0
    assert "control-plane manifest mode must be 0644" in wrong_mode.stderr
