"""Contract tests for the Task 171 approved apply channel boundary."""

from __future__ import annotations

import json

from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-apply-approved-channel-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"

REMAINING_OPEN_GATES = {"G5", "G6", "G8"}


def _contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _gate_status() -> dict[str, object]:
    return json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))


def test_approved_channel_contract_closes_only_g1_and_remains_no_go() -> None:
    contract = _contract()
    status = _gate_status()

    assert "**Status:** active Task 171 contract." in contract
    assert "**Closes:** G1: Approved Invocation And Confirmation Channel." in contract
    assert "**Verdict:** G1 closed; NO-GO remains for any first guarded apply task." in contract
    assert "**Selected first channel:** post-merge GitHub Actions on `refs/heads/main`." in contract
    assert "This task does not add a post-merge apply workflow" in contract
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "173"
    assert status["gates"]["G1"]["status"] == "closed"
    assert status["gates"]["G1"]["closed_by_task"] == "171"
    assert status["gates"]["G1"]["selected_channel"] == "post_merge_ci"
    assert status["gates"]["G2"]["status"] == "closed"
    assert status["gates"]["G2"]["closed_by_task"] == "173"
    assert status["gates"]["G3"]["status"] == "closed"
    assert status["gates"]["G3"]["closed_by_task"] == "173"
    assert status["gates"]["G4"]["status"] == "closed"
    assert status["gates"]["G4"]["closed_by_task"] == "172"
    assert status["gates"]["G7"]["status"] == "closed"
    for gate in REMAINING_OPEN_GATES:
        assert status["gates"][gate]["status"] == "open"
        assert status["gates"][gate]["blocking"] is True


def test_approved_channel_contract_selects_post_merge_ci_shape() -> None:
    contract = _contract()

    for snippet in (
        "provider: GitHub Actions",
        "event: `push`",
        "ref: `refs/heads/main`",
        "`github_actions_protected_main`",
        "candidate class: `merged_but_not_done/git_ancestor`",
        "Task 170 `$RUNNER_TEMP/aegis-apply-audit/...` destination",
        "`operator_controlled_local` remains a recognized future context family",
        "but it is not the selected first channel",
    ):
        assert snippet in contract


def test_approved_channel_contract_lists_required_confirmation_fields() -> None:
    contract = _contract()

    for field in (
        "`context_type: post_merge_ci`",
        "`selected_channel: post_merge_ci`",
        "`proof_id`",
        "`task_id`",
        "`finding_kind`",
        "`proof`",
        "`candidate_class`",
        "`proof_artifact`",
        "`idempotency_key`",
        "`audit_destination`",
        "`operator_identity: github_actions_protected_main`",
        "`external_anchor`",
        "`expires_at`",
        "`agent_originated: false`",
        "`ci.run_id`",
        "`ci.run_attempt`",
        "`ci.workflow`",
        "`ci.repository`",
        "`ci.sha`",
        "`ci.event_name`",
        "`ci.ref`",
        "`ci.ref_name`",
    ):
        assert field in contract

    assert "must derive from the task id, finding kind, proof, and proof artifact" in contract
    assert "must include the Task 170 audit root, the task id, and the idempotency key" in contract


def test_approved_channel_contract_lists_refusal_and_replay_requirements() -> None:
    contract = _contract()

    for refusal in (
        "missing confirmation",
        "malformed confirmation",
        "stale confirmation",
        "PR-shaped confirmation",
        "wrong ref",
        "wrong task",
        "wrong proof",
        "wrong finding kind",
        "wrong candidate class",
        "wrong operator identity",
        "idempotency mismatch",
        "replayed idempotency key",
        "audit destination mismatch",
        "governed-agent-originated confirmation",
    ):
        assert refusal in contract

    assert "Two approved invocations of the same candidate must not both fire" in contract
    assert "claim that key atomically before any live write" in contract
    assert "returns `enable_gate_unsatisfiable`" in contract


def test_approved_channel_contract_binds_channel_identity_to_task170_audit() -> None:
    contract = _contract()

    assert (
        "`channel-confirmation.json` stores the full selected-channel confirmation artifact"
        in contract
    )
    assert "`apply-audit.jsonl` records the selected channel identity" in contract
    assert (
        "the before-audit record must still be durable before any Taskmaster status write"
        in contract
    )
    assert "the audit destination remains outside mutable Taskmaster files" in contract


def test_approved_channel_contract_preserves_non_goals() -> None:
    contract = _contract()

    for forbidden in (
        "No apply or apply-like command.",
        "No post-merge apply workflow.",
        "No operator-local apply command.",
        "No production approved context that can mutate.",
        "No kill-switch flip.",
        "No MCP apply tool.",
        "No package CLI apply flag.",
        "No `scripts/codex-task` apply route.",
        "No agent-reachable enablement path.",
        "No new candidate class.",
        "No Taskmaster status mutation against the governed repository.",
    ):
        assert forbidden in contract
