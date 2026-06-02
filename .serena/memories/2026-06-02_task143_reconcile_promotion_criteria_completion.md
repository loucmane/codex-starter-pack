# Task 143 Reconcile Promotion Criteria

Task 143 dogfooded `aegis reconcile` against three additional safe fixture histories under `/tmp/aegis-task143-reconcile-promotion-fixtures-1780398438` on branch `feat/task-143-reconcile-promotion-criteria`.

Evidence directory: `docs/ai/work-tracking/active/20260602-task143-reconcile-promotion-criteria-ACTIVE/reports/reconcile-promotion-criteria/`.

Targets/results:
- `squash-offline`: no-GitHub squash-shaped history stayed `clean`; Task 201 merge truth remained `unknown` with proof `git_only_non_ancestor_or_missing_base`, preventing false certainty.
- `drift-mixed`: no-GitHub produced one true `merged_but_not_done` error for Task 202 via `git_ancestor`; fixture GitHub metadata added one true `done_but_not_merged` error for Task 205 via `github_pr_open`.
- `ambiguity-stubs`: warning-only manual-review findings for abandoned in-progress branch, stale local stub, local ad hoc stub, and multi-PR ambiguity when fixture GitHub metadata was available.

All fixture before/after `git status --short` diffs were empty. Task 143 remains report-first: no auto-status mutation, Taskmaster mutation, git ref mutation, PR mutation, closeout automation, or Aegis state mutation was implemented.

Promotion criteria captured in `promotion-criteria-summary.md`: future auto-mutation must remain a separate task, default reconcile stays read-only, warning kinds remain manual-only, squash-shaped no-GitHub cases stay unknown, and any automatable `merged_but_not_done` path requires high-confidence proof plus explicit operator/audit/rollback controls.