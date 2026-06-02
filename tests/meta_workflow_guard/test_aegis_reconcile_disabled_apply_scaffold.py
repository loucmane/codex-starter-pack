"""Disabled reconcile apply scaffold tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_CLASS_KEY,
    ApplyCandidate,
    ApplyScaffoldError,
    authorization_binding_for,
    build_apply_audit_record,
    evaluate_approved_context,
    evaluate_kill_switch,
    idempotency_key_for,
    load_kill_switch_state,
    run_disabled_apply_scaffold,
)
from aegis_mcp.server import AegisMCPConfig, create_server
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import (
    RECONCILE_MUTATION_FLAGS,
    REPO_ROOT,
    load_task_module,
)
from tests.meta_workflow_guard.test_aegis_mcp_server import (
    RECONCILE_MUTATION_PARAMETER_NAMES,
    list_tools,
    tool_by_name,
)
from tests.meta_workflow_guard.test_aegis_reconcile_precision_corpus import CORPUS_CASES

FIRST_CANDIDATE = {
    "task_id": "42",
    "finding_kind": "merged_but_not_done",
    "proof": "git_ancestor",
    "current_status": "pending",
    "proposed_status": "done",
}
FUTURE_CI_CONTEXT = {
    "context_type": "post_merge_ci",
    "proof_id": "run-123",
    "task_id": "42",
    "proof": "git_ancestor",
}
ENABLE_SHAPED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
}
PROOF_ARTIFACT = {"merge_commit": "abc123", "ancestor": True}
ALLOWED_DELTA_HASHES = {
    ".taskmaster/tasks/tasks.json": "before:aaa after:bbb",
    ".taskmaster/tasks/task_042.md": "before:ccc after:ddd",
}


@pytest.mark.parametrize("case", CORPUS_CASES, ids=lambda case: case.case_id)
def test_disabled_apply_scaffold_has_zero_side_effects_across_precision_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case,
) -> None:
    target = tmp_path / case.case_id
    case.setup(target, monkeypatch)
    before = snapshot_whole_tree(target)

    result = run_disabled_apply_scaffold(
        FIRST_CANDIDATE,
        approved_context_proof=FUTURE_CI_CONTEXT,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
    )

    assert result.status == "refused"
    assert result.enabled is False
    assert result.mutated is False
    before.assert_matches(snapshot_whole_tree(target))


@pytest.mark.parametrize(
    "context",
    [
        None,
        {},
        {"context_type": "post_merge_ci"},
        {"context_type": "operator_controlled_local", "proof_id": "operator-1"},
        FUTURE_CI_CONTEXT,
        {**FUTURE_CI_CONTEXT, "task_id": "99"},
        {**FUTURE_CI_CONTEXT, "proof": "github_pr_merged"},
    ],
)
def test_enable_gate_is_unsatisfiable_for_all_current_inputs(context: dict | None) -> None:
    result = run_disabled_apply_scaffold(
        FIRST_CANDIDATE,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
    )

    assert result.enabled is False
    assert result.mutated is False
    assert result.status == "refused"


def test_environment_variables_cannot_satisfy_enable_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_RECONCILE_APPLY_ENABLED", "1")
    monkeypatch.setenv("AEGIS_APPROVED_CONTEXT", "post_merge_ci")

    result = run_disabled_apply_scaffold(
        FIRST_CANDIDATE,
        approved_context_proof=FUTURE_CI_CONTEXT,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
    )

    assert result.enabled is False
    assert result.reason == "enable_gate_unsatisfiable"


def test_apply_scaffold_is_not_reachable_from_agent_surfaces(tmp_path: Path) -> None:
    codex_parser = load_task_module().build_parser()
    package_parser = aegis_cli.build_arg_parser()

    for flag in RECONCILE_MUTATION_FLAGS:
        with pytest.raises(SystemExit):
            codex_parser.parse_args(["aegis", "reconcile", flag])
        with pytest.raises(SystemExit):
            package_parser.parse_args(["reconcile", flag])

    server = create_server(
        AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    )
    tool_names = {tool.name for tool in list_tools(server)}
    assert "aegis.apply" not in tool_names
    assert "aegis.reconcile_apply" not in tool_names
    reconcile_tool = tool_by_name(server, "aegis.reconcile")
    assert set(reconcile_tool.inputSchema["properties"]).isdisjoint(
        RECONCILE_MUTATION_PARAMETER_NAMES
    )

    codex_task_source = (REPO_ROOT / "scripts/codex-task").read_text(encoding="utf-8")
    assert "run_disabled_apply_scaffold" not in codex_task_source


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (None, "kill_switch_missing"),
        ({}, "kill_switch_default_disabled"),
        ({"global": "yes"}, "kill_switch_corrupt"),
        ({"global": {}, "classes": "yes"}, "kill_switch_corrupt"),
    ],
)
def test_kill_switch_fail_closed_states(state, reason: str) -> None:
    decision = evaluate_kill_switch(state)

    assert decision.enabled is False
    assert decision.reason == reason


def test_kill_switch_load_fail_closed_states(tmp_path: Path) -> None:
    missing = load_kill_switch_state(tmp_path / "missing.json")
    assert evaluate_kill_switch(missing).reason == "kill_switch_missing"

    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{not-json", encoding="utf-8")
    corrupt = load_kill_switch_state(corrupt_path)
    assert evaluate_kill_switch(corrupt).reason == "kill_switch_corrupt"

    directory = tmp_path / "directory"
    directory.mkdir()
    unreadable = load_kill_switch_state(directory)
    assert evaluate_kill_switch(unreadable).reason == "kill_switch_unreadable"


def test_kill_switch_disable_precedence() -> None:
    global_disabled = {
        "global": {"enabled": True, "disabled": True},
        "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
    }
    class_disabled = {
        "global": {"enabled": True},
        "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True, "disabled": True}},
    }

    assert evaluate_kill_switch(global_disabled).reason == "kill_switch_global_disabled"
    assert evaluate_kill_switch(class_disabled).reason == "kill_switch_class_disabled"
    assert evaluate_kill_switch(ENABLE_SHAPED_KILL_SWITCH).reason == "enable_gate_unsatisfiable"


def test_approved_context_uses_positive_proof_and_defaults_denied() -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)

    assert evaluate_approved_context(None, candidate=candidate).reason == "approved_context_missing"
    assert (
        evaluate_approved_context(
            {"context_type": "unknown", "proof_id": "x"}, candidate=candidate
        ).reason
        == "approved_context_unknown"
    )
    assert (
        evaluate_approved_context(
            {**FUTURE_CI_CONTEXT, "task_id": "99"}, candidate=candidate
        ).reason
        == "approved_context_binding_mismatch"
    )
    decision = evaluate_approved_context(FUTURE_CI_CONTEXT, candidate=candidate)
    assert decision.approved is False
    assert decision.reason == "enable_gate_unsatisfiable"


def test_apply_audit_record_requires_transaction_fields_and_binding() -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)
    binding = authorization_binding_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=PROOF_ARTIFACT,
    )

    record = build_apply_audit_record(
        phase="before",
        candidate=candidate,
        proof_artifact=PROOF_ARTIFACT,
        allowed_delta_hashes=ALLOWED_DELTA_HASHES,
        approved_context_proof_id="run-123",
        authorization_binding=binding,
        rollback_handle_ref="rollback://task-42",
        rolled_back=False,
        eligibility_corpus_version="task146-v1",
        external_anchor="github-actions://run/123",
    )

    assert record["record_type"] == "reconcile_apply_audit"
    assert record["authorization_binding"] == binding
    assert record["approved_context_proof_id"] == "run-123"
    assert record["external_anchor"] == "github-actions://run/123"

    with pytest.raises(ApplyScaffoldError, match="authorization binding"):
        build_apply_audit_record(
            phase="before",
            candidate=candidate,
            proof_artifact=PROOF_ARTIFACT,
            allowed_delta_hashes=ALLOWED_DELTA_HASHES,
            approved_context_proof_id="run-123",
            authorization_binding="wrong",
            rollback_handle_ref="rollback://task-42",
            rolled_back=False,
            eligibility_corpus_version="task146-v1",
        )


def test_apply_audit_record_idempotency_and_chain_are_stable() -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)
    binding = authorization_binding_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=PROOF_ARTIFACT,
    )
    kwargs = {
        "phase": "before",
        "candidate": candidate,
        "proof_artifact": PROOF_ARTIFACT,
        "allowed_delta_hashes": ALLOWED_DELTA_HASHES,
        "approved_context_proof_id": "run-123",
        "authorization_binding": binding,
        "rollback_handle_ref": "rollback://task-42",
        "rolled_back": False,
        "eligibility_corpus_version": "task146-v1",
        "previous_hash": "a" * 64,
        "external_anchor": "github-actions://run/123",
    }

    first = build_apply_audit_record(**kwargs)
    second = build_apply_audit_record(**kwargs)

    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["chain_hash"] == second["chain_hash"]
    assert first["idempotency_key"] == idempotency_key_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=PROOF_ARTIFACT,
    )


def test_existing_writers_do_not_consume_disabled_scaffold() -> None:
    writer_functions = (
        "install",
        "repair",
        "start_local_work",
        "kickoff",
        "log_work",
        "verify",
        "closeout",
        "repair_handoff",
    )
    installer = __import__("scripts._aegis_installer", fromlist=list(writer_functions))

    for name in writer_functions:
        source = inspect.getsource(getattr(installer, name))
        assert "run_disabled_apply_scaffold" not in source
        assert "reconcile_apply_scaffold" not in source
