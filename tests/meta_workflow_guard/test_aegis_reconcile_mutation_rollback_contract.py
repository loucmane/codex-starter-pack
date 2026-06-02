"""Report-only rollback contract tests for future Aegis reconcile mutation."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.meta_workflow_guard.reconcile_mutation_rollback_contract import (
    FIRST_MUTATION_CANDIDATE,
    BlastRadiusContract,
    MutationContractError,
    RollbackHandle,
    audit_breadcrumb,
    build_mutation_proposal,
    default_rollback_contract,
    run_taskmaster_done_cascade_fixture,
)
from tests.meta_workflow_guard.reconcile_precision_corpus import FindingKey
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree


def test_first_mutation_candidate_requires_git_ancestor_confirmation_and_audits() -> None:
    blast_radius = BlastRadiusContract(
        registered_paths=(
            ".taskmaster/tasks/task_042.md",
            ".taskmaster/tasks/tasks.json",
        )
    )
    rollback = default_rollback_contract(blast_radius)

    proposal = build_mutation_proposal(
        finding=FIRST_MUTATION_CANDIDATE,
        operator_confirmed=True,
        audit_before=audit_breadcrumb("before"),
        audit_after=audit_breadcrumb("after"),
        blast_radius=blast_radius,
        rollback=rollback,
    )

    assert proposal.finding == FIRST_MUTATION_CANDIDATE
    assert proposal.operator_confirmed is True


@pytest.mark.parametrize(
    "finding",
    [
        FindingKey("merged_but_not_done", "43", "github_pr_merged"),
        FindingKey("done_but_not_merged", "45", "github_pr_open"),
        FindingKey("done_but_not_merged", "451", "github_pr_closed_unmerged"),
        FindingKey("multi_pr_epic_ambiguity", "47"),
        FindingKey("abandoned_in_progress_branch", "46"),
        FindingKey("stale_local_stub", "999"),
        FindingKey("local_ad_hoc_stub", "1000"),
        FindingKey("merged_but_not_done", "44", "git_only_non_ancestor_or_missing_base"),
    ],
)
def test_manual_ambiguous_and_non_first_auto_findings_cannot_enter_proposal_set(finding: FindingKey) -> None:
    blast_radius = BlastRadiusContract(registered_paths=(".taskmaster/tasks/tasks.json",))
    rollback = default_rollback_contract(blast_radius)

    with pytest.raises(MutationContractError):
        build_mutation_proposal(
            finding=finding,
            operator_confirmed=True,
            audit_before=audit_breadcrumb("before", finding),
            audit_after=audit_breadcrumb("after", finding),
            blast_radius=blast_radius,
            rollback=rollback,
        )


@pytest.mark.parametrize(
    ("operator_confirmed", "before_phase", "after_phase", "match"),
    [
        (False, "before", "after", "operator confirmation"),
        (True, None, "after", "audit breadcrumbs"),
        (True, "before", None, "audit breadcrumbs"),
        (True, "after", "after", "expected 'before' audit"),
        (True, "before", "before", "expected 'after' audit"),
    ],
)
def test_proposal_contract_rejects_missing_confirmation_or_audits(
    operator_confirmed: bool, before_phase: str | None, after_phase: str | None, match: str
) -> None:
    blast_radius = BlastRadiusContract(registered_paths=(".taskmaster/tasks/tasks.json",))
    rollback = default_rollback_contract(blast_radius)

    with pytest.raises(MutationContractError, match=match):
        build_mutation_proposal(
            finding=FIRST_MUTATION_CANDIDATE,
            operator_confirmed=operator_confirmed,
            audit_before=audit_breadcrumb(before_phase) if before_phase else None,
            audit_after=audit_breadcrumb(after_phase) if after_phase else None,
            blast_radius=blast_radius,
            rollback=rollback,
        )


def test_real_taskmaster_done_cascade_has_exact_registered_blast_radius(tmp_path: Path) -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is not available for the real cascade inventory")
    cascade = run_taskmaster_done_cascade_fixture(tmp_path / "taskmaster-done-cascade")

    assert cascade.changed_paths == (
        ".taskmaster/tasks/task_042.md",
        ".taskmaster/tasks/tasks.json",
    )
    assert (cascade.root / ".taskmaster" / "state.json").exists()


def test_blast_radius_contract_rejects_unregistered_changed_path(tmp_path: Path) -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is not available for the real cascade inventory")
    target = tmp_path / "unregistered-delta"
    cascade = run_taskmaster_done_cascade_fixture(target)

    (target / ".taskmaster" / "unregistered.tmp").write_text("not registered\n", encoding="utf-8")

    with pytest.raises(MutationContractError, match="unregistered.tmp"):
        cascade.blast_radius.assert_exact_delta(cascade.before, snapshot_whole_tree(target))


def test_rollback_handle_restores_registered_paths_and_verifies_tree(tmp_path: Path) -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is not available for the real cascade inventory")
    cascade = run_taskmaster_done_cascade_fixture(tmp_path / "rollback")

    cascade.rollback_handle.restore(cascade.root)

    cascade.before.assert_matches(snapshot_whole_tree(cascade.root))


def test_rollback_contract_requires_restoration_for_each_registered_path() -> None:
    blast_radius = BlastRadiusContract(
        registered_paths=(
            ".taskmaster/tasks/task_042.md",
            ".taskmaster/tasks/tasks.json",
        )
    )
    incomplete = default_rollback_contract(
        BlastRadiusContract(registered_paths=(".taskmaster/tasks/tasks.json",))
    )

    with pytest.raises(MutationContractError, match="missing"):
        build_mutation_proposal(
            finding=FIRST_MUTATION_CANDIDATE,
            operator_confirmed=True,
            audit_before=audit_breadcrumb("before"),
            audit_after=audit_breadcrumb("after"),
            blast_radius=blast_radius,
            rollback=incomplete,
        )


def test_rollback_handle_restores_missing_files_directories_and_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "path-kinds"
    target.mkdir()
    (target / "state").mkdir()
    (target / "state" / "tracked.json").write_text("{}\n", encoding="utf-8")
    (target / "state" / "current").symlink_to("tracked.json")
    paths = ("state", "state/tracked.json", "state/current", "state/missing.json")
    before = snapshot_whole_tree(target)
    handle = RollbackHandle.capture(target, paths)

    shutil.rmtree(target / "state")
    (target / "state").write_text("wrong kind\n", encoding="utf-8")

    handle.restore(target)

    before.assert_matches(snapshot_whole_tree(target))
