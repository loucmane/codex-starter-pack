"""TM #213: per-session hashed capsule A/B assignment + fixed-n stopping rule.

Spec §7 as amended 2026-06-11: `"ab_assignment": "session-hash"` in brief.json makes
SessionStart pick the capsule arm from sha256(session_id) parity; AEGIS_CAPSULE env and
`inject: false` keep their precedence; the session_begin stamp records the assignment
mode; `aegis ab` counts genuine cold starts (source == "startup") per arm against the
stopping rule that replaced the 2-week calendar window.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"
ASSETS_BRIEF_LIB = REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "brief_lib.py"

sys.path.insert(0, str(REPO_ROOT))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


brief_lib = load_module(ASSETS_BRIEF_LIB, "brief_lib_ab_tests")


def arm_for(session_id: str) -> bool:
    return int(hashlib.sha256(session_id.encode("utf-8")).hexdigest(), 16) % 2 == 0


def session_id_for_arm(injected: bool) -> str:
    for index in range(200):
        candidate = f"ab-session-{index}"
        if arm_for(candidate) is injected:
            return candidate
    raise AssertionError("no session id found for arm")


def make_repo(tmp_path: Path, *, ab: bool = True, inject: bool | None = None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=False,
    )
    brief: dict[str, object] = {"gates": {}}
    if ab:
        brief["ab_assignment"] = "session-hash"
    if inject is not None:
        brief["inject"] = inject
    (repo / ".aegis").mkdir(exist_ok=True)
    (repo / ".aegis" / "brief.json").write_text(json.dumps(brief), encoding="utf-8")
    return repo


def run_sessionstart(
    repo: Path,
    state: Path,
    session_id: str,
    source: str = "startup",
    extra_env: dict[str, str] | None = None,
    payload_cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("AEGIS_CAPSULE", None)
    env["XDG_STATE_HOME"] = state.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    env.update(extra_env or {})
    payload = json.dumps(
        {
            "session_id": session_id,
            "cwd": payload_cwd or repo.as_posix(),
            "hook_event_name": "SessionStart",
            "source": source,
        }
    )
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "sessionstart"],
        cwd=repo,
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def session_begin_events(state: Path) -> list[dict[str, object]]:
    events = []
    for db in (state / "aegis").glob("*/ledger.db"):
        connection = sqlite3.connect(db.as_posix())
        for row in connection.execute(
            "SELECT event_type, extra FROM events WHERE event_type='session_begin' ORDER BY seq"
        ):
            events.append({"event_type": row[0], "extra": json.loads(row[1])})
        connection.close()
    return events


def test_assignment_is_deterministic(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    for session_id in ("a", "b", "ebfac72d-67da-4bcf-b51f-2982a8a94711"):
        first = brief_lib.capsule_assignment(repo, session_id=session_id, env={})
        second = brief_lib.capsule_assignment(repo, session_id=session_id, env={})
        assert first == second
        assert first["mode"] == "session-hash"
        assert first["injected"] is arm_for(session_id)


def test_both_arms_are_reachable(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    arms = {
        brief_lib.capsule_assignment(repo, session_id=f"s-{index}", env={})["injected"]
        for index in range(32)
    }
    assert arms == {True, False}, "hashing must land in both arms across session ids"


def test_env_override_beats_session_hash(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    on_id = session_id_for_arm(True)
    off_id = session_id_for_arm(False)
    forced_off = brief_lib.capsule_assignment(repo, session_id=on_id, env={"AEGIS_CAPSULE": "off"})
    forced_on = brief_lib.capsule_assignment(repo, session_id=off_id, env={"AEGIS_CAPSULE": "on"})
    assert forced_off == {"injected": False, "mode": "env-override"}
    assert forced_on == {"injected": True, "mode": "env-override"}


def test_inject_false_beats_session_hash(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, inject=False)
    assignment = brief_lib.capsule_assignment(repo, session_id=session_id_for_arm(True), env={})
    assert assignment == {"injected": False, "mode": "brief-inject-false"}


def test_no_session_id_never_randomizes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    assert brief_lib.capsule_assignment(repo, session_id=None, env={}) == {
        "injected": True,
        "mode": "static-on",
    }
    assert brief_lib.injection_enabled(repo, env={}) is True


def test_without_ab_key_assignment_is_static(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, ab=False)
    assignment = brief_lib.capsule_assignment(repo, session_id=session_id_for_arm(False), env={})
    assert assignment == {"injected": True, "mode": "static-on"}


def test_sessionstart_off_arm_stamps_without_injecting(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    result = run_sessionstart(repo, state, session_id_for_arm(False))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", "off-arm session must not receive the capsule"
    stamps = session_begin_events(state)
    assert len(stamps) == 1
    assert stamps[0]["extra"]["capsule_injected"] is False
    assert stamps[0]["extra"]["assignment"] == "session-hash"


def test_sessionstart_on_arm_injects_and_stamps(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    result = run_sessionstart(repo, state, session_id_for_arm(True))
    assert result.returncode == 0, result.stderr
    assert "Aegis Session Zero Capsule" in result.stdout
    stamps = session_begin_events(state)
    assert stamps[0]["extra"]["capsule_injected"] is True
    assert stamps[0]["extra"]["assignment"] == "session-hash"


def test_sessionstart_env_off_records_override_mode(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    result = run_sessionstart(repo, state, session_id_for_arm(True), extra_env={"AEGIS_CAPSULE": "off"})
    assert result.stdout.strip() == ""
    stamps = session_begin_events(state)
    assert stamps[0]["extra"]["capsule_injected"] is False
    assert stamps[0]["extra"]["assignment"] == "env-override"


def run_ab_cli(repo: Path, state: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state.as_posix()
    return subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "ab", "--target-dir", repo.as_posix(), "--json", *extra],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_ab_counts_only_genuine_cold_starts(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    on_id = session_id_for_arm(True)
    off_id = session_id_for_arm(False)
    run_sessionstart(repo, state, on_id)
    run_sessionstart(repo, state, off_id)
    run_sessionstart(repo, state, on_id + "-resume", source="resume")
    run_sessionstart(repo, state, on_id + "-compact", source="compact")
    result = run_ab_cli(repo, state, "--min-n", "2")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["cold_starts"]["on"] >= 1
    assert report["cold_starts"]["off"] >= 1
    assert report["cold_starts"]["on"] + report["cold_starts"]["off"] == 2
    assert report["excluded_non_startup"] == 2
    assert report["min_n_per_arm"] == 2
    assert report["stopping_rule_met"] is False


def test_ab_excludes_out_of_repo_harness_sessions(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    run_sessionstart(repo, state, session_id_for_arm(True))
    # A replay-worktree session shares the ledger via the git common dir but begins
    # elsewhere — it must not count as a live A/B observation.
    run_sessionstart(repo, state, session_id_for_arm(False), payload_cwd="/tmp/aegis-coldstart-x/wt")
    result = run_ab_cli(repo, state, "--min-n", "1")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["cold_starts"] == {"on": 1, "off": 0}
    assert report["excluded_other_cwd"] == 1


def test_ab_stopping_rule_met(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    minted = {True: 0, False: 0}
    index = 0
    while min(minted.values()) < 2:
        session_id = f"fill-{index}"
        index += 1
        if minted[arm_for(session_id)] >= 2:
            continue
        run_sessionstart(repo, state, session_id)
        minted[arm_for(session_id)] += 1
    result = run_ab_cli(repo, state, "--min-n", "2")
    report = json.loads(result.stdout)
    assert report["stopping_rule_met"] is True
    assert report["remaining"] == {"on": 0, "off": 0}


def test_codex_brief_opts_into_session_hash() -> None:
    brief = json.loads((REPO_ROOT / ".aegis" / "brief.json").read_text(encoding="utf-8"))
    assert brief["ab_assignment"] == "session-hash"
    assert brief.get("inject") is True


def test_spec_documents_the_amendment() -> None:
    spec = (REPO_ROOT / "docs" / "aegis" / "AEGIS_CAPSULE_SPEC.md").read_text(encoding="utf-8")
    assert "session-hash" in spec
    assert "Stopping rule" in spec
    assert "supersedes the original calendar-day alternation" in spec


def test_assets_and_live_copies_identical() -> None:
    for rel in (".claude/scripts/gate_lib.py", ".claude/scripts/brief_lib.py"):
        live = (REPO_ROOT / rel).read_bytes()
        asset = (REPO_ROOT / "aegis_foundation" / "assets" / rel).read_bytes()
        assert live == asset, f"assets/live copies diverge for {rel}"
