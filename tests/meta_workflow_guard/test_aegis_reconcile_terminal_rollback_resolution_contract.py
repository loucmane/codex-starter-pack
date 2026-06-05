"""Contract tests for the Task 174 terminal rollback resolution boundary."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-terminal-rollback-resolution-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"

REMAINING_OPEN_GATES = {"G5", "G8"}


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _gate_status() -> dict[str, object]:
    return json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))


def test_terminal_resolution_contract_closes_g6_and_keeps_no_go() -> None:
    contract = _contract()
    status = _gate_status()

    assert "**Status:** active Task 174 contract." in contract
    assert "**Closes:** G6: Terminal Rollback Failure Operator Resolution." in contract
    assert "**Verdict:** G6 closed; NO-GO remains" in contract
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "174"
    assert status["gates"]["G6"]["status"] == "closed"
    assert status["gates"]["G6"]["closed_by_task"] == "174"
    assert status["gates"]["G6"]["contract"] == (
        "docs/aegis/reconcile-terminal-rollback-resolution-contract.md"
    )
    for gate in REMAINING_OPEN_GATES:
        assert status["gates"][gate]["status"] == "open"
        assert status["gates"][gate]["blocking"] is True


def test_terminal_resolution_contract_defines_terminal_record_and_manual_procedure() -> None:
    contract = _contract()

    for field in (
        "`record_type: reconcile_apply_terminal_rollback_failure`",
        "`audit_linked: true`",
        "`operator_resolution_required: true`",
        "`auto_clear_allowed: false`",
        "`auto_retry_allowed: false`",
        "`chain_hash`",
    ):
        assert field in contract

    for step in (
        "Stop all reconcile apply attempts",
        "Download the Task 170 audit bundle",
        "Verify the audit hash chain",
        "Inspect the governed repository manually",
        "Record a `reconcile_apply_terminal_rollback_resolution` proof",
        "does not implement the clearing writer",
    ):
        assert step in contract


def test_terminal_resolution_contract_pins_resolution_proof_and_refusals() -> None:
    contract = _contract()

    for field in (
        "`record_type: reconcile_apply_terminal_rollback_resolution`",
        "`action: clear_terminal`",
        "`class_key: merged_but_not_done/git_ancestor`",
        "`terminal_chain_hash`",
        "`operator_approval_id`",
        "`audit_destination`",
        "`manual_resolution_summary`",
        "`agent_originated: false`",
        "`expires_at`",
    ):
        assert field in contract

    for refusal in (
        "missing",
        "malformed",
        "stale",
        "replayed",
        "wrong-class",
        "mismatched to the terminal breadcrumb",
        "missing operator approval",
        "missing the terminal audit destination",
        "governed-agent-originated",
        "`terminal_resolution_gate_unsatisfiable`",
    ):
        assert refusal in contract


def test_terminal_resolution_contract_preserves_agent_exclusion_and_non_goals() -> None:
    contract = _contract()

    for surface in (
        "MCP",
        "package CLI",
        "`scripts/codex-task`",
        "hooks",
        "environment variables",
        "config files",
        "workflow state",
        "reports",
        "repair/start/kickoff paths",
    ):
        assert surface in contract

    for forbidden in (
        "No live apply.",
        "No automatic repair.",
        "No agent-cleared terminal state.",
        "No terminal-state clearing writer.",
        "No kill-switch flip to enabled.",
        "No operator-local apply command.",
        "No MCP apply tool.",
        "No post-merge apply workflow.",
        "No new candidate class.",
        "No Taskmaster status mutation against the governed repository.",
    ):
        assert forbidden in contract
