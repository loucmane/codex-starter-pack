from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

from aegis_foundation import task_authority


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
LAUNCHER = DEPLOY / "bin" / "provider-container"
RUNTIME_SOURCE = DEPLOY / "docker" / "task-authority.py"
RUNTIME_DIGEST = "5ea3e3cad6b71fbaf6c976c0ba5e1e948fc0cb1267575c5611a8d3bde9c1c11f"


def _supervisor_module():
    path = DEPLOY / "docker" / "provider-supervisor.py"
    spec = importlib.util.spec_from_file_location("provider_supervisor_authority_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_launcher_binds_explicit_authority_and_read_only_taskmaster() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")

    assert "AEGIS_TASK_AUTHORITY_FILE=/run/gas-city/authority/aegis.json" in source
    assert "AEGIS_TASK_AUTHORITY_RUNTIME_FILE=/opt/gas-city/task-authority.py" in source
    assert 'AEGIS_TASK_AUTHORITY_RUNTIME_SHA256=$task_authority_sha256' in source
    assert "AEGIS_BD_EXECUTABLE=/usr/local/bin/bd" in source
    assert 'AEGIS_BD_SHA256=$bd_sha256' in source
    assert '"$city_runtime/authority"' in source
    assert 'src=$authority_root,dst=/run/gas-city/authority,readonly' in source
    assert 'dst=$repo_root/.taskmaster,readonly' in source
    assert 'src=$beads_dir,dst=$beads_dir,readonly' in source
    assert "permits only the exact Aegis rig identity aegis/ags" in source
    assert "rig-scoped workdir %s cannot fall back to HQ identity" in source
    assert '"$city_root/.gc/agents/boot"' in source
    assert '"$city_root/.gc/agents/deacon"' in source
    assert '"$city_root/.gc/agents/mayor"' in source
    assert '"$city_root/.gc/agents/dogs"' in source
    hq_roots = source.split("allowed_roots=(", 2)[2].split(")", 1)[0]
    assert ".gc/worktrees" not in hq_roots

    # The authority submount must be appended after the writable receipt root
    # mount array is initialized; otherwise a later assignment silently drops it.
    assert source.index("mount_args=(") < source.index(
        'dst=/run/gas-city/authority,readonly'
    )
    # The Taskmaster submount must follow the writable repository bind so it
    # overrides that one subtree as read-only inside the worker.
    assert source.index('src=$repo_root,dst=$repo_root') < source.index(
        'dst=$repo_root/.taskmaster,readonly'
    )


def test_provider_authority_digest_comes_from_the_locked_bd_binary() -> None:
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text(encoding="utf-8"))
    digest = lock["tools"]["bd"]["binary_sha256"]
    source = LAUNCHER.read_text(encoding="utf-8")

    assert len(digest) == 64
    assert 'jq -er \'.tools.bd.binary_sha256' in source
    assert digest not in source


def test_task_authority_runtime_is_immutable_pinned_build_input() -> None:
    dockerfile = (DEPLOY / "docker" / "Dockerfile").read_text(encoding="utf-8")
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text(encoding="utf-8"))

    assert RUNTIME_SOURCE.read_bytes() == (ROOT / "aegis_foundation" / "task_authority.py").read_bytes()
    assert hashlib.sha256(RUNTIME_SOURCE.read_bytes()).hexdigest() == RUNTIME_DIGEST
    assert "COPY docker/task-authority.py /opt/gas-city/task-authority.py" in dockerfile
    assert f"{RUNTIME_DIGEST}  /opt/gas-city/task-authority.py" in dockerfile
    assert "chmod 0444 /opt/gas-city/task-authority.py" in dockerfile
    assert lock["task_authority_runtime"] == {
        "source_path": "docker/task-authority.py",
        "image_path": "/opt/gas-city/task-authority.py",
        "sha256": RUNTIME_DIGEST,
    }


def _configure_supervisor_authority(monkeypatch, tmp_path: Path):
    supervisor = _supervisor_module()
    city = tmp_path / "gas-city"
    rig_root = tmp_path / "aegis"
    workdir = city / ".gc" / "worktrees" / "aegis" / "polecat"
    beads_dir = rig_root / ".beads"
    workdir.mkdir(parents=True)
    beads_dir.mkdir(parents=True)
    runtime = tmp_path / "immutable-image" / "task-authority.py"
    runtime.parent.mkdir()
    runtime.write_bytes(RUNTIME_SOURCE.read_bytes())
    runtime.chmod(0o444)
    authority_root = tmp_path / "authority"
    receipt_path = authority_root / "aegis.json"
    evidence = task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=hashlib.sha256(b"snapshot").hexdigest(),
        migration_report_sha256=hashlib.sha256(b"migration").hexdigest(),
        backup_restore_report_sha256=hashlib.sha256(b"restore").hexdigest(),
    )
    first = task_authority.initialize_taskmaster_authority(
        receipt_path,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        evidence=evidence,
        activated_at="2026-07-15T18:00:00Z",
    )
    second = task_authority.transition_authority(
        receipt_path,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=first.generation,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=evidence,
        activated_at="2026-07-15T18:01:00Z",
    )
    identity = dict(supervisor.AEGIS_RUNTIME_IDENTITY)
    identity.update(
        {
            "GC_CITY_ROOT": str(city),
            "GC_RIG_ROOT": str(rig_root),
            "BEADS_DIR": str(beads_dir),
        }
    )
    monkeypatch.setattr(supervisor, "AEGIS_RUNTIME_IDENTITY", identity)
    monkeypatch.setattr(supervisor, "TASK_AUTHORITY_RUNTIME_PATH", runtime)
    monkeypatch.setattr(supervisor, "TASK_AUTHORITY_RUNTIME_UID", os.getuid())
    monkeypatch.setattr(supervisor, "TASK_AUTHORITY_RECEIPT_PATH", receipt_path)
    for name, value in identity.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("AEGIS_TASK_AUTHORITY_FILE", str(receipt_path))
    monkeypatch.setenv("AEGIS_TASK_AUTHORITY_RUNTIME_FILE", str(runtime))
    monkeypatch.setenv("AEGIS_TASK_AUTHORITY_RUNTIME_SHA256", RUNTIME_DIGEST)
    monkeypatch.chdir(workdir)
    return supervisor, receipt_path, evidence, second, runtime


def test_supervisor_requires_live_generation_two_and_observes_atomic_replacement(
    monkeypatch,
    tmp_path: Path,
) -> None:
    supervisor, receipt_path, evidence, second, _runtime = _configure_supervisor_authority(
        monkeypatch, tmp_path
    )

    assert supervisor.validate_task_authority_environment() == task_authority.receipt_sha256(
        second
    )
    task_authority.transition_authority(
        receipt_path,
        target_mode=task_authority.TaskAuthorityMode.TASKMASTER,
        expected_generation=second.generation,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=evidence,
        activated_at="2026-07-15T18:02:00Z",
    )

    with pytest.raises(RuntimeError, match="exact task-authority receipt generation 2"):
        supervisor.validate_task_authority_environment()


def test_supervisor_rejects_tampered_runtime_and_worker_lock_excludes_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    supervisor, receipt_path, _evidence, _second, runtime = _configure_supervisor_authority(
        monkeypatch, tmp_path
    )
    runtime.chmod(0o644)
    runtime.write_text("raise RuntimeError('tampered')\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="permissions are not immutable 0444"):
        supervisor.validate_task_authority_environment()

    lock_path = receipt_path.with_name(receipt_path.name + ".lock")
    with lock_path.open("r+") as shared_lock, lock_path.open("r+") as transition_lock:
        fcntl.flock(shared_lock.fileno(), fcntl.LOCK_SH)
        with pytest.raises(BlockingIOError):
            fcntl.flock(transition_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(shared_lock.fileno(), fcntl.LOCK_UN)

    launcher = LAUNCHER.read_text(encoding="utf-8")
    authority_source = (ROOT / "aegis_foundation" / "task_authority.py").read_text(
        encoding="utf-8"
    )
    assert '/usr/bin/flock --shared "$authority_lock_file"' in launcher
    assert "fcntl.LOCK_EX" in authority_source


def test_provider_launcher_remains_valid_bash() -> None:
    result = subprocess.run(
        ("bash", "-n", str(LAUNCHER)),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _launcher_identity_fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    city = tmp_path / "gas-city"
    rig_root = tmp_path / "aegis"
    for path in (
        city / "runtime" / "state",
        city / "runtime" / "secrets",
        city / ".gc",
        city / "bin",
        rig_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
    (city / "runtime").chmod(0o700)
    (city / "runtime" / "state").chmod(0o700)
    (city / "runtime" / "secrets").chmod(0o700)
    for name in ("city.toml", "city.worker.toml", "pack.toml", "packs.lock"):
        (city / name).write_text("# fixture\n", encoding="utf-8")
    site = city / ".gc" / "site.toml"
    site.write_text(
        f'workspace_name = "gas-city"\n[[rig]]\nname = "aegis"\npath = "{rig_root}"\n',
        encoding="utf-8",
    )
    site.chmod(0o600)
    sentinel = city / "bin" / "locked-images"
    sentinel.write_text("#!/usr/bin/env bash\necho identity-accepted >&2\nexit 73\n", encoding="utf-8")
    sentinel.chmod(0o700)
    environment = {**os.environ, "GC_CITY_ROOT": str(city)}
    for name in ("GC_RIG", "GC_RIG_ROOT", "GC_BEADS_PREFIX"):
        environment.pop(name, None)
    return city, rig_root, sentinel, environment


def _run_launcher_identity(
    workdir: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    workdir.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [str(LAUNCHER), "codex"],
        cwd=workdir,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_launcher_rejects_missing_or_future_rig_identity_before_hq_fallback(
    tmp_path: Path,
) -> None:
    city, _rig_root, _sentinel, environment = _launcher_identity_fixture(tmp_path)

    missing = _run_launcher_identity(
        city / ".gc" / "worktrees" / "aegis" / "polecat",
        environment,
    )
    future = _run_launcher_identity(
        city / ".gc" / "worktrees" / "future" / "polecat",
        environment,
    )

    assert missing.returncode == 65
    assert "cannot fall back to HQ identity" in missing.stderr
    assert future.returncode == 65
    assert "refusing workdir outside assigned scope" in future.stderr
    assert "identity-accepted" not in missing.stderr + future.stderr


def test_launcher_accepts_only_exact_aegis_binding_and_exact_hq_agent_roots(
    tmp_path: Path,
) -> None:
    city, rig_root, _sentinel, environment = _launcher_identity_fixture(tmp_path)
    workdir = city / ".gc" / "worktrees" / "aegis" / "polecat"
    exact_environment = {
        **environment,
        "GC_RIG": "aegis",
        "GC_RIG_ROOT": str(rig_root),
        "GC_BEADS_PREFIX": "ags",
    }

    exact = _run_launcher_identity(workdir, exact_environment)
    wrong_prefix = _run_launcher_identity(
        workdir,
        {**exact_environment, "GC_BEADS_PREFIX": "future"},
    )
    wrong_root = tmp_path / "wrong-root"
    wrong_root.mkdir()
    mismatched_root = _run_launcher_identity(
        workdir,
        {**exact_environment, "GC_RIG_ROOT": str(wrong_root)},
    )
    hq = _run_launcher_identity(city / ".gc" / "agents" / "mayor", environment)

    assert exact.returncode == 73 and "identity-accepted" in exact.stderr
    assert wrong_prefix.returncode == 65
    assert "exact Aegis rig identity" in wrong_prefix.stderr
    assert mismatched_root.returncode == 65
    assert "does not match the machine-local Aegis binding" in mismatched_root.stderr
    assert hq.returncode == 73 and "identity-accepted" in hq.stderr


def test_launcher_validates_and_forwards_exact_gas_city_bead_identity(
    tmp_path: Path,
) -> None:
    city, rig_root, _sentinel, environment = _launcher_identity_fixture(tmp_path)
    workdir = city / ".gc" / "worktrees" / "aegis" / "polecat"
    exact_environment = {
        **environment,
        "GC_RIG": "aegis",
        "GC_RIG_ROOT": str(rig_root),
        "GC_BEADS_PREFIX": "ags",
    }

    accepted = _run_launcher_identity(
        workdir,
        {**exact_environment, "GC_BEAD_ID": "ags-task-1"},
    )
    wrong_prefix = _run_launcher_identity(
        workdir,
        {**exact_environment, "GC_BEAD_ID": "hq-task-1"},
    )
    unsafe = _run_launcher_identity(
        workdir,
        {**exact_environment, "GC_BEAD_ID": "ags-../../task"},
    )

    assert accepted.returncode == 73 and "identity-accepted" in accepted.stderr
    assert wrong_prefix.returncode == 65
    assert "ags-prefixed GC_BEAD_ID" in wrong_prefix.stderr
    assert unsafe.returncode == 65
    assert "unsafe or unsupported shape" in unsafe.stderr
    launcher = LAUNCHER.read_text(encoding="utf-8")
    forward_loop = launcher.split("for key in ", 1)[1].split("; do", 1)[0]
    assert "GC_BEAD_ID" in forward_loop
