# Task 96 Interactive Template Wizard Kickoff

- Date confirmed: 2026-04-24 15:03:13 CEST +0200
- Branch: `feat/task-96-interactive-template-wizard`
- Taskmaster: Task 96 set to `in-progress`
- Archived Task 95 active folder to `docs/ai/work-tracking/archive/20260424-task95-template-drift-detection-COMPLETED/`
- Active tracker: `docs/ai/work-tracking/active/20260424-task96-interactive-template-wizard-ACTIVE/`
- Current session: `sessions/2026/04/2026-04-24-003-task96-interactive-template-wizard.md`
- Current plan: `plans/2026-04-24-task96-interactive-template-wizard.md`

## Scope baseline
- Implement the first wizard slice as `python3 scripts/codex-task wizard kickoff`.
- Keep the wizard inside `scripts/codex-task` so it reuses the existing work-tracking/session/plan helpers.
- Enforce the task branch prefix and seed initial `plan sync` as part of kickoff.
- Do not broaden into multi-template orchestration or Serena memory automation in this task.

## Implementation status
- `codex-task wizard kickoff` now scaffolds active work tracking, creates the session and plan files, repoints current symlinks/state, runs initial plan sync, and marks the Taskmaster task in progress.
- Regression coverage added in `tests/meta_workflow_guard/test_codex_task.py`.
- Usage documented in `templates/TOOLS.md` and `templates/workflows/taskmaster/work-tracking-enforcement.md`.

## Next steps
1. Run final verification (`pytest`, `plan sync`, `codex-guard validate`) and store evidence under the Task 96 reports folder.
2. Mark Taskmaster subtasks and parent task done if verification remains clean.
3. Prepare closeout summary and commit guidance.
