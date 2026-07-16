from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

from aegis_foundation import task_authority
from scripts import _aegis_installer as installer


ROOT = Path(__file__).resolve().parents[2]
READINESS = ROOT / ".claude" / "scripts" / "readiness.sh"
PRETOOL = ROOT / ".claude" / "scripts" / "pretooluse-gate.sh"


def _run(command: list[str], cwd: Path, **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        **kwargs,
    )


def _private(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def _write_executable(path: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\nprintf '%s\\n' {label!r}\n", encoding="utf-8")
    path.chmod(0o500)


def _git_repo(path: Path) -> Path:
    path.mkdir()
    assert _run(["git", "init", "-q"], path).returncode == 0
    assert _run(["git", "config", "user.email", "test@example.com"], path).returncode == 0
    assert _run(["git", "config", "user.name", "Test User"], path).returncode == 0
    (path / "README.md").write_text("manual authority fixture\n", encoding="utf-8")
    assert _run(["git", "add", "README.md"], path).returncode == 0
    assert _run(["git", "commit", "-q", "-m", "fixture"], path).returncode == 0
    return path


def _provision(tmp_path: Path) -> tuple[Path, Path, task_authority.ProjectAuthorityEnrollment]:
    repo = _git_repo(tmp_path / "repo")
    taskmaster_tasks = repo / ".taskmaster" / "tasks"
    taskmaster_tasks.mkdir(parents=True)
    (taskmaster_tasks / "tasks.json").write_text(
        '{"master":{"tasks":[]}}\n', encoding="utf-8"
    )
    beads_dir = _private(repo / ".beads")
    beads_metadata = beads_dir / "metadata.json"
    beads_metadata.write_text(
        json.dumps(
            {
                "backend": "dolt",
                "database": "dolt",
                "dolt_database": "aegis_beads",
                "dolt_mode": "server",
                "project_id": "74eb5b48-1390-4fc8-a88d-2b979bcfa7b5",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    beads_metadata.chmod(0o600)
    beads_config = beads_dir / "config.yaml"
    beads_config.write_bytes(task_authority._BEADS_CANONICAL_CONFIG)
    beads_config.chmod(0o600)
    city = _private(tmp_path / "gas-city")
    _private(city / "runtime")
    authority_root = _private(city / "runtime" / "authority")
    _private(city / "runtime" / "secrets")
    _private(city / "artifacts")
    _private(city / "provider-config")

    runtime = authority_root / "task-authority.py"
    runtime.write_bytes(Path(task_authority.__file__).read_bytes())
    runtime.chmod(0o444)
    _write_executable(city / "artifacts" / "bd", "bd")
    _write_executable(city / "artifacts" / "claude", "claude")
    _write_executable(city / "artifacts" / "codex" / "bin" / "codex", "codex")
    claude_settings = {
        "switchModelsOnFlag": False,
        "disableAllHooks": False,
        "enableAllProjectMcpServers": False,
        "skipDangerousModePermissionPrompt": False,
    }
    settings = city / "provider-config" / "claude-settings.json"
    settings.write_text(json.dumps(claude_settings, sort_keys=True) + "\n", encoding="utf-8")
    settings.chmod(0o600)
    password = city / "runtime" / "secrets" / "aegis-app-password"
    password.write_text("CorrectHorseBatteryStaple-12345678\n", encoding="utf-8")
    password.chmod(0o600)

    receipt_path = authority_root / "aegis.json"
    evidence = task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=hashlib.sha256(b"snapshot").hexdigest(),
        migration_report_sha256=hashlib.sha256(b"migration").hexdigest(),
        backup_restore_report_sha256=hashlib.sha256(b"recovery").hexdigest(),
    )
    task_authority.initialize_taskmaster_authority(
        receipt_path,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        evidence=evidence,
        activated_at="2026-07-15T20:00:00Z",
    )
    task_authority.transition_authority(
        receipt_path,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=1,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=evidence,
        activated_at="2026-07-15T20:01:00Z",
    )
    enrollment = task_authority.activate_project_enrollment(
        repo, city, activated_at="2026-07-15T20:02:00Z"
    )
    return repo, city, enrollment


def test_unenrolled_legacy_repo_keeps_implicit_taskmaster(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path / "legacy")

    assert task_authority.load_project_enrollment(repo) is None
    assert task_authority.validate_project_authority_environment(repo, {}) is None
    selected = task_authority.load_authority_from_environment({})
    assert selected.mode is task_authority.TaskAuthorityMode.TASKMASTER
    assert selected.explicit is False


def test_enrolled_project_requires_complete_exact_environment(tmp_path: Path) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    expected = enrollment.expected_environment()

    with pytest.raises(task_authority.TaskAuthorityError, match="complete authority environment"):
        task_authority.validate_project_authority_environment(repo, {})

    partial = dict(expected)
    partial.pop("GC_DOLT_USER")
    with pytest.raises(task_authority.TaskAuthorityError, match="GC_DOLT_USER"):
        task_authority.validate_project_authority_environment(repo, partial)

    mismatch = dict(expected)
    mismatch["BEADS_DOLT_SERVER_PORT"] = "33070"
    with pytest.raises(task_authority.TaskAuthorityError, match="environment mismatch"):
        task_authority.validate_project_authority_environment(repo, mismatch)

    assert task_authority.validate_project_authority_environment(repo, expected) == enrollment


def test_primary_and_linked_worktree_share_one_enrollment(tmp_path: Path) -> None:
    repo, _city, primary = _provision(tmp_path)
    linked = tmp_path / "linked"
    result = _run(
        ["git", "worktree", "add", "-q", "-b", "polecat/ags-work-1", str(linked)],
        repo,
    )
    assert result.returncode == 0, result.stderr

    linked_enrollment = task_authority.load_project_enrollment(linked)

    assert linked_enrollment is not None
    assert linked_enrollment.identity == primary.identity
    assert linked_enrollment.pointer_path == repo / ".git" / task_authority.ENROLLMENT_POINTER_NAME
    assert linked_enrollment.binding_path == primary.binding_path
    _loaded, _executable, child = task_authority.manual_launch_environment(
        linked, "codex", {"PATH": "/usr/bin"}
    )
    assert child["BEADS_DIR"] == str(repo / ".beads")
    with pytest.raises(task_authority.TaskAuthorityError, match="alternate project authority"):
        task_authority.manual_launch_environment(
            linked,
            "codex",
            {"PATH": "/usr/bin", "BEADS_DIR": str(linked / ".beads")},
        )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("BEADS_DIR", "/tmp/alternate-beads"),
        ("GC_DOLT_HOST", "127.0.0.2"),
        ("GC_DOLT_PORT", "33070"),
        ("GC_DOLT_USER", "root"),
        ("GC_DOLT_DATABASE", "other_beads"),
        ("BEADS_DOLT_SERVER_HOST", "127.0.0.2"),
        ("BEADS_DOLT_SERVER_PORT", "33070"),
        ("BEADS_DOLT_SERVER_USER", "root"),
        ("BEADS_DOLT_SERVER_DATABASE", "other_beads"),
    ],
)
def test_manual_launcher_rejects_alternate_beads_directory_and_endpoints(
    tmp_path: Path,
    name: str,
    value: str,
) -> None:
    repo, _city, _enrollment = _provision(tmp_path)

    with pytest.raises(task_authority.TaskAuthorityError, match="alternate project authority"):
        task_authority.manual_launch_environment(
            repo,
            "codex",
            {"PATH": "/usr/bin", name: value},
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("backend", "sqlite"),
        ("database", "sqlite"),
        ("dolt_database", "other_beads"),
        ("dolt_mode", "embedded"),
        ("project_id", "../../another-project"),
        ("unexpected", True),
    ],
)
def test_enrollment_rejects_noncanonical_primary_beads_metadata(
    tmp_path: Path,
    field: str,
    replacement: object,
) -> None:
    repo, _city, _enrollment = _provision(tmp_path)
    metadata_path = repo / ".beads" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata[field] = replacement
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata_path.chmod(0o600)

    with pytest.raises(
        task_authority.TaskAuthorityError,
        match="primary repository Beads metadata",
    ):
        task_authority.load_project_enrollment(repo)


def test_enrollment_rejects_noncanonical_primary_beads_config(tmp_path: Path) -> None:
    repo, _city, _enrollment = _provision(tmp_path)
    config = repo / ".beads" / "config.yaml"
    config.write_bytes(task_authority._BEADS_CANONICAL_CONFIG + b"custom: drift\n")
    config.chmod(0o600)

    with pytest.raises(
        task_authority.TaskAuthorityError,
        match="primary repository Beads config",
    ):
        task_authority.load_project_enrollment(repo)


@pytest.mark.parametrize("failure", ["mode", "hardlink", "symlink", "directory-mode"])
def test_enrollment_rejects_unsafe_primary_beads_metadata(
    tmp_path: Path,
    failure: str,
) -> None:
    repo, _city, _enrollment = _provision(tmp_path)
    beads_dir = repo / ".beads"
    metadata_path = beads_dir / "metadata.json"
    if failure == "mode":
        metadata_path.chmod(0o644)
    elif failure == "hardlink":
        os.link(metadata_path, beads_dir / "metadata-hardlink.json")
    elif failure == "symlink":
        content = metadata_path.read_bytes()
        metadata_path.unlink()
        target = beads_dir / "metadata-target.json"
        target.write_bytes(content)
        target.chmod(0o600)
        metadata_path.symlink_to(target.name)
    else:
        beads_dir.chmod(0o755)

    with pytest.raises(task_authority.TaskAuthorityError):
        task_authority.load_project_enrollment(repo)


@pytest.mark.parametrize("retained_kind", ["file", "symlink"])
def test_enrollment_rejects_retained_beads_environment_file(
    tmp_path: Path,
    retained_kind: str,
) -> None:
    repo, _city, _enrollment = _provision(tmp_path)
    retained = repo / ".beads" / ".env"
    if retained_kind == "file":
        retained.write_text("BEADS_DOLT_PASSWORD=must-not-persist\n", encoding="utf-8")
        retained.chmod(0o600)
    else:
        retained.symlink_to("metadata.json")

    with pytest.raises(task_authority.TaskAuthorityError, match=r"\.beads/\.env"):
        task_authority.load_project_enrollment(repo)


@pytest.mark.parametrize("failure", ["mode", "hardlink", "symlink", "owner"])
def test_enrollment_pointer_rejects_alias_permissions_and_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    pointer = enrollment.pointer_path
    if failure == "mode":
        pointer.chmod(0o644)
    elif failure == "hardlink":
        os.link(pointer, pointer.with_name("pointer-hardlink"))
    elif failure == "symlink":
        content = pointer.read_bytes()
        pointer.unlink()
        target = pointer.with_name("pointer-target")
        target.write_bytes(content)
        target.chmod(0o600)
        pointer.symlink_to(target)
    else:
        monkeypatch.setattr(task_authority, "_current_uid", lambda: os.geteuid() + 1)

    with pytest.raises(task_authority.TaskAuthorityError):
        task_authority.load_project_enrollment(repo)


@pytest.mark.parametrize("failure", ["mode", "hardlink", "symlink"])
def test_external_binding_rejects_alias_and_permission_failures(
    tmp_path: Path, failure: str
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    binding = enrollment.binding_path
    if failure == "mode":
        binding.chmod(0o644)
    elif failure == "hardlink":
        os.link(binding, binding.with_name("binding-hardlink"))
    else:
        content = binding.read_bytes()
        binding.unlink()
        target = binding.with_name("binding-target")
        target.write_bytes(content)
        target.chmod(0o600)
        binding.symlink_to(target)

    with pytest.raises(task_authority.TaskAuthorityError):
        task_authority.load_project_enrollment(repo)


def test_enrollment_and_secret_readers_reject_toctou_and_owner_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    real_fstat = task_authority.os.fstat
    pointer_inode = enrollment.pointer_path.stat().st_ino
    seen = 0

    def raced_fstat(descriptor: int):
        nonlocal seen
        value = real_fstat(descriptor)
        if value.st_ino != pointer_inode:
            return value
        seen += 1
        if seen < 2:
            return value
        return SimpleNamespace(
            st_dev=value.st_dev,
            st_ino=value.st_ino,
            st_size=value.st_size,
            st_mtime_ns=value.st_mtime_ns + 1,
            st_mode=value.st_mode,
            st_uid=value.st_uid,
            st_nlink=value.st_nlink,
        )

    monkeypatch.setattr(task_authority.os, "fstat", raced_fstat)
    with pytest.raises(task_authority.TaskAuthorityError, match="changed while"):
        task_authority.load_project_enrollment(repo)

    monkeypatch.setattr(task_authority.os, "fstat", real_fstat)
    monkeypatch.setattr(task_authority, "_current_uid", lambda: os.geteuid() + 1)
    with pytest.raises(task_authority.TaskAuthorityError, match="owned by the current user"):
        task_authority._read_application_password(enrollment.password_file)


def test_manual_launch_is_secret_quiet_and_locks_models_and_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    captured: dict[str, object] = {}

    def fake_execve(path: Path, argv: list[str], env: dict[str, str]) -> None:
        captured.update(path=path, argv=argv, env=env)
        raise RuntimeError("exec boundary")

    monkeypatch.setattr(task_authority.os, "execve", fake_execve)
    with pytest.raises(RuntimeError, match="exec boundary"):
        task_authority.exec_manual_provider(repo, "codex", ["--help"], {"PATH": "/usr/bin"})

    secret = "CorrectHorseBatteryStaple-12345678"
    argv = captured["argv"]
    child = captured["env"]
    assert isinstance(argv, list) and isinstance(child, dict)
    assert captured["path"] == task_authority.MANUAL_BOUNDARY_EXECUTABLE
    taskmaster = str(repo / ".taskmaster")
    assert argv[:6] == [
        str(task_authority.MANUAL_BOUNDARY_EXECUTABLE),
        "--die-with-parent",
        "--bind",
        "/",
        "/",
        "--ro-bind",
    ]
    assert argv[6:8] == [taskmaster, taskmaster]
    separator = argv.index("--")
    assert argv[separator + 1 : separator + 5] == [
        str(enrollment.codex_executable),
        "--strict-config",
        "--model",
        "gpt-5.6-sol",
    ]
    assert 'model_reasoning_effort="xhigh"' in argv
    assert "workspace-write" in argv and "on-request" in argv
    assert secret not in "\0".join(argv)
    assert child["BEADS_DOLT_PASSWORD"] == secret
    assert child["GC_DOLT_PASSWORD"] == secret
    assert "BEADS_DOLT_PASSWORD_FILE" not in child
    assert child["BEADS_ACTOR"] == "manual-codex"
    assert child["PATH"].startswith(str(enrollment.city_root / "bin"))
    captured_output = capsys.readouterr()
    assert secret not in captured_output.out + captured_output.err

    claude_args = task_authority._manual_provider_arguments("claude", [], enrollment)
    assert claude_args[:2] == ["--model", "claude-fable-5"]
    assert str(enrollment.claude_config) in claude_args


def test_source_controlled_launcher_executes_pinned_cli_without_secret_output(
    tmp_path: Path,
) -> None:
    repo, city, _enrollment = _provision(tmp_path)
    city_bin = _private(city / "bin")
    for name in ("with-aegis-authority", "aegis-claude", "aegis-codex", "task-master"):
        shutil.copy2(ROOT / "deploy" / "gas-city" / "bin" / name, city_bin / name)
        (city_bin / name).chmod(0o755)
    runtime = city / "runtime" / "authority" / "task-authority.py"
    lock = {
        "task_authority_runtime": {
            "sha256": hashlib.sha256(runtime.read_bytes()).hexdigest()
        }
    }
    lock_path = city / "runtime-lock.json"
    lock_path.write_text(json.dumps(lock) + "\n", encoding="utf-8")
    lock_path.chmod(0o600)

    result = _run([str(city_bin / "aegis-codex"), "--help"], repo, env={"PATH": "/usr/bin"})
    assert result.returncode == 0, result.stderr
    assert result.stdout == "codex\n"
    assert "CorrectHorseBatteryStaple" not in result.stdout + result.stderr

    override = _run(
        [str(city_bin / "aegis-claude"), "--model", "wrong"],
        repo,
        env={"PATH": "/usr/bin"},
    )
    assert override.returncode != 0
    assert "override locked settings" in override.stderr
    assert "CorrectHorseBatteryStaple" not in override.stdout + override.stderr


def test_manual_namespace_makes_taskmaster_kernel_read_only(tmp_path: Path) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    before = tasks.read_bytes()
    _boundary, argv = task_authority._manual_boundary_arguments(
        enrollment,
        Path("/bin/sh"),
        ["-c", f"printf tampered > {tasks}"],
    )

    result = _run(argv, repo, env={"PATH": "/usr/bin:/bin"})

    assert result.returncode != 0
    assert "Read-only file system" in result.stderr
    assert tasks.read_bytes() == before


@pytest.mark.parametrize(
    ("provider", "arguments"),
    [
        ("codex", ["--model", "other"]),
        ("codex", ["-c", "model_reasoning_effort=low"]),
        ("claude", ["--fallback-model=other"]),
        ("claude", ["--dangerously-skip-permissions"]),
    ],
)
def test_manual_launch_rejects_provider_overrides(
    tmp_path: Path, provider: str, arguments: list[str]
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    with pytest.raises(task_authority.TaskAuthorityError, match="override locked settings"):
        task_authority._manual_provider_arguments(provider, arguments, enrollment)
    with pytest.raises(task_authority.TaskAuthorityError, match="auth/model boundary overrides"):
        task_authority.manual_launch_environment(
            repo, provider, {"PATH": "/usr/bin", "OPENAI_API_KEY": "must-not-use"}
        )


@pytest.mark.parametrize("failure", ["mode", "hardlink", "symlink"])
def test_manual_launch_rejects_unsafe_password_file(tmp_path: Path, failure: str) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    password = enrollment.password_file
    if failure == "mode":
        password.chmod(0o644)
    elif failure == "hardlink":
        os.link(password, password.with_name("password-hardlink"))
    else:
        content = password.read_bytes()
        password.unlink()
        target = password.with_name("password-target")
        target.write_bytes(content)
        target.chmod(0o600)
        password.symlink_to(target)

    with pytest.raises(task_authority.TaskAuthorityError):
        task_authority.manual_launch_environment(repo, "claude", {"PATH": "/usr/bin"})


def test_rollback_deactivation_is_fail_closed_and_idempotent_after_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _city, enrollment = _provision(tmp_path)
    receipt = task_authority.load_authority_receipt(
        enrollment.authority_receipt,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
    )
    task_authority.transition_authority(
        enrollment.authority_receipt,
        target_mode=task_authority.TaskAuthorityMode.TASKMASTER,
        expected_generation=2,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=receipt.evidence,
        activated_at="2026-07-15T20:03:00Z",
    )
    with pytest.raises(task_authority.TaskAuthorityError, match="generation-2"):
        task_authority.validate_project_authority_environment(
            repo, enrollment.expected_environment()
        )

    real_fsync = task_authority.os.fsync
    monkeypatch.setattr(
        task_authority.os,
        "fsync",
        lambda _descriptor: (_ for _ in ()).throw(OSError("simulated directory fsync failure")),
    )
    with pytest.raises(task_authority.TaskAuthorityError, match="atomically deactivate"):
        task_authority.deactivate_project_enrollment_after_rollback(repo)
    assert not enrollment.pointer_path.exists()
    monkeypatch.setattr(task_authority.os, "fsync", real_fsync)

    archive = task_authority.deactivate_project_enrollment_after_rollback(repo)
    assert archive.is_file()
    assert task_authority.deactivate_project_enrollment_after_rollback(repo) == archive
    assert task_authority.validate_project_authority_environment(repo, {}) is None


def test_enrolled_unwrapped_readiness_gate_and_numeric_kickoff_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _city, _enrollment = _provision(tmp_path)
    package = repo / "aegis_foundation"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(Path(task_authority.__file__), package / "task_authority.py")

    result = _run(["bash", str(READINESS), "--quick", "--root", str(repo)], repo)
    assert result.returncode == 2
    assert "complete authority environment" in result.stdout

    payload = json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": str(repo / "new.txt")}}
    )
    gate = subprocess.run(
        ["bash", str(PRETOOL)],
        cwd=repo,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)},
        check=False,
    )
    assert gate.returncode == 2
    assert "explicit task authority could not be validated" in gate.stderr.lower()

    with pytest.raises(installer.AegisError, match="invalid project task authority"):
        installer.kickoff(repo, task_id="1", slug="legacy", title="Legacy kickoff")


def test_codex_task_generate_one_refuses_enrolled_taskmaster_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = ROOT / "scripts" / "codex-task"
    loader = importlib.machinery.SourceFileLoader("_manual_authority_codex_task", str(script))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    monkeypatch.setattr(
        module._task_authority,
        "validate_project_authority_environment",
        lambda _root, _environment: object(),
    )

    with pytest.raises(module.TaskError, match="authoritative Beads enrollment"):
        module.handle_taskmaster_generate_one(argparse.Namespace(task_id="1", dry_run=True))
