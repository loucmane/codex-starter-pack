"""Shadow-mode reconcile apply artifact tests."""

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

import pytest
import yaml

from aegis_foundation import reconcile_shadow_apply as shadow_apply
from aegis_foundation import cli as aegis_cli
from aegis_foundation.reconcile_apply_scaffold import FIRST_APPLY_CLASS_KEY
from aegis_foundation.reconcile_shadow_apply import (
    SHADOW_ARTIFACT_NAME,
    build_ci_shadow_cascade_validation_report,
    build_ci_shadow_context_proof,
    build_shadow_accumulation_report,
    build_shadow_record,
    build_shadow_report,
    validate_sacrificial_taskmaster_done_cascade,
    validate_taskmaster_apply_semantic_delta,
    write_local_shadow_report,
)
from aegis_foundation.taskmaster_toolchain import (
    TASKMASTER_PACKAGE_VERSION,
    build_taskmaster_toolchain_evidence,
    compare_taskmaster_toolchain_evidence,
    taskmaster_install_spec,
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


def test_shadow_accumulation_marks_pr_ci_invalid_for_shadow(tmp_path: Path) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-pr-ci")
    candidate = _first_preview_candidate(target)
    context = build_ci_shadow_context_proof(
        {
            **_github_env(),
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/155/merge",
            "GITHUB_REF_NAME": "155/merge",
        },
        task_id=str(candidate["task_id"]),
        proof=str(candidate["proof"]),
    )

    report = build_shadow_accumulation_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )

    assert report["record_type"] == "reconcile_shadow_accumulation"
    assert report["valid_for_shadow"] is False
    assert report["summary"]["would_apply"] == 0
    assert report["summary"]["shadow_refused"] == 1
    assert report["shadow_report"]["shadow_refused"][0]["approved_context"]["valid_for_shadow"] is False
    assert report["shadow_report"]["shadow_refused"][0]["reason"] == (
        "shadow_context_not_valid_for_accumulation"
    )
    assert "validation_context" not in report["shadow_report"]["shadow_refused"][0]


def test_shadow_accumulation_forces_no_would_apply_when_context_marks_invalid(
    tmp_path: Path,
) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-invalid-context-flag")
    candidate = _first_preview_candidate(target)
    context = {**_ci_context(candidate), "valid_for_shadow": False}

    report = build_shadow_accumulation_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )

    assert report["valid_for_shadow"] is False
    assert report["summary"]["would_apply"] == 0
    assert report["shadow_report"]["would_apply"] == []
    refused = report["shadow_report"]["shadow_refused"][0]
    assert refused["reason"] == "shadow_context_not_valid_for_accumulation"
    assert "validation_context" not in refused


def test_shadow_accumulation_triage_is_reporting_only(tmp_path: Path) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-accumulation")
    candidate = _first_preview_candidate(target)
    context = build_ci_shadow_context_proof(
        _github_env(),
        task_id=str(candidate["task_id"]),
        proof=str(candidate["proof"]),
    )
    before = snapshot_whole_tree(target)

    report = build_shadow_accumulation_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )

    before.assert_matches(snapshot_whole_tree(target))
    assert report["valid_for_shadow"] is True
    assert report["triage"]["reporting_only"] is True
    assert report["triage"]["auto_extend_canonicalization"] is False
    assert report["triage"]["auto_write_exemptions"] is False
    assert report["triage"]["benign_normalizations_accepted"] == 0
    assert report["summary"]["zero_unexplained_divergences"] is True


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


@pytest.mark.parametrize(
    "payload",
    [
        "{not json\n",
        {"master": {"tasks": [{"id": 42, "status": "frobnicate", "dependencies": []}]}},
        {
            "master": {
                "tasks": [
                    {"id": 42, "status": "pending", "dependencies": []},
                    {"id": "42", "status": "pending", "dependencies": []},
                ]
            }
        },
        {"master": {"tasks": []}},
    ],
)
def test_shadow_refuses_invalid_taskmaster_authority_before_validation(
    tmp_path: Path, payload: str | dict[str, Any]
) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "shadow-invalid-taskmaster")
    candidate = _first_preview_candidate(target)
    tasks_path = target / ".taskmaster" / "tasks" / "tasks.json"
    if isinstance(payload, str):
        tasks_path.write_text(payload, encoding="utf-8")
    else:
        tasks_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    report = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=_ci_context(candidate),
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
    )

    assert report["would_apply"] == []
    assert report["shadow_refused"][0]["reason"] == "taskmaster_authority_invalid"
    assert "validation_context" not in report["shadow_refused"][0]


def test_shadow_refuses_state_json_meaningful_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-state-json-mutation")
    state_path = target / ".taskmaster" / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "currentTag": "master",
                "lastSwitched": "2025-09-22T11:42:16.191Z",
                "branchTagMapping": {},
                "migrationNoticeShown": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    candidate = _first_preview_candidate(target)
    original_read = shadow_apply._read_taskmaster_semantic_inputs
    read_count = 0

    def mutating_read(root: Path, *, task_id: str, predicted_paths: Any) -> dict[str, Any]:
        nonlocal read_count
        read_count += 1
        payload = original_read(root, task_id=task_id, predicted_paths=predicted_paths)
        if read_count == 2:
            payload["state_json"] = {
                "currentTag": "other",
                "lastSwitched": "2025-09-22T11:42:16.191Z",
                "branchTagMapping": {},
                "migrationNoticeShown": True,
            }
        return payload

    monkeypatch.setattr(shadow_apply, "_read_taskmaster_semantic_inputs", mutating_read)

    report = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=_ci_context(candidate),
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        clone_parent=tmp_path / "clones",
    )

    assert report["would_apply"] == []
    refused = report["shadow_refused"][0]
    assert refused["reason"] == "state_json_unexpected_mutation"
    assert refused["taskmaster_semantic_delta"]["reason"] == "state_json_unexpected_mutation"
    assert refused["taskmaster_semantic_delta"]["details"]["state_json"]["reason"] == (
        "state_json_active_tag_changed"
    )


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
    assert validation.path_delta_matches_prediction is True
    assert validation.semantic_delta_matches_prediction is True
    assert validation.semantic_delta.reason == "semantic_delta_matches_prediction"
    assert validation.actual_delta_paths == validation.predicted_paths
    assert validation.clone_root != target
    assert str(validation.clone_root).startswith(str(tmp_path))
    live_tasks = json.loads((target / ".taskmaster" / "tasks" / "tasks.json").read_text())
    clone_tasks = json.loads(
        (validation.clone_root / ".taskmaster" / "tasks" / "tasks.json").read_text()
    )
    assert live_tasks["master"]["tasks"][0]["status"] == "pending"
    assert clone_tasks["master"]["tasks"][0]["status"] == "done"


def test_semantic_delta_allows_id_normalization_but_only_target_status_change() -> None:
    before = {
        "tasks_json": {
            "master": {
                "tasks": [
                    {"id": 42, "status": "pending", "dependencies": [41], "subtasks": []},
                    {"id": 41, "status": "done", "dependencies": [], "subtasks": []},
                ]
            }
        },
        "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
    }
    after = {
        "tasks_json": {
            "master": {
                "tasks": [
                    {"id": "42", "status": "done", "dependencies": ["41"], "subtasks": []},
                    {"id": "41", "status": "done", "dependencies": [], "subtasks": []},
                ]
            }
        },
        "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
    }

    result = validate_taskmaster_apply_semantic_delta(
        before=before,
        after=after,
        task_id="42",
        expected_status="done",
    )

    assert result.passed is True
    assert result.reason == "semantic_delta_matches_prediction"


@pytest.mark.parametrize("after_status", ["pending", "in-progress", "cancelled", "deferred"])
def test_semantic_delta_rejects_target_status_other_than_done(after_status: str) -> None:
    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": {
                "master": {
                    "tasks": [
                        {"id": 42, "status": "pending", "dependencies": [], "subtasks": []}
                    ]
                }
            },
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": {
                "master": {
                    "tasks": [
                        {"id": "42", "status": after_status, "dependencies": [], "subtasks": []}
                    ]
                }
            },
            "generated_task_markdown": f"# Task 42: Target\n\n- Status: {after_status}\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == "target_status_not_done"
    assert result.details["after_status"] == after_status


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (
            lambda payload: payload["master"]["tasks"][1].__setitem__("status", "pending"),
            "tasks_json_semantic_mismatch",
        ),
        (
            lambda payload: payload["master"]["tasks"][1].__setitem__("dependencies", ["42"]),
            "tasks_json_semantic_mismatch",
        ),
        (
            lambda payload: payload["master"]["tasks"].append(
                {"id": "99", "status": "pending", "dependencies": [], "subtasks": []}
            ),
            "tasks_json_semantic_mismatch",
        ),
        (
            lambda payload: payload["master"]["tasks"][0]["subtasks"].append(
                {"id": "1", "status": "pending", "dependencies": []}
            ),
            "tasks_json_semantic_mismatch",
        ),
    ],
)
def test_semantic_delta_rejects_unrelated_task_and_subtask_drift(
    mutator: Any, reason: str
) -> None:
    before_tasks = {
        "master": {
            "tasks": [
                {"id": 42, "status": "pending", "dependencies": [], "subtasks": []},
                {"id": 41, "title": "Dependency", "status": "done", "dependencies": [], "subtasks": []},
            ]
        }
    }
    after_tasks = json.loads(json.dumps(before_tasks))
    after_tasks["master"]["tasks"][0]["status"] = "done"
    mutator(after_tasks)

    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == reason


def test_semantic_delta_rejects_non_target_content_drift() -> None:
    before_tasks = {
        "master": {
            "tasks": [
                {"id": 42, "title": "Target", "status": "pending", "dependencies": [], "subtasks": []},
                {"id": 41, "title": "Dependency", "status": "done", "dependencies": [], "subtasks": []},
            ]
        }
    }
    after_tasks = json.loads(json.dumps(before_tasks))
    after_tasks["master"]["tasks"][0]["status"] = "done"
    after_tasks["master"]["tasks"][1]["title"] = "Dependency changed"

    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == "tasks_json_semantic_mismatch"


def test_semantic_delta_updated_at_and_tag_metadata_exemptions_stay_narrow() -> None:
    before_tasks = {
        "master": {
            "tasks": [
                {
                    "id": 42,
                    "title": "Target",
                    "status": "pending",
                    "priority": "high",
                    "dependencies": [],
                    "subtasks": [],
                    "updatedAt": "2026-06-01T00:00:00.000Z",
                }
            ],
            "metadata": {"updated": "2026-06-01T00:00:00.000Z", "description": "old"},
        }
    }
    after_tasks = json.loads(json.dumps(before_tasks))
    after_tasks["master"]["tasks"][0]["status"] = "done"
    after_tasks["master"]["tasks"][0]["updatedAt"] = "2026-06-03T00:00:00.000Z"
    after_tasks["master"]["metadata"] = {
        "updated": "2026-06-03T00:00:00.000Z",
        "description": "new",
    }

    allowed = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert allowed.passed is True
    assert allowed.reason == "semantic_delta_matches_prediction"

    after_with_content_drift = json.loads(json.dumps(after_tasks))
    after_with_content_drift["master"]["tasks"][0]["title"] = "Changed target"

    rejected = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_with_content_drift,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert rejected.passed is False
    assert rejected.reason == "tasks_json_semantic_mismatch"


def test_semantic_delta_rejects_dropped_dependencies_after_type_normalization() -> None:
    before_tasks = {
        "master": {
            "tasks": [
                {"id": 42, "status": "pending", "dependencies": [40, 41], "subtasks": []},
                {"id": 41, "status": "done", "dependencies": [], "subtasks": []},
                {"id": 40, "status": "done", "dependencies": [], "subtasks": []},
            ]
        }
    }
    after_tasks = json.loads(json.dumps(before_tasks))
    after_tasks["master"]["tasks"][0]["id"] = "42"
    after_tasks["master"]["tasks"][0]["status"] = "done"
    after_tasks["master"]["tasks"][0]["dependencies"] = ["41"]

    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_tasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == "tasks_json_semantic_mismatch"


def test_semantic_delta_allows_absent_empty_subtasks_but_rejects_subtask_deletion() -> None:
    before_without_subtasks = {
        "master": {"tasks": [{"id": 42, "status": "pending", "dependencies": []}]}
    }
    after_with_empty_subtasks = {
        "master": {
            "tasks": [
                {"id": "42", "status": "done", "dependencies": [], "subtasks": []}
            ]
        }
    }

    allowed = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_without_subtasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_with_empty_subtasks,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert allowed.passed is True
    assert allowed.reason == "semantic_delta_matches_prediction"

    before_with_subtask = {
        "master": {
            "tasks": [
                {
                    "id": 42,
                    "status": "pending",
                    "dependencies": [],
                    "subtasks": [
                        {"id": "42.1", "status": "pending", "dependencies": []}
                    ],
                }
            ]
        }
    }
    after_deleted_subtask = {
        "master": {
            "tasks": [
                {"id": "42", "status": "done", "dependencies": [], "subtasks": []}
            ]
        }
    }

    rejected = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": before_with_subtask,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": after_deleted_subtask,
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert rejected.passed is False
    assert rejected.reason == "tasks_json_semantic_mismatch"


def test_semantic_delta_rejects_target_generated_markdown_without_done_status() -> None:
    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": {
                "master": {
                    "tasks": [{"id": 42, "status": "pending", "dependencies": [], "subtasks": []}]
                }
            },
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        after={
            "tasks_json": {
                "master": {
                    "tasks": [{"id": "42", "status": "done", "dependencies": [], "subtasks": []}]
                }
            },
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == "generated_markdown_status_mismatch"


def test_semantic_delta_rejects_state_json_branch_mapping_rewrite() -> None:
    result = validate_taskmaster_apply_semantic_delta(
        before={
            "tasks_json": {
                "master": {
                    "tasks": [{"id": 42, "status": "pending", "dependencies": [], "subtasks": []}]
                }
            },
            "generated_task_markdown": "# Task 42: Target\n\n- Status: pending\n",
            "state_json": {
                "currentTag": "master",
                "branchTagMapping": {"main": "master"},
                "migrationNoticeShown": True,
            },
        },
        after={
            "tasks_json": {
                "master": {
                    "tasks": [{"id": "42", "status": "done", "dependencies": [], "subtasks": []}]
                }
            },
            "generated_task_markdown": "# Task 42: Target\n\n- Status: done\n",
            "state_json": {
                "currentTag": "master",
                "branchTagMapping": {"main": "other"},
                "migrationNoticeShown": True,
            },
        },
        task_id="42",
        expected_status="done",
    )

    assert result.passed is False
    assert result.reason == "state_json_unexpected_mutation"
    assert result.details["state_json"]["reason"] == "state_json_branch_mapping_changed"


def test_shadow_prediction_accepts_steady_state_json_without_required_delta(tmp_path: Path) -> None:
    _require_taskmaster_cli()
    target = _setup_merged_git_ancestor(tmp_path / "shadow-state-present")
    state_path = target / ".taskmaster" / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "currentTag": "master",
                "lastSwitched": "2025-09-22T11:42:16.191Z",
                "branchTagMapping": {},
                "migrationNoticeShown": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    candidate = _first_preview_candidate(target)
    context = _ci_context(candidate)

    report = build_shadow_report(
        [candidate],
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=tmp_path / "clones",
    )

    record = report["would_apply"][0]
    assert record["sacrificial_delta_matches_prediction"] is True
    assert record["predicted_blast_radius_paths"] == record["actual_sacrificial_delta_paths"]


def test_ci_shadow_cascade_validation_report_covers_both_state_json_branches(
    tmp_path: Path,
) -> None:
    _require_taskmaster_cli()
    toolchain = _toolchain_evidence()

    report = build_ci_shadow_cascade_validation_report(
        _github_env(),
        work_root=tmp_path / "ci-work",
        toolchain_evidence=toolchain,
        clone_parent=tmp_path / "clones",
    )

    assert report["record_type"] == "reconcile_shadow_ci_cascade_validation"
    assert report["executed"] is False
    assert report["mutated_live_repo"] is False
    assert report["task_master_toolchain"] == toolchain
    assert report["toolchain_binding"]["comparison"]["matches"] is True
    assert report["summary"]["would_apply_records"] == 3
    assert report["summary"]["all_sacrificial_deltas_match_prediction"] is True
    cases = {case["case"]: case for case in report["cases"]}
    absent_record = cases["state_json_absent"]["shadow_report"]["would_apply"][0]
    legacy_record = cases["state_json_legacy_tag"]["shadow_report"]["would_apply"][0]
    steady_record = cases["state_json_steady_state"]["shadow_report"]["would_apply"][0]

    assert cases["state_json_absent"]["state_json_initially_present"] is False
    assert cases["state_json_legacy_tag"]["state_json_initially_present"] is True
    assert cases["state_json_steady_state"]["state_json_initially_present"] is True
    for record in (absent_record, legacy_record, steady_record):
        assert record["predicted_blast_radius_paths"] == record["actual_sacrificial_delta_paths"]
        assert record["executed"] is False
        assert record["mutated_live_repo"] is False


def test_taskmaster_toolchain_mismatch_invalidates_prior_cascade_evidence() -> None:
    validated = _toolchain_evidence()
    current = _toolchain_evidence(task_master_version="99.0.0")
    lock_changed = _toolchain_evidence(lock_id="different-lock")

    version_comparison = compare_taskmaster_toolchain_evidence(validated, current)
    lock_comparison = compare_taskmaster_toolchain_evidence(validated, lock_changed)

    assert version_comparison["matches"] is False
    assert {item["field"] for item in version_comparison["mismatches"]} == {"task_master.version"}
    assert lock_comparison["matches"] is False
    assert {item["field"] for item in lock_comparison["mismatches"]} == {"provisioning.lock_id"}
    assert compare_taskmaster_toolchain_evidence(validated, dict(validated))["matches"] is True


def test_build_ci_shadow_context_proof_uses_stable_github_run_fields() -> None:
    env = {
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REF_NAME": "main",
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
    assert first["valid_for_shadow"] is True
    assert first["shadow_context_reason"] == "post_merge_push_main"
    assert first["ci"]["event_name"] == "push"
    assert first["ci"]["ref"] == "refs/heads/main"

    pr = build_ci_shadow_context_proof(
        {
            **env,
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/155/merge",
            "GITHUB_REF_NAME": "155/merge",
        },
        task_id="42",
    )
    assert pr["context_type"] == "pull_request_ci"
    assert pr["valid_for_shadow"] is False
    assert pr["shadow_context_reason"] == "pull_request_not_post_merge"


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
        assert "build_shadow_accumulation_report" not in source
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


def _github_env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REF_NAME": "main",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW": "CI",
        "GITHUB_REPOSITORY": "loucmane/codex-starter-pack",
        "GITHUB_SHA": "abc",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
        "ImageOS": "ubuntu22",
        "ImageVersion": "20260603.1",
    }


def _toolchain_evidence(
    *,
    task_master_version: str = TASKMASTER_PACKAGE_VERSION,
    lock_id: str | None = None,
) -> dict[str, Any]:
    evidence = build_taskmaster_toolchain_evidence(
        _github_env(),
        task_master_version=task_master_version,
        node_version="v22.16.0",
        npm_version="10.9.2",
        python_version="3.12.3",
    )
    if lock_id is not None:
        evidence["provisioning"]["lock_id"] = lock_id
    assert evidence["task_master"]["install_spec"] == taskmaster_install_spec()
    return evidence


def _dynamic_shadow_prediction(target: Path, candidate: Mapping[str, Any]) -> tuple[str, ...]:
    paths = {str(path) for path in candidate["predicted_blast_radius_paths"]}
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
