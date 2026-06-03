# Task 154 Add semantic blast-radius validation for reconcile apply – Implementation Notes

## Planned Workstreams
- Added `TaskmasterSemanticDelta` and semantic validation to `aegis_foundation/reconcile_shadow_apply.py`.
- Extended sacrificial cascade validation so the same clone run now returns:
  - path delta verdict (`path_delta_matches_prediction`)
  - semantic delta verdict (`semantic_delta_matches_prediction`)
  - canonicalized Taskmaster semantic diff details
- Canonicalized Taskmaster aggregate content by normalizing task/dependency IDs and version-scoped Taskmaster defaults (`updatedAt`, tag-level metadata, absent-vs-empty `subtasks`) before comparing.
- Enforced that the only surviving semantic change in `.taskmaster/tasks/tasks.json` is the target task status moving to `done`.
- Added generated task markdown validation requiring the target task file to identify the target task and report `Status: done`.
- Threaded semantic validation through the default-off write apparatus in `aegis_foundation/reconcile_apply_runtime.py`.
- Added live apply-time semantic checking after a test-enabled write and before success is reported; semantic drift now rolls back just like path drift.
- Added terminal rollback-failure hard-deny detection from the terminal breadcrumb in kill-switch state.
- Added semantic validation data to apply audit records.

## Tests Added
- Direct semantic diff acceptance for Taskmaster number-to-string ID/dependency normalization.
- Rejection coverage for unrelated task status changes, dependency drift, task insertion, and subtask drift.
- Generated markdown rejection when the target task file does not report the expected `done` status.
- Runtime refusal when fresh sacrificial validation reports a semantic mismatch.
- Runtime rollback when live path delta matches but semantic content diverges inside `tasks.json`.
- Terminal rollback-failure breadcrumb refusal before validation.
- Governed-repo target refusal even when test-only write enablement is set.
