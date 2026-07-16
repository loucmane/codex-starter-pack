from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time

import pytest


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
BD = DEPLOY / "artifacts" / "bd"
DOLT = DEPLOY / "artifacts" / "dolt"


def _tree_fingerprint(root: Path) -> list[tuple[str, int, str]]:
    return [
        (
            path.relative_to(root).as_posix(),
            path.stat().st_mode & 0o777,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


@pytest.mark.skipif(
    os.environ.get("AEGIS_RUN_BD_READONLY_INTEGRATION") != "1",
    reason="opt-in loopback integration proof",
)
def test_real_bd_external_write_read_leaves_read_only_beads_tree_unchanged() -> None:
    """Prove Beads 1.1 writes only external Dolt when local metadata is immutable."""

    # Force a Linux filesystem even when desktop TEMP points at /mnt/c.
    scratch = Path(tempfile.mkdtemp(prefix="aegis-bd-readonly-", dir="/tmp"))
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    data = scratch / "dolt-data"
    repo = scratch / "repo"
    data.mkdir()
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Aegis Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "aegis@example.invalid"],
        check=True,
    )
    server = subprocess.Popen(
        [
            str(DOLT),
            "sql-server",
            "--data-dir",
            str(data),
            "-H",
            "127.0.0.1",
            "-P",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    client = [str(DOLT), "--host", "127.0.0.1", "--port", str(port), "--no-tls", "sql"]
    environment = {
        **os.environ,
        "BD_NON_INTERACTIVE": "1",
        "BEADS_DOLT_PASSWORD": "",
        "BD_ACTOR": "aegis-test",
    }
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            ready = subprocess.run(
                [*client, "-q", "SELECT 1;"],
                text=True,
                capture_output=True,
                check=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.1)
        else:
            stderr = server.stderr.read() if server.stderr is not None else ""
            pytest.fail(f"temporary Dolt server did not start: {stderr}")
        subprocess.run([*client, "-q", "CREATE DATABASE aegis_beads;"], check=True)
        subprocess.run(
            [
                str(BD),
                "init",
                "--server",
                "--external",
                "--server-host",
                "127.0.0.1",
                "--server-port",
                str(port),
                "--server-user",
                "root",
                "--database",
                "aegis_beads",
                "--prefix",
                "ags",
                "--skip-agents",
                "--skip-hooks",
                "--non-interactive",
            ],
            cwd=repo,
            env=environment,
            check=True,
            text=True,
            capture_output=True,
        )
        beads = repo / ".beads"
        for path in sorted(beads.rglob("*"), reverse=True):
            path.chmod(0o444 if path.is_file() else 0o555)
        beads.chmod(0o555)
        assert not os.access(beads, os.W_OK)
        before = _tree_fingerprint(beads)

        created = subprocess.run(
            [str(BD), "--json", "create", "Read-only metadata proof"],
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        issue_id = __import__("json").loads(created.stdout)["id"]
        shown = subprocess.run(
            [str(BD), "--json", "show", issue_id],
            cwd=repo,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )

        assert issue_id in shown.stdout
        assert _tree_fingerprint(beads) == before
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        for path in sorted(scratch.rglob("*"), reverse=True):
            try:
                path.chmod(0o755 if path.is_dir() else 0o644)
            except FileNotFoundError:
                pass
        shutil.rmtree(scratch, ignore_errors=True)
