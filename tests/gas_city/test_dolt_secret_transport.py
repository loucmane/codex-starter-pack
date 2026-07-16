from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = ROOT / "deploy" / "gas-city" / "docker" / "dolt-entrypoint.sh"
ROOT_PASSWORD = "R" * 40 + "1"
APP_PASSWORD = "A" * 40 + "2"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o700)


def _fake_dolt(path: Path) -> None:
    _write_executable(
        path,
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time

args = sys.argv[1:]
with Path(os.environ["FAKE_DOLT_ARGV_LOG"]).open("a") as stream:
    stream.write(json.dumps(args, separators=(",", ":")) + "\\n")

if args and args[0] == "config":
    raise SystemExit(0)
if args and args[0] == "init":
    Path(".dolt").mkdir(exist_ok=True)
    raise SystemExit(0)
if args and args[0] == "sql-server":
    if any(item.endswith("dolt-bootstrap.yaml") for item in args):
        stopping = False

        def stop(_signum, _frame):
            global stopping
            stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        while not stopping:
            time.sleep(0.02)
    raise SystemExit(0)

if "sql" in args and "--query" not in args:
    target = os.readlink("/proc/self/fd/0")
    target_path = Path(target)
    evidence = {
        "stdin_target": target,
        "file_mode": stat.S_IMODE(target_path.stat().st_mode),
        "directory_mode": stat.S_IMODE(target_path.parent.stat().st_mode),
    }
    Path(os.environ["FAKE_DOLT_STDIN_TARGET_LOG"]).write_text(
        json.dumps(evidence, sort_keys=True) + "\\n"
    )
    Path(os.environ["FAKE_DOLT_SQL_LOG"]).write_text(sys.stdin.read())
    if os.environ.get("FAKE_DOLT_FAIL_BOOTSTRAP_SQL") == "1":
        raise SystemExit(42)

raise SystemExit(0)
""",
    )


def _run_entrypoint(tmp_path: Path, *, fail_bootstrap_sql: bool) -> tuple[
    subprocess.CompletedProcess[str], Path, Path, Path
]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _fake_dolt(fake_bin / "dolt")

    data_dir = tmp_path / "dolt-data"
    data_dir.mkdir(mode=0o700)
    root_password_file = tmp_path / "root-password"
    app_password_file = tmp_path / "app-password"
    root_password_file.write_text(ROOT_PASSWORD)
    app_password_file.write_text(APP_PASSWORD)
    root_password_file.chmod(0o600)
    app_password_file.chmod(0o600)

    argv_log = tmp_path / "argv.jsonl"
    sql_log = tmp_path / "bootstrap.sql"
    stdin_target_log = tmp_path / "stdin-target.json"
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "HOME": str(tmp_path / "home"),
        "DOLT_DATABASE": "aegis_beads",
        "DOLT_APP_USER": "aegis_beads",
        "DOLT_DATA_DIR": str(data_dir),
        "DOLT_ROOT_PASSWORD_FILE": str(root_password_file),
        "DOLT_APP_PASSWORD_FILE": str(app_password_file),
        "FAKE_DOLT_ARGV_LOG": str(argv_log),
        "FAKE_DOLT_SQL_LOG": str(sql_log),
        "FAKE_DOLT_STDIN_TARGET_LOG": str(stdin_target_log),
    }
    if fail_bootstrap_sql:
        environment["FAKE_DOLT_FAIL_BOOTSTRAP_SQL"] = "1"

    result = subprocess.run(
        ["bash", str(ENTRYPOINT)],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    return result, data_dir, argv_log, stdin_target_log


def _assert_secret_transport_evidence(
    *, tmp_path: Path, argv_log: Path, stdin_target_log: Path
) -> None:
    argv_text = argv_log.read_text()
    assert ROOT_PASSWORD not in argv_text
    assert APP_PASSWORD not in argv_text

    calls = [json.loads(line) for line in argv_text.splitlines()]
    bootstrap_calls = [
        call for call in calls if "sql" in call and "--query" not in call
    ]
    assert len(bootstrap_calls) == 1

    sql = (tmp_path / "bootstrap.sql").read_text()
    assert ROOT_PASSWORD in sql
    assert APP_PASSWORD in sql
    assert "ALTER USER 'root'@'localhost'" in sql
    assert "FLUSH PRIVILEGES;" in sql

    evidence = json.loads(stdin_target_log.read_text())
    stdin_target = Path(evidence["stdin_target"])
    assert str(stdin_target).startswith("/tmp/gas-city-dolt-bootstrap.")
    assert stdin_target.name == "bootstrap.sql"
    assert evidence["file_mode"] == stat.S_IRUSR | stat.S_IWUSR
    assert evidence["directory_mode"] == stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    assert not stdin_target.exists()
    assert not stdin_target.parent.exists()


def test_bootstrap_sql_secrets_travel_via_private_tmpfs_stdin_and_are_cleaned(
    tmp_path: Path,
) -> None:
    result, data_dir, argv_log, stdin_target_log = _run_entrypoint(
        tmp_path, fail_bootstrap_sql=False
    )

    assert result.returncode == 0, result.stderr
    assert ROOT_PASSWORD not in result.stdout + result.stderr
    assert APP_PASSWORD not in result.stdout + result.stderr
    _assert_secret_transport_evidence(
        tmp_path=tmp_path,
        argv_log=argv_log,
        stdin_target_log=stdin_target_log,
    )
    marker = data_dir / ".credentials-initialized"
    assert marker.is_file()
    assert stat.S_IMODE(marker.stat().st_mode) == stat.S_IRUSR | stat.S_IWUSR


def test_failed_bootstrap_sql_cleans_tmpfs_artifact_without_writing_marker(
    tmp_path: Path,
) -> None:
    result, data_dir, argv_log, stdin_target_log = _run_entrypoint(
        tmp_path, fail_bootstrap_sql=True
    )

    assert result.returncode == 42
    assert ROOT_PASSWORD not in result.stdout + result.stderr
    assert APP_PASSWORD not in result.stdout + result.stderr
    _assert_secret_transport_evidence(
        tmp_path=tmp_path,
        argv_log=argv_log,
        stdin_target_log=stdin_target_log,
    )
    assert not (data_dir / ".credentials-initialized").exists()
    assert not list(data_dir.glob(".credentials-initialized.*"))
