"""Shadow-mode reconcile apply artifact tests."""

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

import pytest
import yaml

from aegis_foundation import cli as aegis_cli
from aegis_foundation.reconcile_apply_scaffold import FIRST_APPLY_CLASS_KEY
from aegis_foundation.reconcile_shadow_apply import (
    SHADOW_ARTIFACT_NAME,
    build_ci_shadow_context_proof,
    build_shadow_record,
    build_shadow_report,
    validate_sacrificial_taskmaster_done_cascade,
    write_local_shadow_report,
)
from aegis_mcp.server import AegisMCPConfig, create_server
from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import reconcile
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import (
    RECONCILE_MUTATION_FLAGS,
    REPO_ROOT,
    commit_file,
    git,
    init_git_repo,
    load_task_module,
    write_taskmaster_tasks,
)
from tests.meta_workflow_guard.test_aegis_mcp_server import (
    RECONCILE_MUTATION_PARAMETER_NAMES,
    list_tools,
    tool_by_name,
)

ENABLE_SHAPED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True}},
}
DISABLED_KILL_SWITCH = {
    "global": {"enabled": True},
    "classes": {FIRST_APPLY_CLASS_KEY: {"enabled": True, "disabled": True}},
}
ACTION_SHAPED_KEYS = {
    "apply",
    "auto",
    "auto_fix",
    "cli",
    "command",
    "done",
    "fix",
    "mcp",
    "proposed_action",
    "push",
    "set_status",
    "status_transition",
    "tool",
    "write",
}
ACTION_SHAPED_VALUES = (
    "task-master set-status",
    "set-status",
    "aegis closeout",
    "git push",
    "gh pr",
    "--apply",
    "--auto",
    "--fix",
    "--set-status",
)


def _require_taskmaster_cli() -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is not available for the sacrificial cascade validation")


def test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas(
    tmp_path: Path,
) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-ci")
    candidate = _first_preview_candidate(target)
    context = _ci_context(candidate)
    before = snapshot_whole_tree(target)

    report = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )

    before.assert_matches(snapshot_whole_tree(target))
    assert report["artifact_mode"] == "ci"
    assert report["artifact_name"] == SHADOW_ARTIFACT_NAME
    assert report["shadow_refused"] == []
    record = report["would_apply"][0]
    assert record["decision"] == "would_apply"
    assert record["mode"] == "shadow"
    assert record["executed"] is False
    assert record["mutated_live_repo"] is False
    assert record["target_status"] == "done"
    assert record["sacrificial_delta_matches_prediction"] is True
    assert record["actual_sacrificial_delta_paths"] == record["predicted_blast_radius_paths"]
    assert record["clone_fidelity"]["detached"] is True
    assert all(record["clone_fidelity"]["relevant_paths_match"].values())
    assert set(record["rollback_baseline_metadata"]) == set(record["predicted_blast_radius_paths"])
    _assert_no_action_shape(report)

    second = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "second-clones",
    )
    assert (
        report["would_apply"][0]["idempotency_key"] == second["would_apply"][0]["idempotency_key"]
    )


def test_shadow_local_mode_writes_only_declared_report_path(tmp_path: Path) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-local")
    (target / ".aegis" / "reports").mkdir(parents=True)
    candidate = _first_preview_candidate(target)
    context = _ci_context(candidate)
    report_path = target / ".aegis" / "reports" / "reconcile-shadow-apply.json"
    before = snapshot_whole_tree(target)

    report = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="local",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )
    write_local_shadow_report(report, report_path)

    before.assert_matches(
        snapshot_whole_tree(target),
        allowed_deltas=[".aegis/reports/reconcile-shadow-apply.json"],
    )
    stored = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored["would_apply"][0]["mutated_live_repo"] is False


@pytest.mark.parametrize(
    "candidate",
    [
        {"task_id": "42", "finding_kind": "merged_but_not_done", "proof": "github_pr_merged"},
        {"task_id": "42", "finding_kind": "done_but_not_merged", "proof": "github_pr_open"},
        {"task_id": "42", "finding_kind": "multi_pr_epic_ambiguity", "proof": ""},
    ],
)
def test_shadow_manual_unknown_and_wrong_proof_cases_never_emit_would_apply(
    tmp_path: Path, candidate: dict[str, str]
) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-refused")
    record = build_shadow_record(
        candidate,
        target_root=target,
        approved_context_proof=_ci_context({"task_id": "42", "proof": candidate["proof"]}),
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        clone_parent=tmp_path / "clones",
    )

    assert record["decision"] == "shadow_refused"
    assert record["reason"] == "candidate_outside_first_apply_class"
    assert "target_status" not in record


@pytest.mark.parametrize(
    ("context", "kill_switch", "reason"),
    [
        (None, ENABLE_SHAPED_KILL_SWITCH, "approved_context_missing"),
        (
            {"context_type": "post_merge_ci"},
            ENABLE_SHAPED_KILL_SWITCH,
            "approved_context_malformed",
        ),
        (
            {"context_type": "unknown", "proof_id": "run"},
            ENABLE_SHAPED_KILL_SWITCH,
            "approved_context_unknown",
        ),
        (
            {
                "context_type": "post_merge_ci",
                "proof_id": "run",
                "task_id": "99",
                "proof": "git_ancestor",
            },
            ENABLE_SHAPED_KILL_SWITCH,
            "approved_context_binding_mismatch",
        ),
        (None, None, "approved_context_missing"),
        (None, DISABLED_KILL_SWITCH, "approved_context_missing"),
    ],
)
def test_shadow_refuses_missing_malformed_unapproved_contexts_before_validation(
    tmp_path: Path,
    context: dict[str, Any] | None,
    kill_switch: dict[str, Any] | None,
    reason: str,
) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-context-refused")
    candidate = _first_preview_candidate(target)
    record = build_shadow_record(
        candidate,
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=kill_switch,
        clone_parent=tmp_path / "clones",
    )

    assert record["decision"] == "shadow_refused"
    assert record["reason"] == reason


def test_shadow_refuses_kill_switch_disabled_after_valid_context(tmp_path: Path) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-kill-switch")
    candidate = _first_preview_candidate(target)
    record = build_shadow_record(
        candidate,
        target_root=target,
        approved_context_proof=_ci_context(candidate),
        kill_switch_state=DISABLED_KILL_SWITCH,
        clone_parent=tmp_path / "clones",
    )

    assert record["decision"] == "shadow_refused"
    assert record["reason"] == "kill_switch_class_disabled"


def test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo(
    tmp_path: Path,
) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-sacrificial")
    candidate = _first_preview_candidate(target)
    before = snapshot_whole_tree(target)

    validation = validate_sacrificial_taskmaster_done_cascade(
        target_root=target,
        task_id="42",
        predicted_paths=_dynamic_shadow_prediction(target, candidate),
        clone_parent=tmp_path / "clone-root",
    )

    before.assert_matches(snapshot_whole_tree(target))
    assert validation.matches_prediction is True
    assert validation.actual_delta_paths == _dynamic_shadow_prediction(target, candidate)
    assert validation.clone_root != target
    assert str(validation.clone_root).startswith(str(tmp_path))
    live_tasks = json.loads((target / ".taskmaster" / "tasks" / "tasks.json").read_text())
    clone_tasks = json.loads(
        (validation.clone_root / ".taskmaster" / "tasks" / "tasks.json").read_text()
    )
    assert live_tasks["master"]["tasks"][0]["status"] == "pending"
    assert clone_tasks["master"]["tasks"][0]["status"] == "done"


def test_build_ci_shadow_context_proof_uses_stable_github_run_fields() -> None:
    env = {
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "2",
        "GITHUB_WORKFLOW": "CI",
        "GITHUB_REPOSITORY": "loucmane/codex-starter-pack",
        "GITHUB_SHA": "abc",
    }

    first = build_ci_shadow_context_proof(env, task_id="42")
    second = build_ci_shadow_context_proof(env, task_id="42")

    assert first == second
    assert first["context_type"] == "post_merge_ci"
    assert first["proof_id"] == "github-actions:123:2"
    assert first["task_id"] == "42"
    assert first["proof"] == "git_ancestor"


def test_shadow_apply_is_not_reachable_from_agent_surfaces(tmp_path: Path) -> None:
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
    assert "aegis.reconcile_shadow_apply" not in tool_names
    reconcile_tool = tool_by_name(server, "aegis.reconcile")
    assert set(reconcile_tool.inputSchema["properties"]).isdisjoint(
        RECONCILE_MUTATION_PARAMETER_NAMES
    )

    codex_task_source = (REPO_ROOT / "scripts/codex-task").read_text(encoding="utf-8")
    assert "reconcile_shadow_apply" not in codex_task_source


def test_existing_writers_do_not_consume_shadow_apply() -> None:
    writer_functions = (
        aegis_installer.install,
        aegis_installer.repair,
        aegis_installer.start_local_work,
        aegis_installer.kickoff,
        aegis_installer.log_work,
        aegis_installer.verify,
        aegis_installer.closeout,
        aegis_installer.repair_handoff,
    )

    for function in writer_functions:
        source = inspect.getsource(function)
        assert "reconcile_shadow_apply" not in source
        assert "build_shadow_report" not in source


def test_ci_workflow_captures_shadow_context_artifact_without_apply_surface() -> None:
    workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    text = workflow_path.read_text(encoding="utf-8")
    steps = workflow["jobs"]["python-tests"]["steps"]

    assert "build_ci_shadow_context_proof" in text
    assert "reconcile-shadow-context-proof.json" in text
    assert any(step.get("uses") == "actions/upload-artifact@v4" for step in steps)
    assert "--apply" not in text
    assert "task-master set-status" not in text


def _setup_merged_git_ancestor(target: Path) -> Path:
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-42-cart-button")
    commit_file(target, "feature.txt", "cart\n", "task 42")
    git(target, "switch", "main")
    git(target, "merge", "--no-ff", "feat/task-42-cart-button", "-m", "merge task 42")
    return target


def _first_preview_candidate(target: Path) -> dict[str, Any]:
    report = reconcile(
        target,
        source_root=REPO_ROOT,
        base_ref="main",
        use_github=False,
        preview_candidates=True,
    )
    return dict(report["mutation_candidate_preview"]["candidates"][0])


def _ci_context(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "context_type": "post_merge_ci",
        "proof_id": "github-actions:123:1",
        "task_id": str(candidate.get("task_id") or ""),
        "proof": str(candidate.get("proof") or ""),
        "external_anchor": "github-actions://run/123/attempt/1",
    }


def _dynamic_shadow_prediction(target: Path, candidate: Mapping[str, Any]) -> tuple[str, ...]:
    paths = {str(path) for path in candidate["predicted_blast_radius_paths"]}
    if not (target / ".taskmaster" / "state.json").exists():
        paths.add(".taskmaster/state.json")
    return tuple(sorted(paths))


def _assert_no_action_shape(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            assert key not in ACTION_SHAPED_KEYS
            _assert_no_action_shape(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_action_shape(child)
    elif isinstance(value, str):
        for forbidden in ACTION_SHAPED_VALUES:
            assert forbidden not in value
