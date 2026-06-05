"""Contract tests for the reconcile enablement-readiness gate inventory."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-readiness-gates.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"


def test_enablement_readiness_contract_is_no_go_and_non_executing() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "**Status:** active Task 169 audit." in contract
    assert "**Verdict:** NO-GO for creating any first guarded apply task." in contract
    assert "This task does not enable apply" in contract
    assert "Task 170 closed the G7" in contract
    assert "Task 171 closed the G1" in contract
    assert "Task 172" in contract
    assert "Task 173 closed the G2/G3" in contract
    assert "Task 174 closed the G6" in contract
    assert "Task 175 closed the G8" in contract
    assert "Task 176 produced the G5" in contract
    assert "No first guarded apply task may be scoped unless G1-G8 are closed" in contract
    assert "explicit signed operator decision" in contract
    assert "No Taskmaster status mutation against the governed repository" in contract


def test_enablement_readiness_contract_lists_closed_standing_gates() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for closed_gate in (
        "Read-only reconcile promotion",
        "Agent-facing apply surface absent",
        "Single live writer caller",
        "Default config produces zero governed-repo delta",
        "Taskmaster authority is single-source in shadow and runtime checks",
        "Apply-time candidate freshness re-validation",
        "Semantic validation fails closed",
        "Terminal rollback failure freezes subsequent apply attempts",
        "Replayable precision corpus",
        "CI artifact transport under Node24 actions",
        "Audit storage, retention, and review boundary",
        "Approved invocation and confirmation channel",
        "Live apply-time side-effect oracle gate",
        "Agent-excluded enablement mechanism",
        "Kill-switch enablement and disable semantics",
        "Terminal rollback failure operator resolution",
        "Final agent-surface regression with the selected channel present",
    ):
        assert closed_gate in contract


def test_enablement_readiness_contract_lists_no_open_gates_but_keeps_packet_no_go() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "## Gate Packet Outcome Still Blocking Any First Guarded Apply Task" in contract
    assert "All G1-G8 markers are now closed" in contract
    assert "records `NO-GO`, not `GO`" in contract
    remaining = contract.split(
        "## Gate Packet Outcome Still Blocking Any First Guarded Apply Task", 1
    )[1]
    assert "G5: Enablement Evidence Decision Packet" in remaining
    assert "**Status:** closed by Task 176." in remaining
    assert "G2: Agent-Excluded Enablement Mechanism" not in remaining
    assert "G3: Kill-Switch Enablement And Disable Semantics" not in remaining
    assert "G6: Terminal Rollback Failure Operator Resolution" not in remaining
    assert "G8: Final Agent-Surface Regression With The Selected Channel Present" not in remaining
    assert "G1: Approved Invocation And Confirmation Channel" not in contract
    assert "G4: Live Apply-Time Side-Effect Oracle Gate" not in contract
    assert "G7: Audit Storage, Retention, And Review Boundary" not in contract
    assert "process-level oracle" in contract
    assert "terminal breadcrumbs are audit-linked" in contract
    assert "malformed/stale/PR-shaped/wrong/ref-task-proof/replayed/agent-originated" in contract


def test_enablement_readiness_contract_keeps_evidence_streams_non_interchangeable() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "precision corpus artifact as the precision basis" in contract
    assert "empty operational ledgers or cascade smoke as precision" in contract
    assert "operational post-merge runs are listed as inertness/context evidence only" in contract
    assert "the decision packet states that the evidence is not sufficient" in contract


def test_enablement_readiness_contract_has_current_gate_status_marker() -> None:
    status = json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))

    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "176"
    for gate_id in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"):
        assert status["gates"][gate_id]["status"] == "closed"
        assert status["gates"][gate_id]["blocking"] is False
    assert status["gates"]["G5"]["decision"] == "NO-GO"


def test_enablement_readiness_contract_preserves_future_non_goals() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for forbidden in (
        "No apply or apply-like command.",
        "No kill-switch flip.",
        "No production approved context.",
        "No MCP apply tool.",
        "No agent-reachable enablement path.",
        "No new candidate class.",
    ):
        assert forbidden in contract
