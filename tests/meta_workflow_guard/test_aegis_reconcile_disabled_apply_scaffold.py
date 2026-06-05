"""Disabled reconcile apply scaffold tests."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_foundation.reconcile_apply_scaffold import (
    FIRST_APPLY_CLASS_KEY,
    KILL_SWITCH_AGENT_ORIGINS,
    SELECTED_APPLY_CHANNEL,
    SELECTED_APPLY_CHANNEL_OPERATOR_IDENTITY,
    ApplyCandidate,
    ApplyScaffoldError,
    authorization_binding_for,
    build_kill_switch_control_plane_state,
    build_apply_audit_record,
    build_post_merge_ci_apply_confirmation,
    evaluate_approved_context,
    evaluate_kill_switch,
    evaluate_kill_switch_control_action,
    evaluate_selected_apply_channel_confirmation,
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
POST_MERGE_CI_ENV = {
    "GITHUB_RUN_ID": "123",
    "GITHUB_RUN_ATTEMPT": "1",
    "GITHUB_WORKFLOW": "reconcile-apply",
    "GITHUB_REPOSITORY": "loucmane/codex-starter-pack",
    "GITHUB_SHA": "a" * 40,
    "GITHUB_EVENT_NAME": "push",
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_REF_NAME": "main",
}
ENABLE_SHAPED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
}
FUTURE_KILL_SWITCH_EXPIRY = "2026-06-05T13:00:00Z"
PAST_KILL_SWITCH_EXPIRY = "2026-06-05T11:00:00Z"
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
    for surface in (
        REPO_ROOT / "aegis_foundation" / "cli.py",
        REPO_ROOT / "aegis_mcp" / "server.py",
        REPO_ROOT / "scripts" / "codex-task",
    ):
        source = surface.read_text(encoding="utf-8")
        assert "build_post_merge_ci_apply_confirmation" not in source
        assert "evaluate_selected_apply_channel_confirmation" not in source
        assert "run_selected_channel_apply_with_process_oracle" not in source
        assert "build_kill_switch_control_plane_state" not in source
        assert "evaluate_kill_switch_control_action" not in source


def test_kill_switch_control_plane_is_absent_from_agent_writable_surfaces() -> None:
    forbidden_helpers = (
        "build_kill_switch_control_plane_state",
        "evaluate_kill_switch_control_action",
    )
    surfaces = [
        REPO_ROOT / "aegis_foundation" / "cli.py",
        REPO_ROOT / "aegis_mcp" / "server.py",
        REPO_ROOT / "scripts" / "codex-task",
        REPO_ROOT / "aegis_foundation" / "resources.py",
        REPO_ROOT / "aegis_foundation" / "reconcile_shadow_apply.py",
        REPO_ROOT / "aegis_foundation" / "reconcile_shadow_precision.py",
        *(REPO_ROOT / ".github" / "workflows").glob("*.yml"),
        *(REPO_ROOT / ".claude" / "scripts").glob("*.sh"),
        *(REPO_ROOT / ".claude" / "scripts").glob("*.py"),
    ]

    for surface in surfaces:
        source = surface.read_text(encoding="utf-8")
        for helper in forbidden_helpers:
            assert helper not in source, surface


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


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (
            build_kill_switch_control_plane_state(
                global_enabled=True,
                class_enabled=True,
                expires_at=PAST_KILL_SWITCH_EXPIRY,
            ),
            "kill_switch_stale",
        ),
        (
            build_kill_switch_control_plane_state(
                class_key="other/proof",
                global_enabled=True,
                class_enabled=True,
                expires_at=FUTURE_KILL_SWITCH_EXPIRY,
            ),
            "kill_switch_wrong_class",
        ),
        (
            {
                **build_kill_switch_control_plane_state(
                    global_enabled=True,
                    class_enabled=True,
                    expires_at=FUTURE_KILL_SWITCH_EXPIRY,
                ),
                "record_type": "unexpected",
            },
            "kill_switch_corrupt",
        ),
    ],
)
def test_durable_kill_switch_control_plane_refuses_bad_state(state, reason: str) -> None:
    decision = evaluate_kill_switch(state, now="2026-06-05T12:00:00Z")

    assert decision.enabled is False
    assert decision.reason == reason


def test_durable_kill_switch_disable_precedence_over_enable_shape() -> None:
    global_disabled = build_kill_switch_control_plane_state(
        global_enabled=True,
        class_enabled=True,
        global_disabled=True,
        expires_at=PAST_KILL_SWITCH_EXPIRY,
    )
    class_disabled = build_kill_switch_control_plane_state(
        global_enabled=True,
        class_enabled=True,
        class_disabled=True,
        expires_at=PAST_KILL_SWITCH_EXPIRY,
    )

    assert (
        evaluate_kill_switch(global_disabled, now="2026-06-05T12:00:00Z").reason
        == "kill_switch_global_disabled"
    )
    assert (
        evaluate_kill_switch(class_disabled, now="2026-06-05T12:00:00Z").reason
        == "kill_switch_class_disabled"
    )


@pytest.mark.parametrize("origin", sorted(KILL_SWITCH_AGENT_ORIGINS))
@pytest.mark.parametrize("action", ["enable", "clear_terminal"])
def test_agent_originated_control_plane_actions_are_refused(origin: str, action: str) -> None:
    decision = evaluate_kill_switch_control_action(
        {"action": action, "class_key": FIRST_APPLY_CLASS_KEY, "origin": origin}
    )

    assert decision.allowed is False
    assert decision.reason == "kill_switch_control_agent_originated_refused"


def test_kill_switch_enable_remains_unsatisfiable_for_approved_non_agent_origin() -> None:
    decision = evaluate_kill_switch_control_action(
        {
            "action": "enable",
            "class_key": FIRST_APPLY_CLASS_KEY,
            "origin": "approved_non_agent_channel",
            "operator_approval_id": "operator-approved-173",
        }
    )

    assert decision.allowed is False
    assert decision.reason == "enable_gate_unsatisfiable"


def test_emergency_disable_is_the_only_default_authorized_control_action() -> None:
    decision = evaluate_kill_switch_control_action(
        {
            "action": "disable",
            "class_key": FIRST_APPLY_CLASS_KEY,
            "origin": "approved_non_agent_channel",
        }
    )

    assert decision.allowed is True
    assert decision.reason == "kill_switch_disable_authorized"


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


def test_selected_post_merge_ci_confirmation_is_bound_but_unsatisfiable_by_default() -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)
    confirmation = _selected_channel_confirmation(candidate)

    decision = evaluate_selected_apply_channel_confirmation(
        confirmation,
        candidate=candidate,
        now="2026-06-05T12:00:00Z",
    )

    assert decision.approved is False
    assert decision.reason == "enable_gate_unsatisfiable"
    assert decision.channel == SELECTED_APPLY_CHANNEL
    assert decision.proof_id == confirmation["proof_id"]
    assert decision.idempotency_key == confirmation["idempotency_key"]
    assert decision.audit_destination == confirmation["audit_destination"]

    isolated_positive = evaluate_selected_apply_channel_confirmation(
        confirmation,
        candidate=candidate,
        now="2026-06-05T12:00:00Z",
        enable_gate_open=True,
    )
    assert isolated_positive.approved is True
    assert isolated_positive.reason == "selected_channel_confirmation_verified"


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (lambda proof: None, "selected_channel_confirmation_missing"),
        (lambda proof: "not-a-mapping", "selected_channel_confirmation_malformed"),
        (
            lambda proof: {**proof, "expires_at": "2026-06-05T11:59:59Z"},
            "selected_channel_confirmation_stale",
        ),
        (
            lambda proof: {
                **proof,
                "ci": {
                    **proof["ci"],
                    "event_name": "pull_request",
                    "ref": "refs/pull/172/merge",
                    "ref_name": "172/merge",
                },
            },
            "selected_channel_pr_shaped_refused",
        ),
        (
            lambda proof: {**proof, "ci": {**proof["ci"], "ref": "refs/heads/feature"}},
            "selected_channel_wrong_ref",
        ),
        (
            lambda proof: {**proof, "task_id": "99"},
            "approved_context_binding_mismatch",
        ),
        (
            lambda proof: {**proof, "proof": "github_pr_merged"},
            "approved_context_binding_mismatch",
        ),
        (
            lambda proof: {**proof, "finding_kind": "done_but_not_merged"},
            "selected_channel_binding_mismatch",
        ),
        (
            lambda proof: {**proof, "candidate_class": "done_but_not_merged/git_ancestor"},
            "selected_channel_candidate_class_mismatch",
        ),
        (
            lambda proof: {**proof, "operator_identity": "governed-agent"},
            "selected_channel_operator_identity_mismatch",
        ),
        (
            lambda proof: {**proof, "proof_artifact": {}},
            "selected_channel_confirmation_malformed",
        ),
        (
            lambda proof: {**proof, "idempotency_key": "wrong"},
            "selected_channel_idempotency_mismatch",
        ),
        (
            lambda proof: {**proof, "audit_destination": "/tmp/other"},
            "selected_channel_audit_destination_mismatch",
        ),
        (
            lambda proof: {**proof, "ci": {**proof["ci"], "run_id": ""}},
            "selected_channel_confirmation_malformed",
        ),
        (
            lambda proof: {**proof, "agent_originated": True},
            "selected_channel_agent_originated_refused",
        ),
        (
            lambda proof: {**proof, "origin": "mcp"},
            "selected_channel_agent_originated_refused",
        ),
    ],
)
def test_selected_post_merge_ci_confirmation_rejects_forged_shapes(mutator, reason: str) -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)
    confirmation = _selected_channel_confirmation(candidate)

    decision = evaluate_selected_apply_channel_confirmation(
        mutator(confirmation),
        candidate=candidate,
        now="2026-06-05T12:00:00Z",
        enable_gate_open=True,
    )

    assert decision.approved is False
    assert decision.reason == reason


def test_selected_post_merge_ci_confirmation_replay_refuses_by_idempotency_key() -> None:
    candidate = ApplyCandidate.from_mapping(FIRST_CANDIDATE)
    confirmation = _selected_channel_confirmation(candidate)

    decision = evaluate_selected_apply_channel_confirmation(
        confirmation,
        candidate=candidate,
        now="2026-06-05T12:00:00Z",
        claimed_idempotency_keys={confirmation["idempotency_key"]},
        enable_gate_open=True,
    )

    assert decision.approved is False
    assert decision.reason == "selected_channel_replay_refused"


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
        toolchain_evidence={"task_master": {"version": "0.43.1"}},
        predicted_delta_paths=(".taskmaster/tasks/tasks.json", ".taskmaster/tasks/task_042.md"),
        actual_delta_paths=(),
        before_hashes={".taskmaster/tasks/tasks.json": "before-hash"},
        after_hashes={},
        outcome="started",
        rollback_state={"rolled_back": False},
        semantic_validation={"passed": True, "reason": "matches_prediction"},
        channel_identity={
            "channel": SELECTED_APPLY_CHANNEL,
            "operator_identity": SELECTED_APPLY_CHANNEL_OPERATOR_IDENTITY,
            "proof_id": "run-123",
        },
        audit_destination=(
            "$RUNNER_TEMP/aegis-apply-audit/123/42/"
            "4f0febcc1df3926bdc08d18c4c35d5b0dcb5a6a40356a5fb12d8b74277c88e43/"
        ),
    )

    assert record["record_type"] == "reconcile_apply_audit"
    assert record["authorization_binding"] == binding
    assert record["approved_context_proof_id"] == "run-123"
    assert record["external_anchor"] == "github-actions://run/123"
    assert record["task_id"] == "42"
    assert record["finding_kind"] == "merged_but_not_done"
    assert record["proof"] == "git_ancestor"
    assert record["proof_artifact"] == PROOF_ARTIFACT
    assert record["toolchain_evidence"]["task_master"]["version"] == "0.43.1"
    assert record["predicted_delta_paths"] == [
        ".taskmaster/tasks/tasks.json",
        ".taskmaster/tasks/task_042.md",
    ]
    assert record["actual_delta_paths"] == []
    assert record["allowed_delta_hashes"] == ALLOWED_DELTA_HASHES
    assert record["before_hashes"] == {".taskmaster/tasks/tasks.json": "before-hash"}
    assert record["after_hashes"] == {}
    assert record["semantic_validation"] == {"passed": True, "reason": "matches_prediction"}
    assert record["rollback_handle_ref"] == "rollback://task-42"
    assert record["rollback_state"] == {"rolled_back": False}
    assert record["rolled_back"] is False
    assert record["idempotency_key"]
    assert record["previous_hash"]
    assert record["chain_hash"]
    assert record["outcome"] == "started"
    assert record["channel_identity"]["channel"] == SELECTED_APPLY_CHANNEL
    assert record["channel_identity"]["operator_identity"] == (
        SELECTED_APPLY_CHANNEL_OPERATOR_IDENTITY
    )
    assert record["audit_destination"].startswith("$RUNNER_TEMP/aegis-apply-audit/")

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


def _selected_channel_confirmation(candidate: ApplyCandidate) -> dict:
    idempotency_key = idempotency_key_for(
        task_id=candidate.task_id,
        finding_kind=candidate.finding_kind,
        proof=candidate.proof,
        proof_artifact=PROOF_ARTIFACT,
    )
    return build_post_merge_ci_apply_confirmation(
        POST_MERGE_CI_ENV,
        candidate=candidate,
        proof_artifact=PROOF_ARTIFACT,
        audit_destination=(
            f"$RUNNER_TEMP/aegis-apply-audit/123/{candidate.task_id}/{idempotency_key}/"
        ),
        expires_at="2026-06-05T12:05:00Z",
    )
