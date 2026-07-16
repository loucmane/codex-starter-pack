from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess

import pytest

from aegis_foundation import gas_city_endpoint


PASSWORD = "endpoint-test-password-0123456789abcdef"


def _write(path: Path, content: str | bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    path.chmod(mode)


def _managed_hq_config() -> str:
    return (
        "issue_prefix: gc\n"
        "issue-prefix: gc\n"
        "dolt.auto-start: false\n"
        "gc.endpoint_origin: managed_city\n"
        "gc.endpoint_status: verified\n"
    )


def _external_hq_config() -> str:
    return (
        "issue_prefix: gc\n"
        "issue-prefix: gc\n"
        "dolt.auto-start: false\n"
        "gc.endpoint_origin: city_canonical\n"
        "gc.endpoint_status: verified\n"
        "dolt.host: 127.0.0.1\n"
        "dolt.port: \"33070\"\n"
        "dolt.user: gas_city_hq\n"
    )


def _aegis_config() -> str:
    return (
        "issue_prefix: ags\n"
        "issue-prefix: ags\n"
        "dolt.auto-start: false\n"
        "gc.endpoint_origin: explicit\n"
        "gc.endpoint_status: verified\n"
        "dolt.host: 127.0.0.1\n"
        "dolt.port: \"33071\"\n"
        "dolt.user: aegis_beads\n"
    )


class EndpointRunner:
    def __init__(
        self,
        city: Path,
        *,
        mutate_dry_run: bool = False,
        apply_stdout: str = "UPDATED: city endpoint\n",
        kill_mid_apply: bool = False,
        kill_after_apply: bool = False,
    ) -> None:
        self.city = city
        self.mutate_dry_run = mutate_dry_run
        self.apply_stdout = apply_stdout
        self.kill_mid_apply = kill_mid_apply
        self.kill_after_apply = kill_after_apply
        self.calls: list[tuple[tuple[str, ...], Path, dict[str, str]]] = []
        self.apply_count = 0

    def __call__(
        self, argv: tuple[str, ...], cwd: Path, environment: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        command = tuple(argv)
        env = dict(environment)
        self.calls.append((command, cwd, env))
        executable = Path(command[0]).name
        if executable == "gc" and command[1:] == ("version",):
            return subprocess.CompletedProcess(command, 0, "gc version 1.3.5\n", "")
        if executable == "bd" and command[1:] == ("--version",):
            return subprocess.CompletedProcess(command, 0, "bd version 1.1.0\n", "")
        if executable == "dolt" and command[1:] == ("version",):
            return subprocess.CompletedProcess(command, 0, "dolt version 2.2.0\n", "")
        if command[1:] == (
            "--city",
            self.city.as_posix(),
            "supervisor",
            "status",
            "--json",
        ):
            runtime = Path(env.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
            home = Path(env["HOME"])
            payload = {
                "schema_version": "1",
                "ok": True,
                "checked_paths": [
                    (runtime / "gc" / "supervisor.sock").as_posix(),
                    (home / ".gc" / "supervisor.sock").as_posix(),
                ],
                "pid": 0,
                "running": False,
                "socket_path": "",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        transition = (
            "--city",
            self.city.as_posix(),
            "beads",
            "city",
            "use-external",
            "--host",
            "127.0.0.1",
            "--port",
            "33070",
            "--user",
            "gas_city_hq",
        )
        if command[1:] == (*transition, "--dry-run"):
            if self.mutate_dry_run:
                (self.city / "city.toml").write_text("[workspace]\nname='mutated'\n")
            return subprocess.CompletedProcess(
                command, 0, "WOULD UPDATE: city endpoint\n", ""
            )
        if command[1:] == transition:
            assert env["BEADS_DOLT_PASSWORD"] == PASSWORD
            assert env["DOLT_CLI_PASSWORD"] == PASSWORD
            assert env["GC_DOLT_PASSWORD"] == PASSWORD
            assert env["BD_BACKUP_ENABLED"] == "false"
            assert all(PASSWORD not in argument for argument in command)
            self.apply_count += 1
            _write(
                self.city / "city.toml",
                (
                    "[workspace]\nname = \"gas-city\"\n\n"
                    "[dolt]\nhost = \"127.0.0.1\"\nport = 33070\n\n"
                    "[[rigs]]\nname = \"aegis\"\nprefix = \"ags\"\n"
                    "dolt_host = \"127.0.0.1\"\ndolt_port = \"33071\"\n"
                ),
                0o600,
            )
            _write(self.city / ".beads" / "config.yaml", _external_hq_config())
            if self.kill_mid_apply:
                os.kill(os.getpid(), signal.SIGKILL)
            # Upstream canonicalization rewrites metadata formatting even when
            # the identity fields are unchanged.
            metadata = json.loads((self.city / ".beads" / "metadata.json").read_text())
            _write(
                self.city / ".beads" / "metadata.json",
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            )
            (self.city / ".beads" / "dolt-server.port").unlink(missing_ok=True)
            aegis = Path(json.loads((self.city / ".gc" / "test-state.json").read_text())["aegis"])
            (aegis / ".beads" / "dolt-server.port").unlink(missing_ok=True)
            _write(
                self.city
                / ".gc"
                / "runtime"
                / "packs"
                / "dolt"
                / "dolt-provider-state.json",
                '{"running":false,"pid":0,"started_at":"post-apply"}\n',
            )
            if self.kill_after_apply:
                os.kill(os.getpid(), signal.SIGKILL)
            return subprocess.CompletedProcess(command, 0, self.apply_stdout, "")
        proof_prefix = ("-C", self.city.as_posix(), "--readonly")
        if executable == "bd" and command[1:] == (*proof_prefix, "where", "--json"):
            assert env["BEADS_DIR"] == (self.city / ".beads").as_posix()
            assert env["BEADS_DOLT_SERVER_HOST"] == "127.0.0.1"
            assert env["BEADS_DOLT_SERVER_PORT"] == "33070"
            assert env["BEADS_DOLT_SERVER_USER"] == "gas_city_hq"
            assert env["BEADS_DOLT_SERVER_DATABASE"] == "hq"
            assert env["GC_DOLT_USER"] == "gas_city_hq"
            payload = {
                "schema_version": 1,
                "database_path": (self.city / ".beads" / "dolt").as_posix(),
                "path": (self.city / ".beads").as_posix(),
                "prefix": "gc",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        if executable == "bd" and command[1:] == (*proof_prefix, "dolt", "show", "--json"):
            payload = {
                "schema_version": 1,
                "backend": "dolt",
                "connection_ok": True,
                "database": "hq",
                "embedded": False,
                "host": "127.0.0.1",
                "port": 33070,
                "user": "gas_city_hq",
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        if executable == "bd" and command[1:] == (*proof_prefix, "dolt", "test", "--json"):
            payload = {
                "schema_version": 1,
                "connection_ok": True,
                "host": "127.0.0.1",
                "port": 33070,
            }
            return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")
        raise AssertionError(f"unexpected command: {command}")


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, object], EndpointRunner]:
    city = tmp_path / "gas-city"
    aegis = tmp_path / "aegis"
    city.mkdir(mode=0o700)
    aegis.mkdir(mode=0o700)
    for directory in (city / "bin", city / ".gc", city / ".beads", aegis / ".beads"):
        directory.mkdir(parents=True, mode=0o700)

    tool_records: dict[str, object] = {}
    versions = {"gc": "1.3.5", "bd": "1.1.0", "dolt": "2.2.0"}
    for name, version in versions.items():
        content = f"fake pinned {name} {version}\n".encode()
        _write(city / "bin" / name, content, 0o500)
        tool_records[name] = {
            "version": version,
            "binary_sha256": hashlib.sha256(content).hexdigest(),
        }
    lock = city / "runtime-lock.json"
    _write(lock, b"{}\n", 0o600)
    locked: dict[str, object] = {"tools": tool_records}

    _write(
        city / "city.toml",
        (
            "[workspace]\nname = \"gas-city\"\n\n"
            "[dolt]\nhost = \"127.0.0.1\"\nport = 3311\n\n"
            "[[rigs]]\nname = \"aegis\"\nprefix = \"ags\"\n"
            "dolt_host = \"127.0.0.1\"\ndolt_port = \"33071\"\n"
        ),
        0o640,
    )
    _write(
        city / ".gc" / "site.toml",
        f'workspace_name = "gas-city"\n\n[[rig]]\nname = "aegis"\npath = "{aegis}"\n',
    )
    _write(city / ".gc" / "test-state.json", json.dumps({"aegis": aegis.as_posix()}))
    _write(city / ".beads" / "config.yaml", _managed_hq_config())
    _write(
        city / ".beads" / "metadata.json",
        '{"database":"dolt","backend":"dolt","dolt_mode":"server","dolt_database":"hq","project_id":"11111111-2222-3333-4444-555555555555"}\n',
    )
    _write(city / ".beads" / "dolt-server.port", "3311\n", 0o640)
    _write(aegis / ".beads" / "config.yaml", _aegis_config())
    _write(
        aegis / ".beads" / "metadata.json",
        '{"database":"dolt","backend":"dolt","dolt_mode":"server","dolt_database":"aegis_beads"}\n',
    )
    _write(aegis / ".beads" / "dolt-server.port", "33071\n", 0o640)
    pack_runtime = city / ".gc" / "runtime" / "packs" / "dolt"
    _write(
        pack_runtime / "dolt-provider-state.json",
        '{"running":false,"pid":0,"started_at":"pre-transition"}\n',
    )
    _write(pack_runtime / "dolt.lock", b"")
    _write(pack_runtime / "dolt-config.yaml", "listener: stopped\n")
    _write(pack_runtime / "dolt.log", "stopped before transition\n")
    runner = EndpointRunner(city)
    return city, aegis, lock, locked, runner


def _transition(
    city: Path,
    aegis: Path,
    lock: Path,
    locked: dict[str, object],
    runner: EndpointRunner,
    *,
    name: str = "run-001",
) -> dict[str, object]:
    return gas_city_endpoint.transition_hq_endpoint(
        city,
        lock,
        city / "runtime" / "evidence" / "endpoint-transition" / name,
        password=PASSWORD,
        runner=runner,
        environment={
            "PATH": "/untrusted",
            "HOME": (city.parent / "home").as_posix(),
            "XDG_RUNTIME_DIR": (city.parent / "run-user").as_posix(),
            "GC_DOLT_DATABASE": "wrong",
            "BEADS_CREDENTIALS_FILE": "/untrusted/credentials",
        },
        expected_city_root=city,
        expected_aegis_root=aegis,
        lock_loader=lambda _: locked,
        now=dt.datetime(2026, 7, 16, 1, 2, 3, tzinfo=dt.timezone.utc),
    )


def _tree_bytes(root: Path) -> dict[str, tuple[bytes, int]]:
    result: dict[str, tuple[bytes, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(root).as_posix()] = (
                path.read_bytes(),
                stat.S_IMODE(path.stat().st_mode),
            )
    return result


def _tracked_bytes(city: Path, aegis: Path) -> dict[str, tuple[bool, bytes, int]]:
    paths = {
        "city_toml": city / "city.toml",
        "site_toml": city / ".gc" / "site.toml",
        "hq_config": city / ".beads" / "config.yaml",
        "hq_metadata": city / ".beads" / "metadata.json",
        "hq_port": city / ".beads" / "dolt-server.port",
        "hq_managed_state": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-state.json",
        "hq_provider_state": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-provider-state.json",
        "hq_provider_pid": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.pid",
        "hq_provider_lock": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.lock",
        "hq_provider_config": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-config.yaml",
        "hq_provider_log": city / ".gc" / "runtime" / "packs" / "dolt" / "dolt.log",
        "hq_provider_script": city / ".gc" / "scripts" / "gc-beads-bd.sh",
        "aegis_config": aegis / ".beads" / "config.yaml",
        "aegis_metadata": aegis / ".beads" / "metadata.json",
        "aegis_port": aegis / ".beads" / "dolt-server.port",
    }
    result: dict[str, tuple[bool, bytes, int]] = {}
    for role, path in paths.items():
        if path.exists():
            result[role] = (
                True,
                path.read_bytes(),
                stat.S_IMODE(path.stat().st_mode),
            )
        else:
            result[role] = (False, b"", 0)
    return result


def test_transition_is_exact_private_secret_free_and_idempotent(tmp_path: Path) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    initial_aegis_config = (aegis / ".beads" / "config.yaml").read_bytes()
    initial_aegis_metadata = (aegis / ".beads" / "metadata.json").read_bytes()

    first = _transition(city, aegis, lock, locked, runner)
    evidence = Path(first["receipt_path"]).parent
    before_rerun = _tree_bytes(evidence)
    second = _transition(city, aegis, lock, locked, runner)

    assert first["status"] == "verified"
    assert first["action"] == "transitioned"
    assert second["status"] == "already-verified"
    assert second["action"] == "none"
    assert runner.apply_count == 1
    assert before_rerun == _tree_bytes(evidence)
    assert (aegis / ".beads" / "config.yaml").read_bytes() == initial_aegis_config
    assert (aegis / ".beads" / "metadata.json").read_bytes() == initial_aegis_metadata
    assert not (aegis / ".beads" / "dolt-server.port").exists()
    assert not (city / ".beads" / "dolt-server.port").exists()
    receipt = json.loads(Path(first["receipt_path"]).read_text())
    assert receipt["endpoint"] == {
        "database": "hq",
        "endpoint_origin": "city_canonical",
        "endpoint_status": "verified",
        "host": "127.0.0.1",
        "port": 33070,
        "user": "gas_city_hq",
    }
    for path in evidence.rglob("*"):
        if path.is_dir():
            assert stat.S_IMODE(path.stat().st_mode) == 0o700
        else:
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            assert PASSWORD.encode() not in path.read_bytes()
    for argv, _, env in runner.calls:
        assert all(PASSWORD not in argument for argument in argv)
        if Path(argv[0]).name == "gc" and "version" not in argv:
            assert env.get("GC_DOLT_DATABASE") is None
            assert env.get("BEADS_CREDENTIALS_FILE", "").startswith("/proc/")
            assert env.get("BEADS_CREDENTIALS_FILE") != "/untrusted/credentials"


def test_transition_receipt_reverification_binds_current_stopped_tree(
    tmp_path: Path,
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    transition = _transition(city, aegis, lock, locked, runner)
    environment = {
        "HOME": (city.parent / "home").as_posix(),
        "XDG_RUNTIME_DIR": (city.parent / "run-user").as_posix(),
    }
    verified = gas_city_endpoint.verify_hq_endpoint_transition(
        city,
        lock,
        Path(transition["receipt_path"]),
        runner=runner,
        environment=environment,
        expected_city_root=city,
        expected_aegis_root=aegis,
        lock_loader=lambda _: locked,
    )
    assert verified["status"] == "verified"
    assert verified["transition_receipt_sha256"] == hashlib.sha256(
        Path(transition["receipt_path"]).read_bytes()
    ).hexdigest()

    _write(city / "city.toml", "[workspace]\nname='tampered'\n", 0o600)
    with pytest.raises(
        gas_city_endpoint.EndpointTransitionError,
        match="sole configured rig|no longer matches",
    ):
        gas_city_endpoint.verify_hq_endpoint_transition(
            city,
            lock,
            Path(transition["receipt_path"]),
            runner=runner,
            environment=environment,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )


def test_dry_run_mutation_is_rejected_before_evidence_or_apply(tmp_path: Path) -> None:
    city, aegis, lock, locked, _ = _fixture(tmp_path)
    runner = EndpointRunner(city, mutate_dry_run=True)
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="dry-run mutated"):
        _transition(city, aegis, lock, locked, runner)
    assert runner.apply_count == 0
    assert not (city / "runtime").exists()


def test_post_apply_validation_failure_restores_every_tracked_byte(tmp_path: Path) -> None:
    city, aegis, lock, locked, _ = _fixture(tmp_path)
    before = _tracked_bytes(city, aegis)
    runner = EndpointRunner(city, apply_stdout="unexpected success output\n")
    with pytest.raises(
        gas_city_endpoint.EndpointTransitionError,
        match="did not confirm",
    ):
        _transition(city, aegis, lock, locked, runner, name="failed-apply")
    assert _tracked_bytes(city, aegis) == before
    failure = json.loads(
        (
            city
            / "runtime"
            / "evidence"
            / "endpoint-transition"
            / "failed-apply"
            / "failure.json"
        ).read_text()
    )
    assert failure["automatic_rollback"] == "verified"


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires POSIX process semantics")
def test_mid_command_kill_resumes_by_restoring_anchored_prestate(tmp_path: Path) -> None:
    city, aegis, lock, locked, _ = _fixture(tmp_path)
    before = _tracked_bytes(city, aegis)
    child = os.fork()
    if child == 0:
        crashing_runner = EndpointRunner(city, kill_mid_apply=True)
        _transition(
            city,
            aegis,
            lock,
            locked,
            crashing_runner,
            name="killed-apply",
        )
        os._exit(97)
    _, status = os.waitpid(child, 0)
    assert os.WIFSIGNALED(status)
    assert os.WTERMSIG(status) == signal.SIGKILL

    evidence = (
        city / "runtime" / "evidence" / "endpoint-transition" / "killed-apply"
    )
    assert (evidence / "prepared.json").is_file()
    assert not (evidence / "transition-receipt.json").exists()
    assert _tracked_bytes(city, aegis) != before

    recovery_runner = EndpointRunner(city)
    recovered = _transition(
        city,
        aegis,
        lock,
        locked,
        recovery_runner,
        name="killed-apply",
    )
    repeated = _transition(
        city,
        aegis,
        lock,
        locked,
        recovery_runner,
        name="killed-apply",
    )
    assert recovered["status"] == "recovered"
    assert recovered["action"] == "restored-pre-transition"
    assert repeated["status"] == "already-recovered"
    assert _tracked_bytes(city, aegis) == before


def test_wrong_lock_tool_symlink_and_concurrency_fail_closed(tmp_path: Path) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    other_lock = city / "other-lock.json"
    _write(other_lock, b"{}\n")
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="exact city runtime"):
        gas_city_endpoint.transition_hq_endpoint(
            city,
            other_lock,
            city / "runtime" / "evidence" / "endpoint-transition" / "wrong-lock",
            password=PASSWORD,
            runner=runner,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )

    (city / "bin" / "gc").chmod(0o700)
    (city / "bin" / "gc").write_text("same version, different binary\n")
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="runtime-lock digest"):
        _transition(city, aegis, lock, locked, runner, name="wrong-tool")
    _write(city / "bin" / "gc", b"fake pinned gc 1.3.5\n", 0o500)

    config = city / ".beads" / "config.yaml"
    outside = tmp_path / "outside.yaml"
    _write(outside, _managed_hq_config())
    config.unlink()
    config.symlink_to(outside)
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="symlink"):
        _transition(city, aegis, lock, locked, runner, name="symlink")
    config.unlink()
    _write(config, _managed_hq_config())

    descriptor = os.open(lock, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="in progress"):
            _transition(city, aegis, lock, locked, runner, name="concurrent")
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def test_rollback_restores_exact_bytes_modes_and_is_idempotent(tmp_path: Path) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    tracked = {
        "city": (city / "city.toml").read_bytes(),
        "city_mode": stat.S_IMODE((city / "city.toml").stat().st_mode),
        "hq_config": (city / ".beads" / "config.yaml").read_bytes(),
        "hq_metadata": (city / ".beads" / "metadata.json").read_bytes(),
        "hq_port": (city / ".beads" / "dolt-server.port").read_bytes(),
        "hq_port_mode": stat.S_IMODE((city / ".beads" / "dolt-server.port").stat().st_mode),
        "aegis_port": (aegis / ".beads" / "dolt-server.port").read_bytes(),
        "provider_state": (
            city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-provider-state.json"
        ).read_bytes(),
    }
    transition = _transition(city, aegis, lock, locked, runner)
    rollback_root = city / "runtime" / "evidence" / "endpoint-rollback" / "rollback-001"
    kwargs = dict(
        runner=runner,
        environment={
            "HOME": (city.parent / "home").as_posix(),
            "XDG_RUNTIME_DIR": (city.parent / "run-user").as_posix(),
            "GC_DOLT_PASSWORD": "must-be-cleared",
        },
        expected_city_root=city,
        expected_aegis_root=aegis,
        lock_loader=lambda _: locked,
        now=dt.datetime(2026, 7, 16, 1, 3, 4, tzinfo=dt.timezone.utc),
    )
    first = gas_city_endpoint.rollback_hq_endpoint(
        city,
        lock,
        Path(transition["receipt_path"]),
        rollback_root,
        **kwargs,
    )
    before_rerun = _tree_bytes(rollback_root)
    second = gas_city_endpoint.rollback_hq_endpoint(
        city,
        lock,
        Path(transition["receipt_path"]),
        rollback_root,
        **kwargs,
    )
    assert first["action"] == "rolled-back"
    assert second["action"] == "none"
    assert before_rerun == _tree_bytes(rollback_root)
    assert (city / "city.toml").read_bytes() == tracked["city"]
    assert stat.S_IMODE((city / "city.toml").stat().st_mode) == tracked["city_mode"]
    assert (city / ".beads" / "config.yaml").read_bytes() == tracked["hq_config"]
    assert (city / ".beads" / "metadata.json").read_bytes() == tracked["hq_metadata"]
    assert (city / ".beads" / "dolt-server.port").read_bytes() == tracked["hq_port"]
    assert stat.S_IMODE((city / ".beads" / "dolt-server.port").stat().st_mode) == tracked["hq_port_mode"]
    assert (aegis / ".beads" / "dolt-server.port").read_bytes() == tracked["aegis_port"]
    assert (
        city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-provider-state.json"
    ).read_bytes() == tracked["provider_state"]
    assert not (city / ".gc" / "runtime" / "packs" / "dolt" / "dolt-state.json").exists()


def test_rollback_rejects_post_state_and_snapshot_tamper(tmp_path: Path) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    transition = _transition(city, aegis, lock, locked, runner)
    receipt = Path(transition["receipt_path"])
    (city / ".beads" / "config.yaml").write_text(_external_hq_config() + "custom: drift\n")
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="post-state"):
        gas_city_endpoint.rollback_hq_endpoint(
            city,
            lock,
            receipt,
            city / "runtime" / "evidence" / "endpoint-rollback" / "drift",
            runner=runner,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )

    # Restore the verified post bytes, then corrupt an immutable before payload.
    after_manifest = json.loads((receipt.parent / "after" / "manifest.json").read_text())
    entry = next(item for item in after_manifest["entries"] if item["role"] == "hq_config")
    (city / ".beads" / "config.yaml").write_bytes(
        (receipt.parent / entry["payload"]).read_bytes()
    )
    before_manifest = json.loads((receipt.parent / "before" / "manifest.json").read_text())
    before_entry = next(item for item in before_manifest["entries"] if item["role"] == "hq_config")
    payload = receipt.parent / before_entry["payload"]
    payload.chmod(0o600)
    payload.write_bytes(b"tampered\n")
    with pytest.raises(gas_city_endpoint.EndpointTransitionError, match="payload digest"):
        gas_city_endpoint.rollback_hq_endpoint(
            city,
            lock,
            receipt,
            city / "runtime" / "evidence" / "endpoint-rollback" / "tamper",
            runner=runner,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )


def test_rollback_resumes_an_exact_mixed_tree_after_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path)
    before = _tracked_bytes(city, aegis)
    transition = _transition(city, aegis, lock, locked, runner)
    rollback_root = (
        city / "runtime" / "evidence" / "endpoint-rollback" / "crash-resume"
    )
    original_restore = gas_city_endpoint._restore_manifest

    def partial_restore(
        before_manifest: dict[str, object],
        after_manifest: dict[str, object],
        *,
        evidence_root: Path,
    ) -> None:
        before_entries = {
            entry["role"]: entry for entry in before_manifest["entries"]  # type: ignore[index]
        }
        after_entries = {
            entry["role"]: entry for entry in after_manifest["entries"]  # type: ignore[index]
        }
        for role in (
            "aegis_metadata",
            "aegis_config",
            "aegis_port",
            "site_toml",
            "city_toml",
            "hq_metadata",
        ):
            gas_city_endpoint._restore_entry(
                before_entries[role],
                after_entries[role],
                evidence_root=evidence_root,
            )
        raise KeyboardInterrupt("simulated power loss during rollback")

    kwargs = dict(
        runner=runner,
        expected_city_root=city,
        expected_aegis_root=aegis,
        lock_loader=lambda _: locked,
    )
    monkeypatch.setattr(gas_city_endpoint, "_restore_manifest", partial_restore)
    with pytest.raises(KeyboardInterrupt, match="simulated power loss"):
        gas_city_endpoint.rollback_hq_endpoint(
            city,
            lock,
            Path(transition["receipt_path"]),
            rollback_root,
            **kwargs,
        )
    assert (rollback_root / "prepared.json").is_file()
    assert _tracked_bytes(city, aegis) != before

    monkeypatch.setattr(gas_city_endpoint, "_restore_manifest", original_restore)
    resumed = gas_city_endpoint.rollback_hq_endpoint(
        city,
        lock,
        Path(transition["receipt_path"]),
        rollback_root,
        **kwargs,
    )
    assert resumed["action"] == "rolled-back"
    assert _tracked_bytes(city, aegis) == before


def test_cli_exposes_only_guarded_endpoint_commands() -> None:
    script = (Path(__file__).parents[2] / "scripts" / "gas-city-admin").read_text()
    assert 'commands.add_parser("initialize-hq-beads")' in script
    assert 'commands.add_parser("endpoint-transition-hq")' in script
    assert 'commands.add_parser("endpoint-rollback-hq")' in script
    assert "GAS_CITY_HQ_DOLT_PASSWORD_FILE" not in script
    assert "--adopt-unverified" not in script
