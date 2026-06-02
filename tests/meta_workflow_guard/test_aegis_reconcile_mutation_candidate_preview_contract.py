"""Inert mutation-candidate preview contract tests for Aegis reconcile."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import (
    AEGIS_CURRENT_WORK_REL,
    install,
    kickoff,
    reconcile,
)
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import (
    REPO_ROOT,
    commit_file,
    git,
    init_git_repo,
    run_target_pretooluse,
    simulate_claude_reload,
    write_taskmaster_tasks,
)
from tests.meta_workflow_guard.test_aegis_reconcile_precision_corpus import CORPUS_CASES

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


def test_reconcile_default_output_stays_observational_without_candidate_preview(
    tmp_path: Path,
) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "default-observational")
    before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    before.assert_matches(snapshot_whole_tree(target))
    assert "mutation_candidate_preview" not in report
    assert "mutation_candidates" not in report["summary"]


def test_reconcile_preview_candidate_is_opt_in_inert_data(tmp_path: Path) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "preview")
    before = snapshot_whole_tree(target)

    report = reconcile(
        target,
        source_root=REPO_ROOT,
        base_ref="main",
        use_github=False,
        preview_candidates=True,
    )

    before.assert_matches(snapshot_whole_tree(target))
    preview = report["mutation_candidate_preview"]
    candidate = preview["candidates"][0]
    assert preview["enabled"] is True
    assert preview["read_only"] is True
    assert preview["executable"] is False
    assert preview["apply_path_exists"] is False
    assert candidate["record_type"] == "mutation_candidate"
    assert candidate["task_id"] == "42"
    assert candidate["finding_kind"] == "merged_but_not_done"
    assert candidate["proof"] == "git_ancestor"
    assert candidate["executable"] is False
    assert candidate["apply_path_exists"] is False
    assert candidate["blocked_reason"] == "report-only per Task 147 contract"
    assert candidate["predicted_blast_radius_paths"] == [
        ".taskmaster/tasks/tasks.json",
        ".taskmaster/tasks/task_042.md",
    ]
    assert (
        candidate["rollback_contract"]["path"]
        == "docs/aegis/reconcile-mutation-rollback-contract.md"
    )
    assert "Task 145 side-effect oracle" in candidate["actual_blast_radius_authority"]
    _assert_no_action_shape(preview)


@pytest.mark.parametrize("case", CORPUS_CASES, ids=lambda case: case.case_id)
def test_preview_builder_reuses_precision_corpus_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case
) -> None:
    target = tmp_path / case.case_id
    case.setup(target, monkeypatch)

    report = reconcile(
        target,
        source_root=REPO_ROOT,
        base_ref="main",
        use_github=case.use_github,
        preview_candidates=True,
    )

    candidates = report["mutation_candidate_preview"]["candidates"]
    if case.case_id == "merged_git_ancestor":
        assert [(candidate["finding_kind"], candidate["proof"]) for candidate in candidates] == [
            ("merged_but_not_done", "git_ancestor")
        ]
    else:
        assert candidates == []
    for excluded in report["mutation_candidate_preview"]["excluded"]:
        assert excluded["record_type"] == "contract_exclusion"
        assert "TODO" not in json.dumps(excluded)


def test_preview_summary_is_report_only_and_non_executable(tmp_path: Path) -> None:
    target = _setup_merged_git_ancestor(tmp_path / "summary")

    report = reconcile(
        target,
        source_root=REPO_ROOT,
        base_ref="main",
        use_github=False,
        preview_candidates=True,
    )
    summary = aegis_installer.format_reconcile_summary(report)

    assert (
        "mutation_candidate_preview: report-only, executable=false, candidates=1, excluded=0"
        in summary
    )
    assert "task-master set-status" not in summary
    assert "--apply" not in summary


def test_preview_data_is_not_consumed_by_writer_functions() -> None:
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
        assert "mutation_candidate_preview" not in source
        assert "mutation_candidate" not in source


def test_preview_cannot_be_executed_out_of_band_by_taskmaster_gate(tmp_path: Path) -> None:
    target = tmp_path / "out-of-band-preview"
    write_taskmaster_tasks(
        target,
        [
            {"id": 42, "title": "Active", "status": "pending", "dependencies": [], "subtasks": []},
            {
                "id": 99,
                "title": "Previewed",
                "status": "pending",
                "dependencies": [],
                "subtasks": [],
            },
        ],
    )
    init_git_repo(target)
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="active", title="Active", source_root=REPO_ROOT)
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    current_work["status"] = "completed"
    current_work["closeout_passed_at"] = "2026-06-02T16:50:00Z"
    current_work["task"]["status"] = "completed"
    current_work_path.write_text(json.dumps(current_work, indent=2) + "\n", encoding="utf-8")

    wrong_task_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=99 --status=done"},
        },
    )

    assert wrong_task_gate.returncode == 2
    assert "readiness is BLOCKED" in wrong_task_gate.stderr


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
