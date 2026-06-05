"""Contract tests for the Task 173 kill-switch control plane."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-apply-kill-switch-control-plane-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"

REMAINING_OPEN_GATES = {"G5", "G6", "G8"}


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _gate_status() -> dict[str, object]:
    return json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))


def test_kill_switch_contract_closes_g2_g3_and_keeps_no_go() -> None:
    contract = _contract()
    status = _gate_status()

    assert "**Status:** active Task 173 contract." in contract
    assert "G2: Agent-Excluded Enablement Mechanism" in contract
    assert "G3: Kill-Switch Enablement And Disable Semantics" in contract
    assert "**Verdict:** G2 and G3 closed; NO-GO remains" in contract
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "173"
    assert status["gates"]["G2"]["status"] == "closed"
    assert status["gates"]["G2"]["closed_by_task"] == "173"
    assert status["gates"]["G3"]["status"] == "closed"
    assert status["gates"]["G3"]["closed_by_task"] == "173"
    for gate in REMAINING_OPEN_GATES:
        assert status["gates"][gate]["status"] == "open"
        assert status["gates"][gate]["blocking"] is True


def test_kill_switch_contract_defines_durable_state_shape_and_refusals() -> None:
    contract = _contract()

    for field in (
        "`record_type: reconcile_apply_kill_switch_control_plane`",
        "`version: 1`",
        "`expires_at`",
        "`writer.origin`",
        "`global.enabled`",
        "`global.disabled`",
        "`classes.<class-key>.class_key`",
        "`classes.<class-key>.enabled`",
        "`classes.<class-key>.disabled`",
    ):
        assert field in contract

    for refusal in (
        "missing state",
        "corrupt state",
        "unreadable state",
        "stale state",
        "wrong-class state",
        "global disabled",
        "class disabled",
        "before clone, validation, idempotency, audit, or write work",
    ):
        assert refusal in contract


def test_kill_switch_contract_preserves_agent_exclusion_and_default_off() -> None:
    contract = _contract()

    assert "exposes no writer or entrypoint" in contract
    assert "returns `enable_gate_unsatisfiable`" in contract
    assert "Default local and CI state therefore remain zero-delta" in contract
    for surface in (
        "MCP",
        "package CLI",
        "`scripts/codex-task`",
        "hooks",
        "environment variables",
        "config files",
        "workflow state",
        "reports",
    ):
        assert surface in contract
    assert "Emergency disable may be authorized only from an approved non-agent origin" in contract
    assert "Clearing terminal rollback state remains gated by the future G6" in contract


def test_kill_switch_contract_preserves_non_goals() -> None:
    contract = _contract()

    for forbidden in (
        "No apply or apply-like command.",
        "No kill-switch flip to enabled.",
        "No live apply.",
        "No operator-local apply command.",
        "No MCP apply tool.",
        "No post-merge apply workflow.",
        "No production approved context that can mutate.",
        "No new candidate class.",
        "No Taskmaster status mutation against the governed repository.",
    ):
        assert forbidden in contract
