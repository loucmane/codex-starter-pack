# Task 146 Design - Reconcile Precision Corpus

## Scope
Task 146 adds a recomputed labeled precision corpus for `aegis reconcile`. The goal is to prove the auto/manual boundary before any future reconcile mutation task can claim a finding class is safe to automate.

## Corpus Contract
- Store expected labels as structured pytest data, not prose-only documentation.
- Rebuild fixture repositories under pytest temp roots.
- Run `scripts/_aegis_installer.py::reconcile` against each fixture.
- Normalize observed findings by stable fields: `kind`, `task_id`, and merge-truth `proof`.
- Compare observed output with expected labels and fail on missing expected findings, unlabelled findings, false positives, non-finding proof drift, or auto/manual boundary leaks.

## Eligibility Boundary
Auto-eligible proof classes are pre-registered in code before measurement:
- `merged_but_not_done` with `git_ancestor`
- `merged_but_not_done` with `github_pr_merged`
- `done_but_not_merged` with `github_pr_open`
- `done_but_not_merged` with `github_pr_closed_unmerged`

Manual-only findings remain manual:
- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- squash/offline unknown merge truth (`git_only_non_ancestor_or_missing_base`)

## Non-Goals
- No reconcile mutation behavior.
- No new `--apply`, `--auto`, `--fix`, status, closeout, git-write, PR-write, or MCP mutation path.
- No Taskmaster status mutation from reconcile.

## Verification Plan
- Focused precision corpus pytest.
- Existing reconcile installer subset.
- Existing MCP reconcile subset.
- Full relevant installer/MCP/corpus suite.
- Taskmaster health, codex guard, work-tracking audit, and Serena continuity memory.
