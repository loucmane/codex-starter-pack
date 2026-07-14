"""TM #195: replay harness — corpora run through the REAL gate in CI on every PR.

The standing rule this enforces: no gate-behavior change ships unreplayed. Regression
definitions live in aegis_foundation/replay.py; this suite asserts the committed
corpora hold under the current policy, plus the two must-fire goldens (E01 observe-stop
dirty tree; E29 trailing-pending Stop gate) directly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPORA = sorted((REPO_ROOT / "tests" / "fixtures" / "replay").glob("*.jsonl"))

sys.path.insert(0, str(REPO_ROOT))
from aegis_foundation import replay  # noqa: E402
from scripts import _aegis_installer  # noqa: E402


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    work = tmp_path_factory.mktemp("replay")
    return replay.run_corpus(CORPORA, source_root=REPO_ROOT, work_dir=work)


def test_corpora_exist_and_cover_all_labels() -> None:
    assert CORPORA, "committed replay corpora required"
    entries = replay.load_corpus(CORPORA)
    labels = {entry["label"] for entry in entries}
    assert {"fp_workflow_state", "ceremony_interior", "must_allow", "must_fire", "adversarial_must_block"} <= labels
    for entry in entries:
        assert entry["label"] in replay.LABELS
        assert entry["state"] in replay.STATES


def test_no_regressions_under_current_policy(report: dict[str, object]) -> None:
    assert report["passed"], replay.render_report(report)


def test_fp_baseline_is_locked(report: dict[str, object]) -> None:
    # The historical false positives still block under today's strict policy. This
    # number is the program's improvement metric: it may only ever DECREASE, and any
    # decrease must arrive with a deliberate corpus update in the same change.
    #
    # 2026-06-13 (TM 216): 9 -> 8. The churn-engine fix classifies the read-only
    # `jq`/`ls` compound in corpus entry E04a (HP-Coach friction case "E04: read-only
    # jq/ls compound gated as persistent mutation while readiness BLOCKED") as
    # inspection, so it no longer blocks — a genuine false-positive elimination. E04a
    # now surfaces in report["improvements"]; see test_e04a_read_only_jq_is_freed.
    #
    # 2026-06-14 (TM 191): 8 -> 7. Browser-observation MCP tools are now read-only, so
    # corpus entry E24a (mcp__playwright__browser_snapshot, "browser verification taxed
    # by pending tracking") no longer blocks — see test_e24a_browser_snapshot_is_freed.
    assert report["fp_baseline"] == 7, (
        f"FP baseline moved to {report['fp_baseline']} (expected 7). If a policy change "
        "legitimately freed historical false positives, update this lock and the corpus "
        "notes in the same PR — never silently."
    )


def test_e04a_read_only_jq_is_freed(report: dict[str, object]) -> None:
    # TM 216 churn-engine fix: the read-only jq/ls compound that historically blocked
    # under BLOCKED readiness is now correctly allowed. Pin it as an improvement so a
    # future regression that re-blocks it is caught.
    results = {result["id"]: result for result in report["results"]}
    assert results["E04a"]["verdict"] == "allow", "read-only jq/ls compound must no longer block"
    improvement_ids = {item["id"] for item in report["improvements"]}
    assert "E04a" in improvement_ids


def test_e24a_browser_snapshot_is_freed(report: dict[str, object]) -> None:
    # TM 191: browser-observation MCP tools are read-only, so the browser_snapshot
    # verification call no longer arms pending-tracking / blocks. Pin as improvement.
    results = {result["id"]: result for result in report["results"]}
    assert results["E24a"]["verdict"] == "allow", "browser_snapshot must no longer be taxed"
    assert "E24a" in {item["id"] for item in report["improvements"]}


def test_known_gaps_are_exactly_the_documented_ones(report: dict[str, object]) -> None:
    gap_ids = {gap["id"] for gap in report["standing_gaps"]}
    assert gap_ids == {"ADV-git-hook-write", "ADV-postinstall"}, (
        f"standing adversarial gaps changed: {gap_ids}. Closing one is an improvement — "
        "flip its expected_gap to false in the corpus in the same PR. A NEW gap is a "
        "regression in disguise."
    )


def test_adversarial_blocks_hold(report: dict[str, object]) -> None:
    results = {result["id"]: result for result in report["results"]}
    for blocked_id in ("ADV-settings-write", "ADV-gate-edit", "ADV-state-edit", "ADV-template-sed", "ADV-taskmaster-blocked", "ADV-workflow-owned"):
        assert results[blocked_id]["verdict"] == "block", f"{blocked_id} must block"


def test_e29_stop_gate_must_fire(report: dict[str, object]) -> None:
    results = {result["id"]: result for result in report["results"]}
    assert results["E29a"]["verdict"] == "block", "the trailing-pending Stop gate is the must-fire set"
    assert results["OK-stop-clean"]["verdict"] == "allow", "clean stop must not fire"


def test_advisory_pending_replay_allows_and_preserves_complete_queue(
    report: dict[str, object],
) -> None:
    results = {result["id"]: result for result in report["results"]}
    assert results["OK-advisory-pending-edit"]["verdict"] == "allow"
    assert results["OK-advisory-pending-stop"]["verdict"] == "allow"

    report_path = Path(str(report["report_path"]))
    queue_path = (
        report_path.parent
        / "ready_advisory_pending"
        / ".aegis"
        / "state"
        / "pending-tracking.json"
    )
    events = json.loads(queue_path.read_text(encoding="utf-8"))["events"]
    assert len(events) == 97
    assert {event["mode"] for event in events} == {"advisory"}
    enforcement = json.loads(
        (queue_path.parent / "enforcement.json").read_text(encoding="utf-8")
    )
    assert enforcement["mode"] == "advisory"


def test_e01_observe_stop_refuses_dirty_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", (tmp_path / "state").as_posix())
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=target, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false",
         "commit", "-q", "--allow-empty", "-m", "seed"],
        cwd=target,
        check=False,
    )
    init = _aegis_installer.initialize_project(
        target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], verify_after_install=False
    )
    assert init.get("status") == "initialized", init.get("status")
    reload_marker = target / ".aegis" / "state" / "client-reload-required.json"
    if reload_marker.exists():
        reload_marker.unlink()  # simulate the post-install Claude restart
    started = _aegis_installer.start_observation(
        target, title="Replay E01 observation", slug="replay-e01", goals=["observe"], source_root=REPO_ROOT
    )
    assert started.get("status") not in {"refused", "failed"}, started
    (target / "stray-screenshot.png").write_bytes(b"PNG")
    stopped = _aegis_installer.stop_observation(
        target, summary="replay E01", allow_dirty=False, collect_artifacts=False, source_root=REPO_ROOT
    )
    assert stopped.get("status") in {"blocked", "refused", "failed"}, (
        "E01 golden: observe-stop must refuse a dirty tree (the deployment's one true positive)"
    )


def test_ledger_ingestion_produces_replayable_candidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", (tmp_path / "state").as_posix())
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "ledger_for_ingest", REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ledger = module.open_ledger(cwd=repo)
    try:
        ledger.append({"event_type": "mutation", "tool_name": "Bash", "extra": {"command": "touch x"}})
        ledger.append({"event_type": "mutation", "tool_name": "Edit", "paths": ["src/a.py"]})
        ledger.append({"event_type": "mutation", "tool_name": "mcp__x__y", "extra": {}})
        ledger.append({"event_type": "gate_decision", "extra": {"verdict": "allow"}})
    finally:
        ledger.close()
    candidates, skipped = replay.ingest_ledger(repo)
    assert len(candidates) == 2, "Bash command and Edit path are reconstructable"
    assert skipped == 1, "digest-only events are counted as non-replayable (recorder-gap finding)"
    assert all(candidate["label"] == "recorded" for candidate in candidates)


def test_cli_replay_runs_and_reports(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "aegis_foundation.cli", "replay",
            "--corpus", (REPO_ROOT / "tests" / "fixtures" / "replay" / "must-allow.jsonl").as_posix(),
            "--work-dir", (tmp_path / "work").as_posix(),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Result: PASS" in result.stdout


def test_cli_replay_fails_on_regression(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps(
            {
                "id": "REG-1",
                "label": "must_allow",
                "state": "blocked_strict",
                "hook": "pretooluse",
                "payload": {"tool_name": "Bash", "tool_input": {"command": "git checkout -b feat/task-1-x"}},
                "notes": "deliberately mislabeled: blocked mutation as must_allow",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable, "-m", "aegis_foundation.cli", "replay",
            "--corpus", bad.as_posix(), "--work-dir", (tmp_path / "work").as_posix(),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "REGRESSION" in result.stdout
