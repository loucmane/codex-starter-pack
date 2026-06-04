"""Labeled precision corpus for Aegis reconcile."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import reconcile
from tests.meta_workflow_guard.reconcile_precision_corpus import (
    ExpectedFinding,
    ExpectedNonFinding,
    FindingKey,
    assert_precision_contract,
)
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import (
    REPO_ROOT,
    commit_file,
    git,
    init_git_repo,
    write_taskmaster_tasks,
)


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    setup: Callable[[Path, pytest.MonkeyPatch], None]
    use_github: bool
    expected_findings: tuple[ExpectedFinding, ...]
    expected_non_findings: tuple[ExpectedNonFinding, ...] = ()


def _setup_merged_git_ancestor(target: Path) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}])
    git(target, "switch", "-c", "feat/task-42-cart-button")
    commit_file(target, "feature.txt", "cart\n", "task 42")
    git(target, "switch", "main")
    git(target, "merge", "--no-ff", "feat/task-42-cart-button", "-m", "merge task 42")


def _setup_squash_github_merged(target: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(target, [{"id": 43, "title": "Squashed Feature", "status": "pending", "dependencies": []}])
    git(target, "switch", "-c", "feat/task-43-squashed-feature")
    commit_file(target, "feature.txt", "squash\n", "task 43")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-43-squashed-feature")
    git(target, "commit", "-m", "squash task 43")
    _mock_prs(
        monkeypatch,
        [
            _pr(
                number=43,
                state="MERGED",
                title="Task 43 squashed feature",
                head="feat/task-43-squashed-feature",
                merged_at="2026-06-02T10:00:00Z",
            )
        ],
    )


def _setup_done_open_pr(target: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(target, [{"id": 45, "title": "Open PR", "status": "done", "dependencies": []}])
    git(target, "switch", "-c", "feat/task-45-open-pr")
    commit_file(target, "feature.txt", "open\n", "task 45")
    _mock_prs(
        monkeypatch,
        [_pr(number=45, state="OPEN", title="Task 45 open PR", head="feat/task-45-open-pr")],
    )


def _setup_squash_offline_unknown(target: Path) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(target, [{"id": 44, "title": "Offline Squash", "status": "pending", "dependencies": []}])
    git(target, "switch", "-c", "feat/task-44-offline-squash")
    commit_file(target, "feature.txt", "offline\n", "task 44")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-44-offline-squash")
    git(target, "commit", "-m", "squash task 44")


def _setup_done_git_only_unknown(target: Path) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(target, [{"id": 441, "title": "Done Offline", "status": "done", "dependencies": []}])
    git(target, "switch", "-c", "feat/task-441-stale-local-branch")
    commit_file(target, "feature.txt", "offline done\n", "task 441")
    git(target, "switch", "main")


def _setup_manual_ambiguity_and_stubs(target: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_git_repo(target)
    write_taskmaster_tasks(
        target,
        [
            {"id": 46, "title": "In Progress", "status": "in-progress", "dependencies": []},
            {"id": 47, "title": "Ambiguous Epic", "status": "pending", "dependencies": []},
        ],
    )
    git(target, "switch", "-c", "feat/task-46-abandoned")
    commit_file(target, "task46.txt", "abandoned\n", "task 46")
    git(target, "switch", "main")
    git(target, "switch", "-c", "feat/task-999-local-stub")
    commit_file(target, "stub.txt", "stub\n", "task 999")
    git(target, "switch", "main")
    (target / ".aegis" / "state").mkdir(parents=True)
    (target / ".aegis" / "state" / "local-tasks.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tasks": [
                    {"id": "1000", "title": "Ad hoc local task", "status": "in-progress", "slug": "ad-hoc"}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _mock_prs(
        monkeypatch,
        [
            _pr(number=470, state="OPEN", title="Task 47 part A", head="feat/task-47-part-a"),
            _pr(number=471, state="OPEN", title="Task 47 part B", head="feat/task-47-part-b"),
        ],
    )


def _mock_prs(monkeypatch: pytest.MonkeyPatch, prs: list[dict[str, object]]) -> None:
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": True, "reason": "", "prs": prs},
    )


def _pr(
    *,
    number: int,
    state: str,
    title: str,
    head: str,
    merged_at: str | None = None,
) -> dict[str, object]:
    return {
        "number": number,
        "state": state,
        "title": title,
        "headRefName": head,
        "baseRefName": "main",
        "mergedAt": merged_at,
        "url": f"https://example.invalid/pr/{number}",
        "isDraft": False,
    }


CORPUS_CASES = (
    CorpusCase(
        case_id="merged_git_ancestor",
        setup=lambda target, monkeypatch: _setup_merged_git_ancestor(target),
        use_github=False,
        expected_findings=(
            ExpectedFinding(FindingKey("merged_but_not_done", "42", "git_ancestor"), "auto_eligible"),
        ),
    ),
    CorpusCase(
        case_id="squash_github_merged",
        setup=_setup_squash_github_merged,
        use_github=True,
        expected_findings=(
            ExpectedFinding(FindingKey("merged_but_not_done", "43", "github_pr_merged"), "auto_eligible"),
        ),
    ),
    CorpusCase(
        case_id="done_open_pr",
        setup=_setup_done_open_pr,
        use_github=True,
        expected_findings=(
            ExpectedFinding(FindingKey("done_but_not_merged", "45", "github_pr_open"), "auto_eligible"),
        ),
    ),
    CorpusCase(
        case_id="squash_offline_unknown",
        setup=lambda target, monkeypatch: _setup_squash_offline_unknown(target),
        use_github=False,
        expected_findings=(),
        expected_non_findings=(ExpectedNonFinding("44", "git_only_non_ancestor_or_missing_base"),),
    ),
    CorpusCase(
        case_id="done_git_only_unknown",
        setup=lambda target, monkeypatch: _setup_done_git_only_unknown(target),
        use_github=False,
        expected_findings=(),
        expected_non_findings=(ExpectedNonFinding("441", "git_only_non_ancestor_or_missing_base"),),
    ),
    CorpusCase(
        case_id="manual_ambiguity_and_stubs",
        setup=_setup_manual_ambiguity_and_stubs,
        use_github=True,
        expected_findings=(
            ExpectedFinding(FindingKey("abandoned_in_progress_branch", "46"), "manual_only"),
            ExpectedFinding(FindingKey("multi_pr_epic_ambiguity", "47"), "manual_only"),
            ExpectedFinding(FindingKey("stale_local_stub", "999"), "manual_only"),
            ExpectedFinding(FindingKey("local_ad_hoc_stub", "1000"), "manual_only"),
        ),
    ),
)


@pytest.mark.parametrize("case", CORPUS_CASES, ids=lambda case: case.case_id)
def test_reconcile_precision_corpus_recomputes_labels_and_blocks_boundary_leaks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: CorpusCase
) -> None:
    target = tmp_path / case.case_id
    case.setup(target, monkeypatch)
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=case.use_github)

    tree_before.assert_matches(snapshot_whole_tree(target))
    metrics = assert_precision_contract(
        report,
        expected_findings=case.expected_findings,
        expected_non_findings=case.expected_non_findings,
    )
    assert metrics.boundary_leak_count == 0
    assert metrics.false_positive_count == 0
    assert all(value == 1.0 for value in metrics.precision_by_finding_proof.values())


def test_precision_gate_rejects_manual_only_labelled_auto_eligible() -> None:
    report = {
        "findings": [
            {"kind": "multi_pr_epic_ambiguity", "task_id": "47", "severity": "warning", "evidence": {}}
        ],
        "tasks": [],
    }

    with pytest.raises(AssertionError, match="boundary leak"):
        assert_precision_contract(
            report,
            expected_findings=(
                ExpectedFinding(FindingKey("multi_pr_epic_ambiguity", "47"), "auto_eligible"),
            ),
        )


def test_precision_gate_rejects_unlabelled_auto_false_positive() -> None:
    report = {
        "findings": [
            {
                "kind": "merged_but_not_done",
                "task_id": "42",
                "severity": "error",
                "evidence": {"merge_truth": {"proof": "git_ancestor"}},
            }
        ],
        "tasks": [],
    }

    with pytest.raises(AssertionError, match="false-positive"):
        assert_precision_contract(report, expected_findings=())


def test_precision_gate_requires_non_finding_proof_labels() -> None:
    report = {
        "findings": [],
        "tasks": [
            {
                "task_id": "44",
                "merge_truth": {"status": "unknown", "proof": "git_only_non_ancestor_or_missing_base"},
            }
        ],
    }

    metrics = assert_precision_contract(
        report,
        expected_findings=(),
        expected_non_findings=(ExpectedNonFinding("44", "git_only_non_ancestor_or_missing_base"),),
    )
    assert metrics.expected_non_finding_count == 1

    mismatch_report = {
        "findings": [],
        "tasks": [{"task_id": "44", "merge_truth": {"status": "unknown", "proof": "git_non_ancestor"}}],
    }
    with pytest.raises(AssertionError, match="proof mismatch"):
        assert_precision_contract(
            mismatch_report,
            expected_findings=(),
            expected_non_findings=(ExpectedNonFinding("44", "git_only_non_ancestor_or_missing_base"),),
        )


def test_precision_metrics_do_not_aggregate_across_proof_sources() -> None:
    report = {
        "findings": [
            {
                "kind": "merged_but_not_done",
                "task_id": "42",
                "severity": "error",
                "evidence": {"merge_truth": {"proof": "git_ancestor"}},
            }
        ],
        "tasks": [],
    }

    metrics = assert_precision_contract(
        report,
        expected_findings=(
            ExpectedFinding(FindingKey("merged_but_not_done", "42", "git_ancestor"), "auto_eligible"),
        ),
    )

    assert metrics.precision_by_finding_proof == {"merged_but_not_done/git_ancestor": 1.0}
    assert "merged_but_not_done/github_pr_merged" not in metrics.precision_by_finding_proof
    assert "merged_but_not_done" not in metrics.precision_by_finding_proof
