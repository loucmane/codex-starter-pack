# Task 29 Template Lifecycle Management

## Status
Task 29 implements the proven current lifecycle gap after scope reconciliation: a non-destructive, portable template lifecycle policy and audit helper over existing metadata and registry systems.

## Scope Decision
- Do not mass-rewrite template statuses.
- Do not move or archive template files automatically.
- Preserve current compatibility statuses such as `beta` and `experimental` by mapping them to canonical lifecycle phases.
- Treat `status: modular` as an ignored aggregate registry marker, not a lifecycle state.
- Leave full version history and rollback to Task 58.

## Implementation
- Added `templates/metadata/template-lifecycle-policy.json` for canonical states, compatibility mappings, transitions, deprecation thresholds, and version bump levels.
- Added `scripts/template_lifecycle.py` for policy loading, transition validation, semver bumping, lifecycle audits, and deprecated-template warnings/recommendations.
- Updated `templates/metadata/template-frontmatter.schema.json` with `review`, `archived`, and lifecycle metadata fields.
- Added machine-readable lifecycle metadata to `templates/behaviors/session/compaction-detection.md`.
- Added `tests/meta_workflow_guard/test_template_lifecycle.py`.

## Evidence
- Scope reconciliation: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/designs/template-lifecycle-scope-reconciliation.md`.
- Focused lifecycle tests: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/reports/template-lifecycle-management/tests-2026-05-08-lifecycle.txt`.
- Lifecycle/registry/guard metadata tests: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/reports/template-lifecycle-management/tests-2026-05-08-lifecycle-registry-guard.txt`.
- Lifecycle audit: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/reports/template-lifecycle-management/lifecycle-audit-2026-05-08.txt`.
- Full pytest: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/reports/template-lifecycle-management/tests-2026-05-08-full-pytest.txt`.

## Active Context
- Branch: `feat/task-29-template-lifecycle-management`.
- Session: `sessions/2026/05/2026-05-08-008-task29-template-lifecycle-management.md`.
- Plan: `plans/2026-05-08-task29-template-lifecycle-management.md`.
- Work tracking: `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/`.

## Next
- Log this Serena memory in the session/tracker.
- Rerun guard, diff-check, and final evidence.
- Mark Taskmaster subtask `29.2` and parent Task `29` done after final verification.