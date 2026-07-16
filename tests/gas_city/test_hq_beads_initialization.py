from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

import pytest

from aegis_foundation import gas_city_endpoint


PASSWORD = "hq-initialization-password-0123456789abcdef"


def _write(path: Path, content: str | bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    path.chmod(mode)


class HQInitializationRunner:
    def __init__(self, city: Path, *, schema_state: str = "virgin") -> None:
        self.city = city
        self.schema_state = schema_state
        self.init_count = 0
        self.custom_types_registered = False
        self.schema_migrations = 0
        self.schema_migrations_applied = False
        self.calls: list[tuple[tuple[str, ...], dict[str, str]]] = []

    def __call__(
        self, argv: tuple[str, ...], cwd: Path, environment: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        command = tuple(argv)
        env = dict(environment)
        self.calls.append((command, env))
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
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
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
                ),
                "",
            )
        if executable == "dolt" and "--query" in command:
            assert env["DOLT_CLI_PASSWORD"] == PASSWORD
            query = command[command.index("--query") + 1]
            if "INSERT INTO config" in query and "types.custom" in query:
                self.custom_types_registered = True
                return subprocess.CompletedProcess(command, 0, json.dumps({}), "")
            payload = (
                {}
                if self.schema_state == "virgin"
                and "information_schema.tables" in query
                else {"rows": self._rows(query)}
            )
            return subprocess.CompletedProcess(
                command, 0, json.dumps(payload), ""
            )
        if executable == "bd" and command == gas_city_endpoint._hq_initialization_argv(
            self.city
        ):
            assert cwd == self.city
            assert env["BEADS_DOLT_PASSWORD"] == PASSWORD
            assert env["BD_BACKUP_ENABLED"] == "false"
            assert all(PASSWORD not in value for value in command)
            self.init_count += 1
            self.schema_state = "initialized"
            beads = self.city / ".beads"
            (beads / "dolt").mkdir(mode=0o700)
            _write(beads / ".gitignore", b"pinned gitignore\n")
            _write(beads / ".local_version", b"1.1.0\n")
            _write(beads / "README.md", b"pinned readme\n")
            _write(beads / "interactions.jsonl", b"")
            _write(beads / "dolt-server.port", b"33070")
            _write(
                beads / "metadata.json",
                json.dumps(
                    {
                        "database": "dolt",
                        "backend": "dolt",
                        "dolt_mode": "server",
                        "dolt_server_host": "127.0.0.1",
                        "dolt_server_port": 33070,
                        "dolt_server_user": "gas_city_hq",
                        "dolt_database": "hq",
                        "project_id": "11111111-2222-3333-4444-555555555555",
                    }
                ),
            )
            return subprocess.CompletedProcess(command, 0, "", "")
        if executable == "bd" and command == gas_city_endpoint._hq_schema_migration_argv(
            self.city
        ):
            assert cwd == self.city
            assert env["BEADS_DOLT_PASSWORD"] == PASSWORD
            self.schema_migrations += 1
            self.schema_migrations_applied = True
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"status": "up-to-date"}), ""
            )
        raise AssertionError(f"unexpected command: {command}")

    def _rows(self, query: str) -> list[dict[str, object]]:
        if "information_schema.tables" in query:
            if self.schema_state == "virgin":
                return []
            schema = list(gas_city_endpoint.HQ_BEADS_SCHEMA)
            if self.schema_state == "partial":
                schema = schema[:8]
            if self.schema_state == "foreign":
                schema.append(("foreign_table", "BASE TABLE"))
            return [
                {"TABLE_NAME": name, "TABLE_TYPE": kind} for name, kind in schema
            ]
        if "FROM dolt_status" in query:
            return (
                []
                if self.schema_state == "virgin"
                else [{"TABLE_NAME": "config", "STATUS": "modified", "STAGED": "0"}]
            )
        if "FROM dolt_branches" in query:
            return [
                {
                    "branch_count": "1",
                    "main_branch_count": "1",
                    "commit_count": "1" if self.schema_state == "virgin" else "8",
                    "head": "a" * 32,
                }
            ]
        if "COUNT(*)" in query:
            result: dict[str, object] = {}
            for name in gas_city_endpoint.HQ_BEADS_CONTENT_TABLES:
                result[f"{name}_count"] = "0"
            for name, count in gas_city_endpoint.HQ_BEADS_SEEDED_ROW_COUNTS.items():
                if name == "config" and not self.custom_types_registered:
                    count -= 1
                if name == "custom_types" and not self.schema_migrations_applied:
                    count = 0
                result[f"{name}_count"] = str(
                    min(count, 1) if self.schema_state == "partial" else count
                )
            return [result]
        if "FROM config" in query and "types.custom" in query:
            rows = [{"key": "issue_prefix", "value": "gc"}]
            if self.custom_types_registered:
                rows.append(
                    {
                        "key": "types.custom",
                        "value": gas_city_endpoint.HQ_BEADS_CUSTOM_TYPES,
                    }
                )
            return rows
        raise AssertionError(f"unexpected SQL: {query}")


def _fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, dict[str, object], HQInitializationRunner]:
    city = tmp_path / "gas-city"
    aegis = tmp_path / "aegis"
    city.mkdir(mode=0o700)
    aegis.mkdir(mode=0o700)
    for directory in (
        city / "bin",
        city / ".gc",
        city / ".beads",
        aegis / ".beads",
    ):
        directory.mkdir(parents=True, mode=0o700)
    (city / ".beads").chmod(0o700)
    (aegis / ".beads").chmod(0o700)

    tool_records: dict[str, object] = {}
    for name, version in {"gc": "1.3.5", "bd": "1.1.0", "dolt": "2.2.0"}.items():
        content = f"fake pinned {name} {version}\n".encode()
        _write(city / "bin" / name, content, 0o500)
        tool_records[name] = {
            "version": version,
            "binary_sha256": hashlib.sha256(content).hexdigest(),
        }
    lock = city / "runtime-lock.json"
    _write(lock, b"{}\n")
    locked: dict[str, object] = {"tools": tool_records}
    _write(
        city / "city.toml",
        (
            '[workspace]\nname = "gas-city"\n\n'
            '[dolt]\nhost = "127.0.0.1"\nport = 33070\n\n'
            '[[rigs]]\nname = "aegis"\nprefix = "ags"\n'
            'dolt_host = "127.0.0.1"\ndolt_port = "33071"\n'
        ),
        0o640,
    )
    _write(
        city / ".gc" / "site.toml",
        f'workspace_name = "gas-city"\n\n[[rig]]\nname = "aegis"\npath = "{aegis}"\n',
    )
    _write(
        city / ".beads" / "config.yaml",
        gas_city_endpoint.HQ_BEADS_INITIAL_CONFIG,
    )
    _write(
        city / ".beads" / "metadata.json",
        json.dumps(
            {
                "backend": "dolt",
                "database": "dolt",
                "dolt_database": "hq",
                "dolt_mode": "server",
            }
        ),
    )
    _write(
        aegis / ".beads" / "config.yaml",
        (
            "issue_prefix: ags\nissue-prefix: ags\ndolt.auto-start: false\n"
            "gc.endpoint_origin: explicit\ngc.endpoint_status: verified\n"
            "dolt.host: 127.0.0.1\ndolt.port: 33071\ndolt.user: aegis_beads\n"
        ),
    )
    _write(
        aegis / ".beads" / "metadata.json",
        json.dumps(
            {
                "backend": "dolt",
                "database": "dolt",
                "dolt_database": "aegis_beads",
                "dolt_mode": "server",
            }
        ),
    )
    gitignore = b"pinned gitignore\n"
    readme = b"pinned readme\n"
    monkeypatch.setattr(
        gas_city_endpoint,
        "HQ_BEADS_GITIGNORE_SHA256",
        hashlib.sha256(gitignore).hexdigest(),
    )
    monkeypatch.setattr(
        gas_city_endpoint,
        "HQ_BEADS_README_SHA256",
        hashlib.sha256(readme).hexdigest(),
    )
    return city, aegis, lock, locked, HQInitializationRunner(city)


def _initialize(
    city: Path,
    aegis: Path,
    lock: Path,
    locked: dict[str, object],
    runner: HQInitializationRunner,
    *,
    hook=None,
) -> dict[str, object]:
    return gas_city_endpoint.initialize_hq_beads(
        city,
        lock,
        city / "runtime" / "evidence" / "beads-initialization" / "hq-test",
        password=PASSWORD,
        runner=runner,
        environment={
            "HOME": (city.parent / "home").as_posix(),
            "XDG_RUNTIME_DIR": (city.parent / "run-user").as_posix(),
        },
        expected_city_root=city,
        expected_aegis_root=aegis,
        lock_loader=lambda _path: locked,
        phase_hook=hook,
        now=dt.datetime(2026, 7, 16, 2, 3, 4, tzinfo=dt.timezone.utc),
    )


def test_hq_initialization_is_exact_secret_free_and_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path, monkeypatch)
    first = _initialize(city, aegis, lock, locked, runner)
    evidence = Path(first["receipt_path"]).parent
    before = {
        path.relative_to(evidence).as_posix(): path.read_bytes()
        for path in evidence.rglob("*")
        if path.is_file()
    }
    second = _initialize(city, aegis, lock, locked, runner)

    assert first["status"] == "verified"
    assert second["status"] == "already-initialized"
    assert first["project_id"] == "11111111-2222-3333-4444-555555555555"
    assert runner.init_count == 1
    assert before == {
        path.relative_to(evidence).as_posix(): path.read_bytes()
        for path in evidence.rglob("*")
        if path.is_file()
    }
    for path in evidence.rglob("*"):
        assert stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600)
        if path.is_file():
            assert PASSWORD.encode() not in path.read_bytes()


def test_hq_initialization_recovers_after_completed_command_before_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path, monkeypatch)

    def crash(phase: str) -> None:
        if phase == "after-init":
            raise RuntimeError("simulated process loss")

    with pytest.raises(RuntimeError, match="simulated process loss"):
        _initialize(city, aegis, lock, locked, runner, hook=crash)
    recovered = _initialize(city, aegis, lock, locked, runner)

    assert recovered["status"] == "verified"
    assert runner.init_count == 1


def test_hq_initialization_recovers_between_bd_init_and_custom_type_registration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path, monkeypatch)

    def crash(phase: str) -> None:
        if phase == "after-bd-init":
            raise RuntimeError("simulated post-bd process loss")

    with pytest.raises(RuntimeError, match="simulated post-bd process loss"):
        _initialize(city, aegis, lock, locked, runner, hook=crash)
    assert runner.custom_types_registered is False

    recovered = _initialize(city, aegis, lock, locked, runner)

    assert recovered["status"] == "verified"
    assert runner.init_count == 1
    assert runner.custom_types_registered is True
    assert (city / ".beads" / "config.yaml").read_bytes() == (
        gas_city_endpoint.HQ_BEADS_CONFIG
    )


def test_hq_initialization_resumes_known_partial_empty_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path, monkeypatch)

    def stop_prepared(phase: str) -> None:
        if phase == "prepared":
            raise RuntimeError("simulated prepared crash")

    with pytest.raises(RuntimeError, match="simulated prepared crash"):
        _initialize(city, aegis, lock, locked, runner, hook=stop_prepared)
    runner.schema_state = "partial"
    result = _initialize(city, aegis, lock, locked, runner)

    assert result["status"] == "verified"
    assert runner.init_count == 1


def test_hq_initialization_rejects_foreign_schema_before_bd_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    city, aegis, lock, locked, runner = _fixture(tmp_path, monkeypatch)
    runner.schema_state = "foreign"

    with pytest.raises(
        gas_city_endpoint.EndpointTransitionError,
        match="foreign table or view",
    ):
        _initialize(city, aegis, lock, locked, runner)

    assert runner.init_count == 0
