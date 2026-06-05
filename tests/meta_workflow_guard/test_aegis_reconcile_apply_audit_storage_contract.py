"""Contract tests for the Task 170 reconcile apply audit boundary."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-apply-audit-storage-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"

REMAINING_OPEN_GATES = {"G5", "G8"}


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _gate_status() -> dict[str, object]:
    return json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))


def test_audit_storage_contract_closes_only_g7_and_remains_no_go() -> None:
    contract = _contract()
    status = _gate_status()

    assert "**Status:** active Task 170 contract." in contract
    assert "**Closes:** G7: Audit Storage, Retention, And Review Boundary." in contract
    assert "**Verdict:** G7 closed; NO-GO remains for any first guarded apply task." in contract
    assert "This task does not add an apply channel" in contract
    assert "does not select the approved invocation channel" in contract
    assert status["record_type"] == "reconcile_enablement_gate_status"
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "174"

    gates = status["gates"]
    assert set(gates) == {*REMAINING_OPEN_GATES, "G1", "G2", "G3", "G4", "G6", "G7"}
    assert gates["G1"]["status"] == "closed"
    assert gates["G1"]["closed_by_task"] == "171"
    assert gates["G2"]["status"] == "closed"
    assert gates["G2"]["closed_by_task"] == "173"
    assert gates["G3"]["status"] == "closed"
    assert gates["G3"]["closed_by_task"] == "173"
    assert gates["G4"]["status"] == "closed"
    assert gates["G4"]["closed_by_task"] == "172"
    assert gates["G6"]["status"] == "closed"
    assert gates["G6"]["closed_by_task"] == "174"
    assert gates["G7"]["status"] == "closed"
    assert gates["G7"]["closed_by_task"] == "170"
    for gate in REMAINING_OPEN_GATES:
        assert gates[gate]["status"] == "open"
        assert gates[gate]["blocking"] is True


def test_audit_storage_contract_defines_destinations_and_allowed_paths() -> None:
    contract = _contract()

    for snippet in (
        "$RUNNER_TEMP/aegis-apply-audit/<run-id>/<task-id>/<idempotency-key>/",
        "$XDG_STATE_HOME/aegis/reconcile-apply/audit/<repo-id>/<task-id>/<idempotency-key>/",
        "isolated test fixture roots under the platform temp directory",
        "Allowed out-of-Taskmaster report paths",
        "channel-confirmation.json",
        "apply-audit.jsonl",
        "rollback-handle.json",
        "terminal-rollback-failure.json",
        "review-summary.json",
    ):
        assert snippet in contract

    for forbidden_path in (
        ".taskmaster/tasks/**",
        ".taskmaster/state.json",
        ".aegis/state/**",
        "docs/ai/work-tracking/**",
        "sessions/**",
        "plans/**",
        "git refs",
    ):
        assert forbidden_path in contract


def test_audit_storage_contract_requires_before_audit_before_mutation() -> None:
    contract = _contract()

    assert "The before-audit breadcrumb is load-bearing" in contract
    assert "persist the before-audit record to the audit root" in contract
    assert "only after step 3 succeeds may any Taskmaster status write run" in contract
    assert "If the before-audit record cannot be written, mutation is blocked" in contract
    assert "before any Taskmaster status write" in contract


def test_audit_storage_contract_lists_required_audit_bindings() -> None:
    contract = _contract()

    for field in (
        "`task_id`",
        "`finding_kind`",
        "`proof`",
        "`proof_artifact`",
        "`approved_context_proof_id`",
        "`authorization_binding`",
        "`external_anchor`",
        "`toolchain_evidence`",
        "`predicted_delta_paths`",
        "`actual_delta_paths`",
        "`allowed_delta_hashes`",
        "`before_hashes`",
        "`after_hashes`",
        "`semantic_validation`",
        "`rollback_handle_ref`",
        "`rollback_state`",
        "`rolled_back`",
        "`idempotency_key`",
        "`previous_hash`",
        "`chain_hash`",
        "`outcome`",
    ):
        assert field in contract

    assert "authorization_binding" in contract
    assert "exact task id, finding kind, proof, and proof artifact" in contract
    assert "record that omits any binding field is not valid enablement evidence" in contract


def test_audit_storage_contract_defines_retention_review_and_alerting() -> None:
    contract = _contract()

    assert "Minimum retention is 90 days" in contract
    assert "Terminal rollback failure artifacts must be retained" in contract
    assert "download the audit artifact bundle" in contract
    assert "verify the `apply-audit.jsonl` hash chain" in contract
    assert "apply fired" in contract
    assert "rollback executed" in contract
    assert "terminal rollback failure entered" in contract
    assert "Audit storage is not a substitute for alerting" in contract


def test_gate_status_marker_is_machine_readable_and_points_to_evidence() -> None:
    status = _gate_status()
    marker = status["closed_gate_markers"]["G7"]

    assert marker["status"] == "closed"
    assert marker["marker"] == "audit_storage_retention_review_boundary_closed"
    assert marker["closed_by_task"] == "170"
    assert "docs/aegis/reconcile-apply-audit-storage-contract.md" in marker["evidence"]
    assert (
        "tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::"
        "test_before_audit_write_failure_blocks_taskmaster_status_write" in marker["evidence"]
    )
