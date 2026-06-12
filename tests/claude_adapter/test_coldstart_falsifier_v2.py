"""TM #212: cold-start falsifier v2 — recon-to-correct-decision + READY envelopes.

V1's metric inverted on gated done-states (correctly doing nothing scored as a loss).
V2 grades each run against scenario ground truth: a correct do-nothing is a success,
a fast wrong mutation is a failure; recon deltas are computed among correct runs only,
and the verdict additionally requires the capsule arm not to lose decision accuracy.
Scenarios come from forward-captured in-progress states (`aegis coldstart capture`)
replayed as READY-envelope worktrees under advisory enforcement.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from aegis_foundation import replay_coldstart as rc  # noqa: E402


def write_transcript(path: Path, events: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


def tool_use(name: str, **tool_input: object) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": tool_input}]}}


def text_block(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def make_task_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-q")
    run_git(repo, "checkout", "-q", "-b", "feat/task-42-widget")
    (repo / "src").mkdir()
    (repo / "src" / "widget.py").write_text("x = 1\n", encoding="utf-8")
    plans = repo / "plans"
    plans.mkdir()
    (plans / "2026-06-12-task42-widget.md").write_text(
        "# Plan - Task 42\n\n"
        "| Step ID | Description | Evidence | Status |\n"
        "| --- | --- | --- | --- |\n"
        "| plan-step-scope | Scope the widget refactor | designs/x.md | completed |\n"
        "| plan-step-implement | Implement the widget parser overhaul | src/widget.py | pending |\n\n"
        "## Scope\n- `src/`\n- `tests/`\n",
        encoding="utf-8",
    )
    (plans / "current").symlink_to("2026-06-12-task42-widget.md")
    run_git(repo, "add", "-A")
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=False,
    )
    return repo


# --- score_decision ----------------------------------------------------------------


def test_correct_continue_counts_recon_to_on_target_mutation(tmp_path: Path) -> None:
    transcript = write_transcript(
        tmp_path / "t.jsonl",
        [
            tool_use("Read", file_path="src/widget.py"),
            tool_use("Grep", pattern="widget"),
            tool_use("Edit", file_path="src/widget.py", old_string="x", new_string="y"),
        ],
    )
    result = rc.score_decision(transcript, {"decision_class": "continue", "target_prefixes": ["src/"]})
    assert result["correct"] is True
    assert result["recon_to_decision"] == 2


def test_wrong_target_mutation_is_incorrect(tmp_path: Path) -> None:
    transcript = write_transcript(
        tmp_path / "t.jsonl",
        [tool_use("Edit", file_path="README.md", old_string="a", new_string="b")],
    )
    result = rc.score_decision(transcript, {"decision_class": "continue", "target_prefixes": ["src/"]})
    assert result["correct"] is False
    assert result["reached"] is True


def test_correct_do_nothing_rewards_restraint(tmp_path: Path) -> None:
    """The v1 inversion case: a well-oriented agent that forages and then correctly
    concludes 'nothing to do' must score as CORRECT, with its foraging as the cost."""

    transcript = write_transcript(
        tmp_path / "t.jsonl",
        [
            tool_use("Bash", command="git status --short"),
            tool_use("Read", file_path="plans/current"),
            text_block("All work on this branch is complete; nothing to do."),
        ],
    )
    result = rc.score_decision(transcript, {"decision_class": "do_nothing", "keywords_any": ["complete", "nothing to do"]})
    assert result["correct"] is True
    assert result["recon_to_decision"] == 2


def test_charge_ahead_mutation_on_done_state_is_incorrect(tmp_path: Path) -> None:
    transcript = write_transcript(
        tmp_path / "t.jsonl",
        [tool_use("Write", file_path="src/new.py", content="x")],
    )
    result = rc.score_decision(transcript, {"decision_class": "do_nothing", "keywords_any": ["complete"]})
    assert result["correct"] is False


# --- capture_scenario --------------------------------------------------------------


def test_capture_derives_ground_truth_from_active_plan(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    (repo / "src" / "widget.py").write_text("x = 2\n", encoding="utf-8")  # dirty state
    scenario = rc.capture_scenario(repo, note="mid-task checkpoint")
    assert scenario["schema"] == "coldstart-scenario/2"
    assert scenario["branch"] == "feat/task-42-widget"
    assert scenario["expected"]["decision_class"] == "continue"
    assert "parser" in scenario["expected"]["keywords_any"]
    assert scenario["expected"]["target_prefixes"] == ["src/", "tests/"]
    assert "widget.py" in scenario["dirty_patch"]
    assert scenario["dirty_patch_truncated"] is False


def test_capture_without_open_plan_steps_expects_do_nothing(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    plan = repo / "plans" / "2026-06-12-task42-widget.md"
    plan.write_text(plan.read_text(encoding="utf-8").replace("| pending |", "| completed |"), encoding="utf-8")
    scenario = rc.capture_scenario(repo)
    assert scenario["expected"]["decision_class"] == "do_nothing"
    assert "complete" in scenario["expected"]["keywords_any"]


def test_capture_expect_class_override(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    scenario = rc.capture_scenario(repo, expect_class="do_nothing", fresh_null=True)
    assert scenario["expected"]["decision_class"] == "do_nothing"
    assert scenario["fresh_null"] is True


# --- READY-envelope worktree --------------------------------------------------------


def test_envelope_worktree_restores_branch_patch_and_advisory(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    (repo / "src" / "widget.py").write_text("x = 2\n", encoding="utf-8")
    scenario = rc.capture_scenario(repo)
    run_git(repo, "checkout", "-q", ".")  # operator moves on; replay must not need the live dirty state
    wt = rc.build_envelope_worktree(repo, scenario, tmp_path / "wt")
    try:
        branch = run_git(wt, "branch", "--show-current").stdout.strip()
        assert branch == "feat/task-42-widget-coldstart-replay", "replay branch must carry the task id"
        assert (wt / "src" / "widget.py").read_text(encoding="utf-8") == "x = 2\n", "dirty patch reapplied"
        enforcement = json.loads((wt / ".aegis" / "state" / "enforcement.json").read_text(encoding="utf-8"))
        assert enforcement["mode"] == "advisory"
        assert (wt / "plans" / "current").exists(), "committed workflow envelope present"
    finally:
        rc.remove_envelope_worktree(repo, scenario, wt)
    assert "coldstart-replay" not in run_git(repo, "branch", "--list").stdout


# --- aggregation + verdict -----------------------------------------------------------


def score(scenario_id: str, arm: str, *, correct: bool, recon: int) -> dict:
    return {"scenario_id": scenario_id, "arm": arm, "correct": correct, "recon_to_decision": recon, "reached": True}


def test_recon_delta_counts_correct_runs_only() -> None:
    scores = [
        score("s1", "capsule", correct=True, recon=3),
        score("s1", "capsule", correct=False, recon=0),  # fast wrong answer must not help
        score("s1", "baseline", correct=True, recon=10),
        score("s2", "capsule", correct=True, recon=4),
        score("s2", "baseline", correct=True, recon=9),
    ]
    aggregated = rc.aggregate_v2(scores)
    assert aggregated["decision_delta_recon"]["n"] == 2
    assert aggregated["decision_delta_recon"]["delta"] == pytest.approx(6.0)
    assert aggregated["accuracy"]["capsule"] == pytest.approx(0.667, abs=0.01)
    assert aggregated["accuracy"]["baseline"] == 1.0


def test_verdict_kills_on_accuracy_loss() -> None:
    scores = [
        score("s1", "capsule", correct=False, recon=1),
        score("s1", "baseline", correct=True, recon=8),
        score("s2", "capsule", correct=False, recon=1),
        score("s2", "baseline", correct=True, recon=8),
    ]
    verdict = rc.decide_v2(rc.aggregate_v2(scores))
    assert verdict["recommendation"] == "KILL"
    assert "accuracy" in verdict["reason"]


def test_verdict_keep_eligible_requires_delta_and_accuracy() -> None:
    scores = []
    for sid in ("s1", "s2", "s3"):
        scores += [
            score(sid, "capsule", correct=True, recon=3),
            score(sid, "baseline", correct=True, recon=12),
        ]
    scores += [
        score("null", "capsule", correct=True, recon=5),
        score("null", "baseline", correct=True, recon=5),
    ]
    verdict = rc.decide_v2(rc.aggregate_v2(scores, fresh_null_ids=["null"]), min_delta=1.0)
    assert verdict["recommendation"] == "KEEP-ELIGIBLE"


def test_verdict_inconclusive_when_fresh_null_violated() -> None:
    scores = []
    for sid in ("s1", "s2"):
        scores += [
            score(sid, "capsule", correct=True, recon=3),
            score(sid, "baseline", correct=True, recon=12),
        ]
    scores += [
        score("null", "capsule", correct=True, recon=2),
        score("null", "baseline", correct=True, recon=9),  # clean state shows a big edge = battery is capsule-shaped
    ]
    verdict = rc.decide_v2(rc.aggregate_v2(scores, fresh_null_ids=["null"]))
    assert verdict["recommendation"] == "INCONCLUSIVE"
    assert "fresh-null" in verdict["reason"]


# --- CLI ------------------------------------------------------------------------------


def test_cli_coldstart_capture_writes_scenario(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    out = tmp_path / "scenario.json"
    result = subprocess.run(
        [
            sys.executable, "-m", "aegis_foundation.cli", "coldstart", "capture",
            "--target-dir", repo.as_posix(), "--out", out.as_posix(), "--id", "probe-1",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["scenario_id"] == "probe-1"
    scenario = json.loads(out.read_text(encoding="utf-8"))
    assert scenario["expected"]["decision_class"] == "continue"


def test_live_runner_v2_is_operator_gated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(rc.RUN_GATE_ENV, raising=False)
    with pytest.raises(RuntimeError, match="operator-only"):
        rc.run_live_ab_v2(REPO_ROOT, [])
