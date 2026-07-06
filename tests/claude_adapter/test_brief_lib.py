"""PR-2a tests: computed capsule compiler, drift sentinel + canary, --check mode.

Merge gate (spec section 1.2 row 2a): brief output matches independently-checked
reality — asserted here against fixture repos with controlled state.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_BRIEF_LIB = REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "brief_lib.py"
LIVE_BRIEF_LIB = REPO_ROOT / ".claude" / "scripts" / "brief_lib.py"
LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


brief_lib = load_module(ASSETS_BRIEF_LIB, "brief_lib_under_test")
ledger_lib = load_module(LEDGER_LIB, "ledger_lib_for_brief_tests")


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/task-9-brief"], cwd=repo, check=False)
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=False,
    )
    monkeypatch.setenv("XDG_STATE_HOME", (tmp_path / "state").as_posix())
    return repo


def write_brief_config(repo: Path) -> None:
    path = repo / ".aegis" / "brief.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "gates": {"app": {"test": ["pnpm -C app test"], "lint": ["pnpm -C app lint"]}},
                "source_roots": ["app/"],
                "thresholds": {"branch_count": 30, "unignored_file_mb": 5},
                "redact_extra": [],
                "archive_keep": 20,
                "inject": True,
            }
        ),
        encoding="utf-8",
    )


def head_commit(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True, check=False
    ).stdout.strip()


def seed_verification(repo: Path, package: str, gate: str, exit_class: str, commit: str) -> None:
    ledger = ledger_lib.open_ledger(cwd=repo)
    try:
        ledger.append(
            {
                "event_type": "verification",
                "branch": "feat/task-9-brief",
                "exit_class": exit_class,
                "outcome": exit_class,
                "extra": {"package": package, "gate": gate, "commit": commit},
            }
        )
    finally:
        ledger.close()


def test_assets_and_live_brief_lib_copies_identical() -> None:
    assert ASSETS_BRIEF_LIB.read_bytes() == LIVE_BRIEF_LIB.read_bytes()


def test_compile_never_raises_outside_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", (tmp_path / "state").as_posix())
    plain = tmp_path / "plain"
    plain.mkdir()
    capsule = brief_lib.compile_capsule(plain)
    assert capsule["capsule_meta"]["source_commit"] == brief_lib.STALE
    assert capsule["task_truth"]["counts"] == "no taskmaster"


def test_verification_ledger_reports_absence_runs_and_staleness(repo: Path) -> None:
    write_brief_config(repo)
    commit = head_commit(repo)
    seed_verification(repo, "app", "test", "pass", commit)
    seed_verification(repo, "app", "lint", "fail", "0000000")
    capsule = brief_lib.compile_capsule(repo)
    gates = capsule["verification_ledger"]["gates"]
    assert gates["app:test"]["exit_class"] == "pass"
    assert gates["app:test"]["stale"] is False
    assert gates["app:lint"]["exit_class"] == "fail"
    assert gates["app:lint"]["stale"] is True, "HEAD moved past the run's commit"
    rendered = brief_lib.render_markdown(capsule)
    assert "app:test: pass" in rendered


def test_verification_absence_is_reported_explicitly(repo: Path) -> None:
    write_brief_config(repo)
    capsule = brief_lib.compile_capsule(repo)
    assert capsule["verification_ledger"]["gates"]["app:test"] == {"no_run_on_record": True}
    assert "NO RUN ON RECORD" in brief_lib.render_markdown(capsule)


def test_sentinel_canary_always_flags_and_check_passes(repo: Path) -> None:
    capsule = brief_lib.compile_capsule(repo)
    sentinel = capsule["drift_sentinel"]
    assert sentinel["canary_flagged"] is True
    assert sentinel["sentinel_ok"] is True
    assert any("canary" in item for item in sentinel["drift"])
    assert (repo / ".aegis" / "capsule" / "canary.md").is_file(), "canary auto-created"
    ok, problems = brief_lib.check_capsule(repo)
    assert ok, problems


def test_sentinel_broken_when_canary_cannot_flag(repo: Path) -> None:
    canary = repo / ".aegis" / "capsule" / "canary.md"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("no claim here\n", encoding="utf-8")
    capsule = brief_lib.compile_capsule(repo)
    assert capsule["drift_sentinel"]["sentinel_ok"] is False
    assert "SENTINEL BROKEN" in brief_lib.render_markdown(capsule)
    ok, problems = brief_lib.check_capsule(repo)
    assert not ok
    assert any("canary" in problem for problem in problems)


def test_stranded_done_flip_detected(repo: Path) -> None:
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks.parent.mkdir(parents=True)
    tasks.write_text(json.dumps({"master": {"tasks": [{"id": 9, "status": "pending"}]}}), encoding="utf-8")
    subprocess.run(["git", "add", "-f", tasks.relative_to(repo).as_posix()], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "tasks"],
        cwd=repo,
        check=False,
    )
    tasks.write_text(json.dumps({"master": {"tasks": [{"id": 9, "status": "done"}]}}, indent=1), encoding="utf-8")
    capsule = brief_lib.compile_capsule(repo)
    assert capsule["task_truth"]["uncommitted_done_flips"] is True
    assert any("stranded-flip" in item for item in capsule["drift_sentinel"]["drift"])


def test_claude_md_task_count_claim_checked(repo: Path) -> None:
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks.parent.mkdir(parents=True)
    tasks.write_text(json.dumps({"master": {"tasks": [{"id": 1, "status": "done"}]}}), encoding="utf-8")
    (repo / "CLAUDE.md").write_text("This project tracks 5 parent tasks.\n", encoding="utf-8")
    capsule = brief_lib.compile_capsule(repo)
    assert any("claims 5 parent tasks" in item for item in capsule["drift_sentinel"]["drift"])
    (repo / "CLAUDE.md").write_text("This project tracks 1 parent tasks.\n", encoding="utf-8")
    capsule = brief_lib.compile_capsule(repo)
    assert not any("parent tasks" in item for item in capsule["drift_sentinel"]["drift"])


def test_broken_plans_pointer_is_drift(repo: Path) -> None:
    plans = repo / "plans"
    plans.mkdir()
    (plans / "current").symlink_to("2026-01-01-missing-plan.md")
    capsule = brief_lib.compile_capsule(repo)
    assert any("plans/current" in item for item in capsule["drift_sentinel"]["drift"])


def test_risk_seed_consumed_once(repo: Path) -> None:
    seed = repo / ".aegis" / "capsule" / "risk-seed.json"
    seed.parent.mkdir(parents=True, exist_ok=True)
    seed.write_text(
        json.dumps([{"claim": "sync-direction hazard", "discovered_at": "2026-06-10"}]),
        encoding="utf-8",
    )
    first = brief_lib.compile_capsule(repo)
    assert first["risk_register"][0]["claim"] == "sync-direction hazard"
    seed.write_text(json.dumps([{"claim": "REPLACED", "discovered_at": "2026-06-11"}]), encoding="utf-8")
    second = brief_lib.compile_capsule(repo)
    assert second["risk_register"][0]["claim"] == "sync-direction hazard", "seed consumed once"


def test_governance_tallies_gate_decisions(repo: Path) -> None:
    ledger = ledger_lib.open_ledger(cwd=repo)
    try:
        ledger.append({"event_type": "gate_decision", "extra": {"verdict": "would_block"}})
        ledger.append({"event_type": "gate_decision", "extra": {"verdict": "allow"}})
    finally:
        ledger.close()
    capsule = brief_lib.compile_capsule(repo)
    tallies = capsule["governance"]["decisions_since_last_capsule"]
    assert tallies.get("would_block") == 1 and tallies.get("allow") == 1


def test_capsule_status_tracks_compile_boundaries_and_staleness(repo: Path) -> None:
    missing = brief_lib.capsule_status(repo)
    assert missing["status"] == "stale"
    assert "missing or unreadable" in missing["reasons"][0]

    capsule = brief_lib.compile_capsule(repo, reason="post-merge")
    assert capsule["capsule_meta"]["compile_reason"] == "post-merge"
    brief_lib.write_capsule(repo, capsule, brief_lib.render_markdown(capsule))
    fresh = brief_lib.capsule_status(repo)
    assert fresh["status"] == "fresh", fresh

    ledger = ledger_lib.open_ledger(cwd=repo)
    try:
        ledger.append({"event_type": "gate_decision", "extra": {"verdict": "would_block"}})
    finally:
        ledger.close()
    stale = brief_lib.capsule_status(repo)
    assert stale["status"] == "stale"
    assert any("new gate decisions recorded" in reason for reason in stale["reasons"])

    capsule = brief_lib.compile_capsule(repo, reason="orientation")
    brief_lib.write_capsule(repo, capsule, brief_lib.render_markdown(capsule))
    assert brief_lib.capsule_status(repo)["status"] == "fresh"

    (repo / "after.txt").write_text("after\n", encoding="utf-8")
    subprocess.run(["git", "add", "after.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "after"],
        cwd=repo,
        check=False,
    )
    head_stale = brief_lib.capsule_status(repo)
    assert head_stale["status"] == "stale"
    assert any("HEAD changed" in reason for reason in head_stale["reasons"])


def test_cli_brief_status_reports_freshness(repo: Path) -> None:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = os.environ["XDG_STATE_HOME"]
    stale = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "brief", "--target-dir", repo.as_posix(), "--status"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert stale.returncode == 1
    assert "capsule status: STALE" in stale.stdout

    compiled = subprocess.run(
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "brief",
            "--target-dir",
            repo.as_posix(),
            "--reason",
            "post-merge",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr
    assert json.loads(compiled.stdout)["capsule_meta"]["compile_reason"] == "post-merge"
    fresh = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "brief", "--target-dir", repo.as_posix(), "--status"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert fresh.returncode == 0, fresh.stdout + fresh.stderr
    assert "capsule status: fresh" in fresh.stdout


def test_check_fails_over_char_budget(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(brief_lib, "CHAR_BUDGET", 10)
    ok, problems = brief_lib.check_capsule(repo)
    assert not ok
    assert any("budget" in problem for problem in problems)


def test_cli_brief_json_and_capsule_files(repo: Path) -> None:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = os.environ["XDG_STATE_HOME"]
    result = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "brief", "--target-dir", repo.as_posix(), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    capsule = json.loads(result.stdout)
    for key in (
        "capsule_meta",
        "repo_pose",
        "delivery_state",
        "verification_ledger",
        "task_truth",
        "governance",
        "drift_sentinel",
        "repo_hygiene",
        "risk_register",
    ):
        assert key in capsule
    assert (repo / ".aegis" / "capsule" / "current.md").is_file()
    assert (repo / ".aegis" / "capsule" / "current.json").is_file()


def test_gate_classifies_brief_read_only() -> None:
    gate_lib = load_module(REPO_ROOT / ".claude" / "scripts" / "gate_lib.py", "gate_lib_for_brief")
    assert gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli brief --target-dir .") is True
    assert gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli brief --check") is True
    assert gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli brief --status") is True
    assert gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli brief --reason post-merge") is True
