# Aegis Reconcile Promotion Contract

**Status:** active contract for Tasks 144-145.
**Scope:** `aegis reconcile` remains a read-only drift report. This document defines the
minimum bar for any separate future task that proposes reconcile-driven mutation.

## Current Contract

The reconcile surfaces are report-only:

- `python3 scripts/codex-task aegis reconcile`
- `aegis_foundation/cli.py` package command `aegis reconcile`
- `scripts/_aegis_installer.py::reconcile`
- MCP tool `aegis.reconcile`

Those surfaces must not mutate Taskmaster status, Aegis workflow state, git refs, PR
state, closeout artifacts, generated task stubs, or work-tracking files. The command may
inspect git, Taskmaster, Aegis state, and optional GitHub PR metadata, then emit a report.
It must not implement hidden status-setting paths, closeout automation, git write
commands, PR writes, or Taskmaster mutation.

Task 143 captured the promotion evidence that justifies keeping this line in place:
`docs/ai/work-tracking/archive/20260602-task143-reconcile-promotion-criteria-COMPLETED/reports/reconcile-promotion-criteria/promotion-criteria-summary.md`.
That dogfood pass proved the report is useful for finding drift, but it also showed that
some findings are intentionally ambiguous and should not be auto-resolved.

## Mutation Is A Separate Task

Any future reconcile auto-mutation mode must be implemented as a separate Taskmaster task
and branch. It cannot be introduced by adding casual flags to the current read-only
surfaces.

The existing CLI and MCP contracts intentionally exclude mutating flags and parameters such
as:

- `--apply`
- `--auto`
- `--auto-fix`
- `--fix`
- `--set-status`
- `--status`
- `--done`
- `--closeout`
- `--mutate`
- `--write`
- `--push`

Tests must fail if those options appear on reconcile before the separate mutation task
defines and verifies the required safety model.

## Promotion Criteria

A future mutation mode must prove all of the following before it can move past report-only:

- **Operator confirmation:** every proposed mutation is shown to the operator with the
  target task, proof source, current state, proposed state, and affected files. The
  operator must explicitly confirm the action.
- **Audit breadcrumb:** every proposed mutation records an audit event before execution and
  a result event after execution. The record must include tool, handler, task id, proof,
  changed paths, timestamp, and outcome.
- **Rollback evidence:** every mutation has either a reversible operation plan or a
  captured before/after artifact that can restore the previous state.
- **High-confidence proof:** each mutation class has a positive proof requirement. Examples
  include `git_ancestor` for merged branches and GitHub `MERGED` PR metadata for squash
  merges. Absence of proof is not proof of drift.
- **Manual-only finding classes:** ambiguous findings remain report-only unless a later
  task proves a narrower safe rule.
- **No closeout shortcut:** reconcile cannot mark Aegis closeout complete. Closeout remains
  governed by its own scope, evidence, verification, and handoff gates.
- **No git or PR writes by default:** pushing, deleting branches, editing PRs, or changing
  refs must be separately confirmed and audited.

## Manual-Only Findings

These finding kinds stay manual-only under the current contract:

- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- squash/offline unknown merge truth, including `git_only_non_ancestor_or_missing_base`

These cases are valuable as report output because they tell an operator where to inspect.
They are not safe automatic mutation targets.

## Test Gate

Task 144 encodes the contract in tests:

- CLI parser tests reject reconcile mutation flags in both `scripts/codex-task` and the
  packaged `aegis_foundation` CLI.
- MCP schema tests assert `aegis.reconcile` exposes only `target_dir`, `base_ref`, and
  `use_github`.
- MCP execution tests assert the tool response and core result are marked `read_only=True`.
- Reconcile smoke checks compare git status before and after execution to guard the
  report-only behavior.

Task 145 strengthens the behavioral side-effect proof:

- `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` snapshots path existence,
  path type, mode, symlink target, regular-file content hash, and recursive membership.
- `tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py` proves the oracle catches
  content edits, creation, deletion, mode changes, symlink target changes, type swaps,
  missing-path creation, and unauthorized deltas while allowing only exact declared output
  paths.
- Whole-tree isolated fixture checks in `tests/meta_workflow_guard/test_aegis_installer.py`
  assert reconcile changes nothing anywhere in the temp fixture, aside from narrowly
  tolerated git discovery churn such as `.git/FETCH_HEAD` and `.git/logs/**`.
- Focused control-plane checks cover larger-repo surfaces where whole-tree snapshots are
  noisy: `.aegis/**`, `.taskmaster/**`, `docs/ai/work-tracking/**`, `sessions/**`,
  `plans/**`, `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`.

The intended sequence is observe, prove, then automate. Task 141 added the report. Task 143
dogfooded its signal quality. Task 144 prevents accidental promotion to mutation flags.
Task 145 proves read-only behavior at the filesystem side-effect boundary until a future
task earns mutation power explicitly.
