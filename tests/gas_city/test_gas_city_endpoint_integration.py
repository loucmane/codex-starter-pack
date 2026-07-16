from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import stat
import subprocess
import tempfile
import time
from unittest import mock

import pytest

from aegis_foundation import gas_city_endpoint


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
ARTIFACTS = DEPLOY / "artifacts"
PASSWORD = "EndpointRehearsalPassword0123456789ABCDEF"


def _write(path: Path, content: str | bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    path.chmod(mode)


def _port_is_free(port: int) -> bool:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _start_dolt(data: Path, port: int, *, environment: dict[str, str]) -> subprocess.Popen[str]:
    data.mkdir(mode=0o700)
    server_environment = dict(environment)
    for key in ("BEADS_DOLT_PASSWORD", "DOLT_CLI_PASSWORD", "GC_DOLT_PASSWORD"):
        server_environment.pop(key, None)
    server = subprocess.Popen(
        [
            (ARTIFACTS / "dolt").as_posix(),
            "sql-server",
            "--data-dir",
            data.as_posix(),
            "-H",
            "127.0.0.1",
            "-P",
            str(port),
        ],
        env=server_environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    client = [
        (ARTIFACTS / "dolt").as_posix(),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-tls",
        "sql",
        "-q",
        "SELECT 1;",
    ]
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        ready = subprocess.run(
            client,
            env=server_environment,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if ready.returncode == 0:
            return server
        if server.poll() is not None:
            break
        time.sleep(0.1)
    stderr = server.stderr.read() if server.stderr is not None else ""
    server.terminate()
    server.wait(timeout=5)
    pytest.fail(f"temporary Dolt server on {port} did not start: {stderr[-2000:]}")


def _bootstrap_database(
    port: int,
    *,
    database: str,
    user: str,
    environment: dict[str, str],
) -> None:
    sql = (
        f"CREATE DATABASE IF NOT EXISTS `{database}`;\n"
        f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{PASSWORD}';\n"
        f"ALTER USER '{user}'@'%' IDENTIFIED BY '{PASSWORD}';\n"
        f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{user}'@'%';\n"
        f"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{PASSWORD}';\n"
        f"ALTER USER '{user}'@'localhost' IDENTIFIED BY '{PASSWORD}';\n"
        f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{user}'@'localhost';\n"
        "FLUSH PRIVILEGES;\n"
    )
    root_environment = dict(environment)
    for key in ("BEADS_DOLT_PASSWORD", "DOLT_CLI_PASSWORD", "GC_DOLT_PASSWORD"):
        root_environment.pop(key, None)
    result = subprocess.run(
        [
            (ARTIFACTS / "dolt").as_posix(),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-tls",
            "sql",
        ],
        env=root_environment,
        input=sql,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    application_environment = dict(root_environment)
    application_environment["DOLT_CLI_PASSWORD"] = PASSWORD
    proof = subprocess.run(
        [
            (ARTIFACTS / "dolt").as_posix(),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--user",
            user,
            "--use-db",
            database,
            "--no-tls",
            "sql",
            "-q",
            "SELECT 1;",
        ],
        env=application_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proof.returncode == 0, proof.stderr


def _init_beads(
    repo: Path,
    *,
    port: int,
    user: str,
    database: str,
    prefix: str,
    environment: dict[str, str],
) -> None:
    subprocess.run(["git", "init", "-q", repo.as_posix()], check=True)
    subprocess.run(
        ["git", "-C", repo.as_posix(), "config", "user.name", "Endpoint Rehearsal"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", repo.as_posix(), "config", "user.email", "endpoint@example.invalid"],
        check=True,
    )
    result = subprocess.run(
        [
            (ARTIFACTS / "bd").as_posix(),
            "init",
            "--server",
            "--external",
            "--server-host",
            "127.0.0.1",
            "--server-port",
            str(port),
            "--server-user",
            user,
            "--database",
            database,
            "--prefix",
            prefix,
            "--skip-agents",
            "--skip-hooks",
            "--non-interactive",
        ],
        cwd=repo,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith("runtime/evidence/"):
            continue
        result[relative] = (
            stat.S_IMODE(path.stat().st_mode),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return result


@pytest.mark.skipif(
    os.environ.get("AEGIS_RUN_GAS_CITY_ENDPOINT_INTEGRATION") != "1",
    reason="opt-in real pinned endpoint rehearsal",
)
def test_real_pinned_endpoint_transition_idempotence_and_rollback(tmp_path: Path) -> None:
    """Exercise real gc 1.3.5, bd 1.1.0, and Dolt 2.2.0 in /tmp only."""

    if not _port_is_free(33070) or not _port_is_free(33071):
        pytest.skip("production endpoint ports are already in use")
    del tmp_path
    scratch = Path(tempfile.mkdtemp(prefix="gas-city-endpoint-rehearsal-", dir="/tmp"))
    city = scratch / "gas-city"
    aegis = scratch / "aegis"
    home = scratch / "home"
    for directory in (scratch, city, aegis, home, city / "bin", city / ".gc"):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)

    helper_root = scratch / "bundle-helper"
    helper_root.mkdir(mode=0o700)
    provision_helpers = runpy.run_path(
        (ROOT / "tests" / "gas_city" / "test_provision_control_plane.py").as_posix()
    )
    bundle = provision_helpers["_bundle"](
        helper_root, site_aegis_root=aegis
    )

    for name in ("gc", "bd", "dolt"):
        shutil.copyfile(bundle / "artifacts" / name, city / "bin" / name)
        (city / "bin" / name).chmod(0o500)
    shutil.copyfile(bundle / "runtime-lock.json", city / "runtime-lock.json")
    (city / "runtime-lock.json").chmod(0o600)
    locked = json.loads((city / "runtime-lock.json").read_text())

    base_environment = {
        **os.environ,
        "HOME": home.as_posix(),
        "PATH": f"{city / 'bin'}:/usr/bin:/bin",
        "BEADS_DOLT_PASSWORD": PASSWORD,
        "DOLT_CLI_PASSWORD": PASSWORD,
        "GC_DOLT_PASSWORD": PASSWORD,
        "BD_NON_INTERACTIVE": "1",
        "BD_ACTOR": "endpoint-rehearsal",
    }
    servers: list[subprocess.Popen[str]] = []
    try:
        hq_server = _start_dolt(
            scratch / "hq-data", 33070, environment=base_environment
        )
        servers.append(hq_server)
        aegis_server = _start_dolt(
            scratch / "aegis-data", 33071, environment=base_environment
        )
        servers.append(aegis_server)
        _bootstrap_database(
            33070,
            database="hq",
            user="gas_city_hq",
            environment=base_environment,
        )
        _bootstrap_database(
            33071,
            database="aegis_beads",
            user="aegis_beads",
            environment=base_environment,
        )
        _init_beads(
            city,
            port=33070,
            user="gas_city_hq",
            database="hq",
            prefix="gc",
            environment=base_environment,
        )
        _init_beads(
            aegis,
            port=33071,
            user="aegis_beads",
            database="aegis_beads",
            prefix="ags",
            environment=base_environment,
        )
        city.chmod(0o700)
        aegis.chmod(0o700)

        _write(
            city / "city.toml",
            (
                "[workspace]\nname = \"gas-city\"\n\n"
                "[dolt]\nhost = \"127.0.0.1\"\nport = 3311\n\n"
                "[[rigs]]\nname = \"aegis\"\nprefix = \"ags\"\n"
                "dolt_host = \"127.0.0.1\"\ndolt_port = \"33071\"\n"
            ),
            0o600,
        )
        _write(
            city / ".gc" / "site.toml",
            f'workspace_name = "gas-city"\n\n[[rig]]\nname = "aegis"\npath = "{aegis}"\n',
        )
        hq_config = (city / ".beads" / "config.yaml").read_text()
        retained = "\n".join(
            line
            for line in hq_config.splitlines()
            if not line.startswith(
                (
                    "dolt.host:",
                    "dolt.port:",
                    "dolt.user:",
                    "gc.endpoint_origin:",
                    "gc.endpoint_status:",
                    "dolt.auto-start:",
                )
            )
        )
        _write(
            city / ".beads" / "config.yaml",
            retained
            + "\ndolt.auto-start: false\n"
            + "gc.endpoint_origin: managed_city\n"
            + "gc.endpoint_status: verified\n",
        )
        _write(city / ".beads" / "dolt-server.port", "3311\n", 0o640)

        aegis_config = (aegis / ".beads" / "config.yaml").read_text()
        retained = "\n".join(
            line
            for line in aegis_config.splitlines()
            if not line.startswith(
                (
                    "dolt.host:",
                    "dolt.port:",
                    "dolt.user:",
                    "gc.endpoint_origin:",
                    "gc.endpoint_status:",
                    "dolt.auto-start:",
                )
            )
        )
        _write(
            aegis / ".beads" / "config.yaml",
            retained
            + "\ndolt.auto-start: false\n"
            + "gc.endpoint_origin: explicit\n"
            + "gc.endpoint_status: verified\n"
            + "dolt.host: 127.0.0.1\n"
            + 'dolt.port: "33071"\n'
            + "dolt.user: aegis_beads\n",
        )
        _write(aegis / ".beads" / "dolt-server.port", "33071\n", 0o640)

        # Match the production stopped-state preflight.  Pinned gc materializes
        # its embedded provider script on the first supervisor inspection; the
        # endpoint receipt intentionally treats that verified runtime asset as
        # part of the pre-transition state.
        stopped = subprocess.run(
            [
                (city / "bin" / "gc").as_posix(),
                "--city",
                city.as_posix(),
                "supervisor",
                "status",
                "--json",
            ],
            cwd=city,
            env=base_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert stopped.returncode == 0, stopped.stderr
        assert json.loads(stopped.stdout)["running"] is False

        before_city = _fingerprint(city)
        before_aegis = _fingerprint(aegis)
        transaction = scratch / "provision-transaction"
        prepared = subprocess.run(
            [
                (bundle / "bin" / "provision-control-plane").as_posix(),
                "prepare",
                "--source-root",
                bundle.as_posix(),
                "--city-root",
                city.as_posix(),
                "--transaction-dir",
                transaction.as_posix(),
            ],
            cwd=bundle,
            env=base_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert prepared.returncode == 0, prepared.stderr
        assert json.loads(prepared.stdout)["status"] == "staged"
        provision_helpers["_mark_images_promoted"](city)
        activated = subprocess.run(
            [
                (bundle / "bin" / "provision-control-plane").as_posix(),
                "activate-topology",
                "--source-root",
                bundle.as_posix(),
                "--city-root",
                city.as_posix(),
                "--transaction-dir",
                transaction.as_posix(),
            ],
            cwd=bundle,
            env=base_environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert activated.returncode == 0, activated.stderr
        assert json.loads(activated.stdout) == {
            "activation_receipt": (
                transaction / "activation-receipt.json"
            ).as_posix(),
            "next_required_action": "transition-hq-endpoint",
            "status": "verified",
        }
        locked = json.loads((city / "runtime-lock.json").read_text())
        transition_root = (
            city / "runtime" / "evidence" / "endpoint-transition" / "real-v1.3.5"
        )
        transition = gas_city_endpoint.transition_hq_endpoint(
            city,
            city / "runtime-lock.json",
            transition_root,
            password=PASSWORD,
            environment=base_environment,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
            now=dt.datetime(2026, 7, 16, 2, 0, tzinfo=dt.timezone.utc),
        )
        after_first_city = _fingerprint(city)
        after_first_aegis = _fingerprint(aegis)
        repeated = gas_city_endpoint.transition_hq_endpoint(
            city,
            city / "runtime-lock.json",
            transition_root,
            password=PASSWORD,
            environment=base_environment,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )
        assert transition["action"] == "transitioned"
        assert repeated["action"] == "none"
        assert _fingerprint(city) == after_first_city
        assert _fingerprint(aegis) == after_first_aegis

        provisioner = runpy.run_path(
            (bundle / "bin" / "provision-control-plane").as_posix()
        )

        def verify_isolated_endpoint(
            current_city: Path,
            receipt: Path | None,
            topology_action: str,
        ) -> dict[str, object] | None:
            assert topology_action == "requires_hq_external_transition"
            assert receipt is not None
            proof = gas_city_endpoint.verify_hq_endpoint_transition(
                current_city,
                current_city / "runtime-lock.json",
                receipt,
                environment=base_environment,
                expected_city_root=city,
                expected_aegis_root=aegis,
                lock_loader=lambda _: locked,
            )
            return {
                "result": proof,
                "command": {
                    "argv": ["isolated-direct-endpoint-verifier"],
                    "cwd": current_city.as_posix(),
                    "returncode": 0,
                    "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                    "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                },
            }

        provisioner["finalize"].__globals__["_validate_endpoint_with_admin"] = (
            verify_isolated_endpoint
        )
        with mock.patch.dict(os.environ, base_environment, clear=True):
            finalized = provisioner["finalize"](
                bundle,
                city,
                transaction,
                Path(transition["receipt_path"]),
            )
        assert finalized["status"] == "verified"
        assert _fingerprint(city) == after_first_city
        with mock.patch.dict(os.environ, base_environment, clear=True):
            repeated_finalize = provisioner["finalize"](
                bundle,
                city,
                transaction,
                Path(transition["receipt_path"]),
            )
        assert repeated_finalize["status"] == "already-finalized"
        assert _fingerprint(city) == after_first_city

        rollback_root = (
            city / "runtime" / "evidence" / "endpoint-rollback" / "real-v1.3.5"
        )
        rollback = gas_city_endpoint.rollback_hq_endpoint(
            city,
            city / "runtime-lock.json",
            Path(transition["receipt_path"]),
            rollback_root,
            environment=base_environment,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
            now=dt.datetime(2026, 7, 16, 2, 1, tzinfo=dt.timezone.utc),
        )
        after_rollback_city = _fingerprint(city)
        after_rollback_aegis = _fingerprint(aegis)
        rollback_repeat = gas_city_endpoint.rollback_hq_endpoint(
            city,
            city / "runtime-lock.json",
            Path(transition["receipt_path"]),
            rollback_root,
            environment=base_environment,
            expected_city_root=city,
            expected_aegis_root=aegis,
            lock_loader=lambda _: locked,
        )
        assert rollback["action"] == "rolled-back"
        assert rollback_repeat["action"] == "none"
        assert after_rollback_city != before_city
        assert after_rollback_aegis == before_aegis

        with mock.patch.dict(os.environ, base_environment, clear=True):
            control_rollback = provisioner["rollback"](
                bundle,
                city,
                transaction,
                Path(rollback["receipt_path"]),
            )
        assert control_rollback["status"] == "restored"
        with mock.patch.dict(os.environ, base_environment, clear=True):
            repeated_control_rollback = provisioner["rollback"](
                bundle,
                city,
                transaction,
                Path(rollback["receipt_path"]),
            )
        assert repeated_control_rollback["status"] == "already-restored"
        assert _fingerprint(city) == before_city
        assert _fingerprint(aegis) == before_aegis
        receipt_text = Path(transition["receipt_path"]).read_text()
        assert PASSWORD not in receipt_text
        assert json.loads(receipt_text)["tools"]["gc"]["version"] == "1.3.5"
    finally:
        for server in reversed(servers):
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
        if os.environ.get("AEGIS_KEEP_GAS_CITY_ENDPOINT_REHEARSAL") != "1":
            shutil.rmtree(scratch, ignore_errors=True)
        else:
            print(f"kept endpoint rehearsal at {scratch}")
