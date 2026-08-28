from __future__ import annotations

import json
import os
import pty
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/codex-gpg-readiness"
INSTALLER = ROOT / "scripts/install-codex-gpg-readiness"
SHELL_SNIPPET = ROOT / "scripts/shell/codex-gpg-readiness.zsh"
FINGERPRINT = "FD5585922F5335BC378AD8D42ECF4432C7E7982D"
KEYGRIP = "640406DD1B34A5EA0BB7CB46F21071BB3DB370FA"


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _fake_environment(
    tmp_path: Path,
    *,
    ready: bool,
    agent_available: bool = True,
    cache_after_sign: bool = True,
) -> tuple[dict[str, str], Path, Path]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log = tmp_path / "calls.log"
    state = tmp_path / "ready"
    if ready:
        state.touch()
    _write_executable(
        fake_bin / "gpg-connect-agent",
        f"""#!/bin/sh
printf '%s\\n' "$*" >>{log}
if [ "{str(agent_available).lower()}" != true ]; then
  exit 0
fi
case "$*" in
  *'getinfo pid'*) echo 'D 4242' ;;
  *'keyinfo {KEYGRIP}'*)
    if [ -f {state} ]; then
      echo 'S KEYINFO {KEYGRIP} D - - 1 P - - -'
    else
      echo 'S KEYINFO {KEYGRIP} D - - - P - - -'
    fi
    ;;
esac
echo OK
""",
    )
    _write_executable(
        fake_bin / "gpgconf",
        f"""#!/bin/sh
printf 'gpgconf %s\\n' "$*" >>{log}
exit 0
""",
    )
    _write_executable(
        fake_bin / "gpg",
        f"""#!/bin/sh
printf 'gpg %s\\n' "$*" >>{log}
if [ "{str(cache_after_sign).lower()}" = true ]; then
  touch {state}
fi
exit 0
""",
    )
    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    env["XDG_RUNTIME_DIR"] = str(runtime_dir)
    return env, log, state


def test_check_queries_only_the_exact_keygrip(tmp_path: Path) -> None:
    env, log, _ = _fake_environment(tmp_path, ready=False)

    result = subprocess.run(
        [str(HELPER), "check", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 11
    payload = json.loads(result.stdout)
    assert payload["status"] == "cold"
    assert payload["fingerprint"] == FINGERPRINT
    assert payload["keygrip"] == KEYGRIP
    assert payload["cached"] is False
    calls = log.read_text(encoding="utf-8")
    assert f"--no-autostart keyinfo {KEYGRIP} /bye" in calls
    assert "keyinfo --list" not in calls


def test_check_accepts_the_exact_cached_key(tmp_path: Path) -> None:
    env, _, _ = _fake_environment(tmp_path, ready=True)

    result = subprocess.run(
        [str(HELPER), "check", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["proof"] == "agent-cache"


def test_check_distinguishes_an_absent_agent_from_a_cold_key(tmp_path: Path) -> None:
    env, _, _ = _fake_environment(tmp_path, ready=False, agent_available=False)

    result = subprocess.run(
        [str(HELPER), "check", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 10
    payload = json.loads(result.stdout)
    assert payload["status"] == "agent-unavailable"
    assert payload["agent_running"] is False
    assert payload["cached"] is False


def test_unlock_launches_agent_and_targets_exact_fingerprint(tmp_path: Path) -> None:
    env, log, state = _fake_environment(tmp_path, ready=False)
    master, slave = pty.openpty()
    try:
        process = subprocess.run(
            [str(HELPER), "unlock", "--json"],
            cwd=ROOT,
            env=env,
            check=False,
            stdin=slave,
            stdout=slave,
            stderr=slave,
        )
    finally:
        os.close(slave)
        os.close(master)

    assert process.returncode == 0
    assert state.exists()
    calls = log.read_text(encoding="utf-8")
    assert "gpgconf --launch gpg-agent" in calls
    assert "updatestartuptty /bye" in calls
    assert "--pinentry-mode ask" in calls
    assert f"--local-user {FINGERPRINT}!" in calls
    assert "--detach-sign --output /dev/null /dev/null" in calls


def test_unlock_records_agent_epoch_proof_when_keyinfo_stays_uncached(
    tmp_path: Path,
) -> None:
    env, log, state = _fake_environment(
        tmp_path,
        ready=False,
        cache_after_sign=False,
    )
    master, slave = pty.openpty()
    try:
        unlocked = subprocess.run(
            [str(HELPER), "unlock", "--json"],
            cwd=ROOT,
            env=env,
            check=False,
            stdin=slave,
            capture_output=True,
            text=True,
        )
    finally:
        os.close(slave)
        os.close(master)

    assert unlocked.returncode == 0, unlocked.stderr
    payload = json.loads(unlocked.stdout)
    assert payload["status"] == "ready"
    assert payload["cached"] is False
    assert payload["proof"] == "agent-epoch-signature"
    assert not state.exists()
    proof = (
        Path(env["XDG_RUNTIME_DIR"])
        / "codex-gpg-readiness"
        / f"{KEYGRIP}.proof"
    )
    assert proof.exists()
    assert proof.stat().st_mode & 0o777 == 0o600

    checked = subprocess.run(
        [str(HELPER), "check", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0
    assert json.loads(checked.stdout)["proof"] == "agent-epoch-signature"
    assert log.read_text(encoding="utf-8").count("gpg --") == 1


def test_agent_epoch_proof_rejects_a_different_agent_pid(tmp_path: Path) -> None:
    env, _, _ = _fake_environment(
        tmp_path,
        ready=False,
        cache_after_sign=False,
    )
    master, slave = pty.openpty()
    try:
        unlocked = subprocess.run(
            [str(HELPER), "unlock", "--json"],
            cwd=ROOT,
            env=env,
            check=False,
            stdin=slave,
            capture_output=True,
            text=True,
        )
    finally:
        os.close(slave)
        os.close(master)
    assert unlocked.returncode == 0

    proof = (
        Path(env["XDG_RUNTIME_DIR"])
        / "codex-gpg-readiness"
        / f"{KEYGRIP}.proof"
    )
    proof.write_text(
        proof.read_text(encoding="utf-8").replace("agent_pid=4242", "agent_pid=9999"),
        encoding="utf-8",
    )
    proof.chmod(0o600)
    checked = subprocess.run(
        [str(HELPER), "check", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 11
    assert json.loads(checked.stdout)["status"] == "cold"


def test_shell_snippet_is_idempotent_when_zshrc_is_reloaded(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "zsh",
            "-fc",
            f"source {SHELL_SNIPPET}; source {SHELL_SNIPPET}",
        ],
        cwd=ROOT,
        env={**os.environ, "HOME": str(tmp_path)},
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "read-only variable" not in result.stderr


def test_installer_manages_helper_and_shell_snippet(tmp_path: Path) -> None:
    helper_dest = tmp_path / "bin/codex-gpg-readiness"
    shell_dest = tmp_path / "config/codex/gpg-readiness.zsh"
    helper_dest.parent.mkdir(parents=True, mode=0o700)
    shell_dest.parent.mkdir(parents=True, mode=0o700)

    applied = subprocess.run(
        [
            str(INSTALLER),
            "--apply",
            "--helper-dest",
            str(helper_dest),
            "--shell-dest",
            str(shell_dest),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, applied.stderr
    assert helper_dest.stat().st_mode & 0o777 == 0o755
    assert shell_dest.stat().st_mode & 0o777 == 0o644
    assert helper_dest.parent.stat().st_mode & 0o777 == 0o700
    assert shell_dest.parent.stat().st_mode & 0o777 == 0o700

    checked = subprocess.run(
        [
            str(INSTALLER),
            "--check",
            "--helper-dest",
            str(helper_dest),
            "--shell-dest",
            str(shell_dest),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr
    assert "gpg_cache_ready" in SHELL_SNIPPET.read_text(encoding="utf-8")
