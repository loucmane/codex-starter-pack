"""Contract tests for the selected-channel live apply-time oracle gate."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-apply-live-oracle-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"


def test_live_oracle_contract_closes_g4_but_keeps_no_go() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    status = json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))

    assert "**Closes:** G4: Live Apply-Time Side-Effect Oracle Gate." in contract
    assert "**Verdict:** G4 closed; NO-GO remains" in contract
    assert status["gates"]["G4"]["status"] == "closed"
    assert status["gates"]["G4"]["closed_by_task"] == "172"
    assert status["first_guarded_apply_task_allowed"] is False


def test_live_oracle_contract_keeps_selected_wrapper_internal_and_default_off() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "run_selected_channel_apply_with_process_oracle" in contract
    assert "internal Python helper, not an entrypoint" in contract
    assert "refuse by default while the enable gate is unsatisfiable" in contract
    for forbidden in (
        "No apply or apply-like command.",
        "No post-merge apply workflow.",
        "No MCP apply tool.",
        "No agent-reachable enablement path.",
        "No new candidate class.",
        "No Taskmaster status mutation against the governed repository.",
    ):
        assert forbidden in contract


def test_live_oracle_contract_pins_delta_and_audit_boundaries() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "snapshot the governed repository immediately before and after" in contract
    assert "No `.aegis`, work-tracking, source, plan, session, workflow-state" in contract
    assert "channel-confirmation.json" in contract
    assert "apply-audit.jsonl" in contract
    assert "process-oracle.json" in contract
    assert "selected channel identity" in contract
    assert "selected audit destination" in contract


def test_live_oracle_contract_requires_precision_validated_toolchain_baseline() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "`evidence_role: validated_ci_baseline`" in contract
    assert "source-controlled precision-validated baseline" in contract
    assert "Comparing two live captures to each other is not valid" in contract
    assert "refuses before fresh validation, idempotency claim, audit, or write" in contract


def test_live_oracle_contract_lists_only_remaining_open_gates() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for gate in (
        "G5: Enablement Evidence Decision Packet",
        "G8: Final Agent-Surface Regression With The Selected Channel Present",
    ):
        assert gate in contract
    remaining = contract.split("## Remaining Open Gates", 1)[1]
    assert "G2: Agent-Excluded Enablement Mechanism" not in remaining
    assert "G3: Kill-Switch Enablement And Disable Semantics" not in remaining
    assert "G4: Live Apply-Time Side-Effect Oracle Gate" not in remaining
    assert "G6: Terminal Rollback Failure Operator Resolution" not in remaining
