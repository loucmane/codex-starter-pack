# Task 95 Template Drift Detection Kickoff

- Date confirmed: 2026-04-24 14:15:14 CEST +0200
- Branch: `feat/task-95-template-drift-detection`
- Taskmaster: Task 95 set to `in-progress`
- Archived Task 94 active folder to `docs/ai/work-tracking/archive/20260424-task94-expand-enforcement-framework-COMPLETED/`
- Active tracker: `docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/`
- Current session: `sessions/2026/04/2026-04-24-002-task95-template-drift-detection.md`
- Current plan: `plans/2026-04-24-task95-template-drift-detection.md`

## Design baseline
- The archived drift-detection note is still draft-only; live `scripts/codex-guard` currently exposes `validate` only.
- Task 95 should implement `python3 scripts/codex-guard drift-check` inside the existing enforcement entrypoint, not as a parallel tool.
- First implementation scope should stay deterministic: canonical-doc drift, template metadata drift, and explicitly mapped workflow-surface drift.
- Repo-level outputs should live under `reports/template-drift/`; task-local evidence stays under the Task 95 active folder.

## Next steps
1. Implement the `drift-check` subcommand and reporting structures in `scripts/codex-guard`.
2. Add regression tests in `tests/meta_workflow_guard`.
3. Add repo-level report documentation and then run plan sync + guard.
