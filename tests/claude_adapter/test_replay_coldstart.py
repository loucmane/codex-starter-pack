"""TM #211: replay-cold-start A/B falsifier — testable core.

Covers the transcript parser, meaningful-action detection, worktree reconstruction, and
the scoring/aggregation/decision math against fixtures. The live `claude -p` execution
is operator-only (AEGIS_RUN_COLDSTART_AB=1) and not exercised here.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = REPO_ROOT / "tests" / "fixtures" / "coldstart_transcripts"
sys.path.insert(0, str(REPO_ROOT))

from aegis_foundation import replay_coldstart as rc  # noqa: E402


def test_meaningful_action_detection() -> None:
    assert rc.is_meaningful_action("Edit", {"file_path": "app/src/main.ts"}) is True
    assert rc.is_meaningful_action("Write", {"file_path": "worker/h.py"}) is True
    # governance / scratch surfaces are not "real work"
    assert rc.is_meaningful_action("Write", {"file_path": ".aegis/capsule/current.md"}) is False
    assert rc.is_meaningful_action("Edit", {"file_path": "sessions/current"}) is False
    assert rc.is_meaningful_action("Edit", {"file_path": "docs/ai/work-tracking/active/x/TRACKER.md"}) is False
    # reads are never meaningful actions
    assert rc.is_meaningful_action("Read", {"file_path": "app/src/main.ts"}) is False
    # bash mutations to real paths count; to scratch don't; read-only don't
    assert rc.is_meaningful_action("Bash", {"command": "sed -i s/a/b/ app/x.ts"}) is True
    assert rc.is_meaningful_action("Bash", {"command": "git status"}) is False
    assert rc.is_meaningful_action("Bash", {"command": "aegis log --pending-id current"}) is False


def test_extract_first_action_cost_low_vs_high() -> None:
    low = rc.extract_first_action_cost(FIX / "capsule_low_recon.jsonl")
    high = rc.extract_first_action_cost(FIX / "baseline_high_recon.jsonl")
    assert low["reached_meaningful_action"] is True
    assert low["recon_calls_before_first_action"] == 1
    assert high["recon_calls_before_first_action"] == 5
    assert high["first_action"]["tool"] == "Edit"


def test_governance_mutations_do_not_count_as_first_action() -> None:
    cost = rc.extract_first_action_cost(FIX / "governance_then_action.jsonl")
    # git status (recon) + .aegis write (not meaningful) + aegis log (not meaningful)
    # then the worker/handler.py write IS the first meaningful action -> 3 recon before.
    assert cost["reached_meaningful_action"] is True
    assert cost["recon_calls_before_first_action"] == 3
    assert "worker" not in (cost["first_action"]["input_keys"])  # sanity on shape


def test_never_acts_counts_all_as_recon() -> None:
    cost = rc.extract_first_action_cost(FIX / "never_acts.jsonl")
    assert cost["reached_meaningful_action"] is False
    assert cost["recon_calls_before_first_action"] == cost["total_tool_calls"] == 3


def test_worktree_reconstruction(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    (repo / "f.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "v1"],
        cwd=repo, check=False,
    )
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=False).stdout.strip()
    (repo / "f.txt").write_text("v2\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-aqm", "v2", "-c", "commit.gpgsign=false"], cwd=repo, check=False)
    dest = tmp_path / "wt"
    rc.build_scenario_worktree(repo, sha, dest)
    assert (dest / "f.txt").read_text(encoding="utf-8") == "v1\n", "worktree reconstructs the historical state"
    rc.remove_worktree(repo, dest)
    assert not dest.exists()


def _scores(scenario, arm, recon_list, reached=True, correct=None):
    return [
        rc.score_arm(scenario, arm, {"recon_calls_before_first_action": r, "reached_meaningful_action": reached, "total_tool_calls": r + 1, "first_action": None}, first_action_correct=correct)
        for r in recon_list
    ]


def test_aggregate_and_keep_eligible_verdict() -> None:
    scores = []
    # 3 decision scenarios: capsule consistently ~1 recon, baseline ~5
    for sid in ("rot-a", "rot-b", "silent-c"):
        scores += _scores(sid, "capsule", [1, 1], correct=True)
        scores += _scores(sid, "baseline", [5, 5], correct=False)
    # fresh-null: both arms cheap and equal
    scores += _scores("fresh", "capsule", [1, 1])
    scores += _scores("fresh", "baseline", [1, 1])
    agg = rc.aggregate(scores, fresh_null_ids=["fresh"])
    assert agg["decision_delta_recon"]["delta"] == 4.0
    assert agg["decision_delta_recon"]["ci_low"] > 0
    assert abs(agg["fresh_null_delta_recon"]["delta"]) <= 0.5
    assert agg["correctness"]["capsule_correct"] == 6
    verdict = rc.decide(agg)
    assert verdict["recommendation"] == "KEEP-ELIGIBLE"
    assert "live A/B" in verdict["reason"]


def test_fresh_null_violation_forces_inconclusive() -> None:
    scores = []
    for sid in ("rot-a", "rot-b"):
        scores += _scores(sid, "capsule", [1, 1])
        scores += _scores(sid, "baseline", [5, 5])
    # fresh-null shows a big (illegitimate) capsule edge -> battery is capsule-shaped
    scores += _scores("fresh", "capsule", [1, 1])
    scores += _scores("fresh", "baseline", [5, 5])
    agg = rc.aggregate(scores, fresh_null_ids=["fresh"])
    verdict = rc.decide(agg)
    assert verdict["recommendation"] == "INCONCLUSIVE"
    assert "fresh-null" in verdict["reason"]


def test_no_effect_fires_kill() -> None:
    scores = []
    for sid in ("a", "b", "c"):
        scores += _scores(sid, "capsule", [3, 3])
        scores += _scores(sid, "baseline", [3, 3])
    agg = rc.aggregate(scores)
    verdict = rc.decide(agg)
    assert verdict["recommendation"] == "KILL"


def test_straddling_ci_is_inconclusive() -> None:
    # Opposite-sign per-scenario deltas (+3, -3): mean 0, wide CI straddling 0.
    scores = []
    scores += _scores("a", "capsule", [2, 2])
    scores += _scores("a", "baseline", [5, 5])
    scores += _scores("b", "capsule", [5, 5])
    scores += _scores("b", "baseline", [2, 2])
    agg = rc.aggregate(scores)
    assert agg["decision_delta_recon"]["ci_low"] < 0 < agg["decision_delta_recon"]["ci_high"]
    verdict = rc.decide(agg)
    assert verdict["recommendation"] == "INCONCLUSIVE"


def test_render_report_smoke() -> None:
    scores = _scores("a", "capsule", [1]) + _scores("a", "baseline", [4]) + _scores("b", "capsule", [1]) + _scores("b", "baseline", [4])
    agg = rc.aggregate(scores)
    report = rc.render_report(agg, rc.decide(agg))
    assert "VERDICT:" in report
    assert "decision recon delta" in report


def test_live_execution_is_operator_gated(monkeypatch: pytest.MonkeyPatch) -> None:
    # run_live_ab must refuse to fire real claude -p sessions without the explicit gate.
    monkeypatch.delenv(rc.RUN_GATE_ENV, raising=False)
    with pytest.raises(RuntimeError, match="operator-only"):
        rc.run_live_ab(REPO_ROOT, [{"scenario_id": "x", "sha": "HEAD"}])
    # And the only claude invocation lives below the OPERATOR-ONLY divider.
    text = (REPO_ROOT / "aegis_foundation" / "replay_coldstart.py").read_text(encoding="utf-8")
    pre, _, post = text.partition("OPERATOR-ONLY LIVE EXECUTION")
    assert post, "operator divider present"
    assert '"claude"' not in pre, "no claude invocation in the CI-tested core"
