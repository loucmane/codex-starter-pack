from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

import pytest

from aegis_foundation import gas_city_ops


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY = REPO_ROOT / "deploy" / "gas-city"
BD = (DEPLOY / "artifacts" / "bd").resolve()
DOLT = (DEPLOY / "artifacts" / "dolt").resolve()
GIT = Path("/usr/bin/git")
PASSWORD = "correct-horse-battery-staple-1234"
PROJECT_ID = "12345678-1234-4123-8123-123456789abc"


def _run(*argv: str, cwd: Path, environment: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "aegis"
    repository.mkdir()
    _run("git", "init", "--quiet", "--initial-branch=main", cwd=repository)
    _run("git", "config", "user.name", "Gas City Test", cwd=repository)
    _run("git", "config", "user.email", "gas-city@example.invalid", cwd=repository)
    (repository / "tracked.txt").write_text("tracked baseline\n")
    _run("git", "add", "tracked.txt", cwd=repository)
    _run("git", "commit", "--quiet", "-m", "baseline", cwd=repository)
    return repository.resolve()


def _dirty_repository(repository: Path) -> dict[str, bytes]:
    (repository / "tracked.txt").write_text("dirty tracked work\n")
    (repository / "untracked.txt").write_text("untracked user work\n")
    return {
        "tracked.txt": (repository / "tracked.txt").read_bytes(),
        "untracked.txt": (repository / "untracked.txt").read_bytes(),
    }


def _lock(tmp_path: Path) -> Path:
    path = tmp_path / "city" / "runtime-lock.json"
    path.parent.mkdir(parents=True)
    path.write_bytes((DEPLOY / "runtime-lock.json").read_bytes())
    path.chmod(0o600)
    manifest = path.parent / "control-plane-manifest.json"
    manifest.write_bytes((DEPLOY / "control-plane-manifest.json").read_bytes())
    manifest.chmod(0o600)
    return path.resolve()


class FakeExternalDolt:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []
        self.contaminated = False
        self.fail_export = False
        self.wrong_metadata = False
        self.create_env = False
        self.metadata_symlink = False
        self.echo_password = False
        self.wrong_bd_version = False
        self.active_config = False
        self.runtime_config_seeded = False
        self.schema_migrations = 0

    def __call__(self, argv, cwd, environment):
        command = tuple(argv)
        captured_environment = dict(environment)
        self.calls.append((command, captured_environment))
        executable = Path(command[0]).name
        if executable == "git":
            assert PASSWORD not in captured_environment.values()
            return subprocess.run(
                command,
                cwd=cwd,
                env=captured_environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        if executable == "bd" and command[1:] == ("--version",):
            assert PASSWORD not in captured_environment.values()
            version = (
                "bd version 1.1.1 (fffffffff)"
                if self.wrong_bd_version
                else "bd version 1.1.0 (8e4e59d39)"
            )
            return subprocess.CompletedProcess(command, 0, version + "\n", "")
        if executable == "dolt" and command[1:] == ("version",):
            assert PASSWORD not in captured_environment.values()
            return subprocess.CompletedProcess(command, 0, "dolt version 2.2.0\n", "")
        if executable == "bd" and command[1:] == ("metrics", "off", "--quiet"):
            assert PASSWORD not in captured_environment.values()
            return subprocess.CompletedProcess(command, 0, "metrics disabled\n", "")
        assert captured_environment["BEADS_DOLT_PASSWORD"] == PASSWORD
        assert captured_environment["DOLT_CLI_PASSWORD"] == PASSWORD
        assert captured_environment["BD_BACKUP_ENABLED"] == "false"
        assert Path(captured_environment["HOME"]).is_relative_to(Path(cwd).anchor)
        if executable == "bd" and "init" in command:
            staging = Path(cwd)
            beads = staging / ".beads"
            beads.mkdir(mode=0o700)
            (beads / "config.yaml").write_text(
                "# Beads Configuration File\n# Secret keys must use environment variables\n"
                + ("no-db: true\n" if self.active_config else "")
            )
            (beads / ".local_version").write_text("1.1.0\n")
            (beads / "dolt-server.port").write_text("33071")
            (beads / ".gitignore").write_text("dolt/\n")
            (beads / "README.md").write_text("Beads metadata\n")
            (beads / "interactions.jsonl").write_text("")
            metadata = {
                "backend": "dolt",
                "database": "dolt",
                "dolt_database": "aegis_beads",
                "dolt_mode": "server",
                "dolt_server_host": "127.0.0.1",
                "dolt_server_port": 33072 if self.wrong_metadata else 33071,
                "dolt_server_user": "aegis_beads",
                "project_id": PROJECT_ID,
            }
            metadata_path = beads / "metadata.json"
            if self.metadata_symlink:
                outside = staging / "outside-metadata.json"
                outside.write_text(json.dumps(metadata))
                metadata_path.symlink_to(outside)
            else:
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
            if self.create_env:
                (beads / ".env").write_text("BEADS_DOLT_PASSWORD=forbidden\n")
            exclude = staging / ".git" / "info" / "exclude"
            exclude.write_bytes(gas_city_ops._exclude_after_bytes(exclude.read_bytes()))
            output = PASSWORD if self.echo_password else ""
            return subprocess.CompletedProcess(command, 0, output, "")
        if executable == "bd" and command == gas_city_ops._aegis_schema_migration_argv(
            BD, Path(cwd)
        ):
            self.schema_migrations += 1
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"status": "up-to-date"}), ""
            )
        if executable == "bd" and "export" in command:
            if self.fail_export:
                return subprocess.CompletedProcess(command, 9, "", "simulated export failure")
            output = '{"id":"ags-contamination"}\n' if self.contaminated else ""
            return subprocess.CompletedProcess(command, 0, output, "")
        if executable == "dolt" and "--query" in command:
            query = command[command.index("--query") + 1]
            if "INSERT INTO config" in query and "types.custom" in query:
                self.runtime_config_seeded = True
                output = {}
            elif "FROM config" in query and "types.custom" in query:
                output = {
                    "rows": (
                        [
                            {"key": "issue_prefix", "value": "ags"},
                            {
                                "key": "types.custom",
                                "value": gas_city_ops.GAS_CITY_REQUIRED_CUSTOM_TYPES,
                            },
                        ]
                        if self.runtime_config_seeded
                        else []
                    )
                }
            elif "HASHOF" in query:
                output = {"rows": [{"head": "a" * 32}]}
            else:
                output = {
                    "rows": [
                        {
                            "issue_count": 0,
                            "working_set_changes": 1,
                            "expected_config_changes": 1,
                            "unexpected_working_changes": 0,
                            "branch_count": 1,
                            "main_branch_count": 1,
                            "commit_count": 4,
                        }
                    ]
                }
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        raise AssertionError(f"unexpected command: {command}")


def _initialize(
    repository: Path,
    lock: Path,
    runner: FakeExternalDolt,
    *,
    phase_hook=None,
):
    return gas_city_ops.initialize_aegis_beads(
        repository,
        lock,
        bd_binary=BD,
        dolt_binary=DOLT,
        git_binary=GIT,
        password=PASSWORD,
        runner=runner,
        phase_hook=phase_hook,
        now=dt.datetime(2026, 7, 15, 22, 30, tzinfo=dt.timezone.utc),
    )


def _repo_state(repository: Path) -> tuple[str, str, bytes, bytes]:
    return (
        _run("git", "rev-parse", "HEAD", cwd=repository).strip(),
        _run(
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            cwd=repository,
        ),
        (repository / "tracked.txt").read_bytes(),
        (repository / "untracked.txt").read_bytes()
        if (repository / "untracked.txt").exists()
        else b"",
    )


def test_clean_initialization_is_private_exact_and_pre_migration_idempotent(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    expected_work = _dirty_repository(repository)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    before = _repo_state(repository)

    first = _initialize(repository, lock, runner)
    after = _repo_state(repository)
    second = _initialize(repository, lock, runner)

    assert first["action"] == "initialized"
    assert second["action"] == "already-initialized"
    assert before == after == _repo_state(repository)
    assert (repository / "tracked.txt").read_bytes() == expected_work["tracked.txt"]
    assert (repository / "untracked.txt").read_bytes() == expected_work["untracked.txt"]
    beads = repository / ".beads"
    assert stat.S_IMODE(beads.stat().st_mode) == 0o700
    assert stat.S_IMODE((beads / "metadata.json").stat().st_mode) == 0o600
    assert not (beads / ".env").exists()
    assert not (beads / "backup").exists()
    metadata = json.loads((beads / "metadata.json").read_text())
    assert metadata == {
        "backend": "dolt",
        "database": "dolt",
        "dolt_database": "aegis_beads",
        "dolt_mode": "server",
        "project_id": PROJECT_ID,
    }
    assert (beads / "config.yaml").read_bytes() == gas_city_ops.AEGIS_BEADS_CANONICAL_CONFIG
    assert not (beads / "dolt-server.port").exists()
    exclude = (repository / ".git" / "info" / "exclude").read_bytes()
    assert exclude.count(gas_city_ops.AEGIS_BEADS_STEALTH_EXCLUDE_BLOCK) == 1
    evidence = Path(first["evidence_directory"])
    assert evidence.is_relative_to(lock.parent)
    assert stat.S_IMODE(evidence.stat().st_mode) == 0o700
    assert {path.name for path in evidence.iterdir()} == {
        "intent.json",
        "beads-tree.json",
        "prepared.json",
        "publish.json",
        "manifest.json",
    }
    for path in evidence.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert PASSWORD.encode() not in path.read_bytes()
    manifest = json.loads((evidence / "manifest.json").read_text())
    assert manifest["credential_transport"] == "owner-only-environment-file"
    assert manifest["runtime_lock_sha256"] == hashlib.sha256(lock.read_bytes()).hexdigest()
    assert runner.schema_migrations == 1
    for argv, _ in runner.calls:
        assert all(PASSWORD not in argument for argument in argv)


class SimulatedCrash(BaseException):
    pass


@pytest.mark.parametrize(
    "phase",
    ["prepared", "published", "excluded", "publish-evidence", "manifest"],
)
def test_crash_at_every_publication_boundary_repairs_idempotently(
    tmp_path: Path,
    phase: str,
) -> None:
    repository = _repository(tmp_path)
    _dirty_repository(repository)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    before = _repo_state(repository)

    def crash(observed: str) -> None:
        if observed == phase:
            raise SimulatedCrash

    with pytest.raises(SimulatedCrash):
        _initialize(repository, lock, runner, phase_hook=crash)
    result = _initialize(repository, lock, runner)

    assert result["action"] == "crash-repaired"
    assert _repo_state(repository) == before
    pointer = json.loads(
        (repository / ".git" / gas_city_ops.AEGIS_BEADS_INIT_POINTER_NAME).read_text()
    )
    assert pointer["status"] == "complete"
    assert hashlib.sha256(
        (Path(result["evidence_directory"]) / "manifest.json").read_bytes()
    ).hexdigest() == pointer["final_manifest_sha256"]


def test_failure_before_publish_leaves_work_and_primary_store_untouched(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    _dirty_repository(repository)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    runner.fail_export = True
    before = _repo_state(repository)

    with pytest.raises(gas_city_ops.GasCityOpsError, match="command failed"):
        _initialize(repository, lock, runner)

    assert not (repository / ".beads").exists()
    assert not (
        repository / ".git" / gas_city_ops.AEGIS_BEADS_INIT_POINTER_NAME
    ).exists()
    assert _repo_state(repository) == before
    failures = list(
        (lock.parent / "runtime" / "evidence" / "beads-initialization").glob(
            "*/failure.json"
        )
    )
    assert len(failures) == 1
    assert PASSWORD.encode() not in failures[0].read_bytes()


@pytest.mark.parametrize(
    ("attribute", "message"),
    [
        ("contaminated", "contaminated"),
        ("wrong_metadata", "metadata"),
        ("create_env", "must not retain"),
        ("metadata_symlink", "symlink"),
        ("echo_password", "echoed"),
        ("wrong_bd_version", "exact bd 1.1.0"),
        ("active_config", "unexpected active setting"),
    ],
)
def test_initialization_rejects_contamination_metadata_env_symlink_and_output_leakage(
    tmp_path: Path,
    attribute: str,
    message: str,
) -> None:
    repository = _repository(tmp_path)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    setattr(runner, attribute, True)

    with pytest.raises(gas_city_ops.GasCityOpsError, match=message):
        _initialize(repository, lock, runner)

    assert not (repository / ".beads").exists()


def test_preexisting_store_wrong_modes_and_binary_symlink_fail_closed(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    drifted = tmp_path / "bd-drifted"
    drifted.write_bytes(BD.read_bytes() + b"drift")
    drifted.chmod(0o700)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="digest mismatch"):
        gas_city_ops.initialize_aegis_beads(
            repository,
            lock,
            bd_binary=drifted,
            dolt_binary=DOLT,
            password=PASSWORD,
            runner=runner,
        )

    (repository / ".beads").mkdir()
    with pytest.raises(gas_city_ops.GasCityOpsError, match="no guarded initialization proof"):
        _initialize(repository, lock, runner)
    (repository / ".beads").rmdir()

    initialized = _initialize(repository, lock, runner)
    assert initialized["status"] == "pass"
    (repository / ".beads" / "metadata.json").chmod(0o666)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="mode 0600"):
        _initialize(repository, lock, runner)

    link = tmp_path / "bd-link"
    link.symlink_to(BD)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="non-symlink"):
        gas_city_ops.initialize_aegis_beads(
            repository,
            lock,
            bd_binary=link,
            dolt_binary=DOLT,
            password=PASSWORD,
            runner=runner,
        )


def test_linked_worktree_and_stealth_hidden_user_work_are_rejected(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    lock = _lock(tmp_path)
    runner = FakeExternalDolt()
    worktree = tmp_path / "linked"
    _run("git", "worktree", "add", "--quiet", "-b", "linked", str(worktree), cwd=repository)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="primary checkout"):
        _initialize(worktree.resolve(), lock, runner)

    (repository / "private.db").write_text("user database\n")
    with pytest.raises(gas_city_ops.GasCityOpsError, match="would hide"):
        _initialize(repository, lock, runner)


def test_target_password_file_must_be_owner_only_real_and_singly_linked(
    tmp_path: Path,
) -> None:
    secret = tmp_path / "target-password"
    secret.write_text(PASSWORD + "\n")
    secret.chmod(0o600)
    environment = {"GAS_CITY_TARGET_DOLT_PASSWORD_FILE": secret.as_posix()}
    assert (
        gas_city_ops.read_private_secret_file_from_environment(
            environment, "GAS_CITY_TARGET_DOLT_PASSWORD_FILE"
        )
        == PASSWORD
    )

    link = tmp_path / "target-password-link"
    link.symlink_to(secret)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="non-symlink"):
        gas_city_ops.read_private_secret_file_from_environment(
            {"GAS_CITY_TARGET_DOLT_PASSWORD_FILE": link.as_posix()},
            "GAS_CITY_TARGET_DOLT_PASSWORD_FILE",
        )

    hardlink = tmp_path / "target-password-hardlink"
    os.link(secret, hardlink)
    with pytest.raises(gas_city_ops.GasCityOpsError, match="singly linked"):
        gas_city_ops.read_private_secret_file_from_environment(
            environment, "GAS_CITY_TARGET_DOLT_PASSWORD_FILE"
        )
