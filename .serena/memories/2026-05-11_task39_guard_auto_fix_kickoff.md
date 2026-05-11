# Task 39 Guard Auto-Fix Kickoff

Date: 2026-05-11 18:20 CEST
Branch: feat/task-39-guard-auto-fix-mode
Task: 39 - Implement Auto-Fix Mode for Guard

Current state:
- Task 39 was moved to in-progress and targeted task file generation updated `.taskmaster/tasks/task_039.txt`.
- Guided kickoff created `sessions/2026/05/2026-05-11-004-task39-guard-auto-fix-mode.md`, `plans/2026-05-11-task39-guard-auto-fix-mode.md`, and active work tracking at `docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/`.
- `sessions/current`, `plans/current`, and `sessions/state.json` point to Task 39.
- Scope reconciliation corrected the generated plan from generic wizard language to `scripts/codex-guard` auto-fix mode.

Decision:
- Implement a bounded, preview-first auto-fix framework for `python3 scripts/codex-guard validate`.
- Initial safe fixer: `tracker-last-updated`, limited to active work-tracking `TRACKER.md` metadata.
- Do not auto-create sessions, plans, Taskmaster state, S:W:H:E entries, templates, or evidence.

Next steps:
- Implement CLI options: `--fix-preview`, `--auto-fix`, optional `--fix-kind`, optional `--fix-history`.
- Add focused tests in `tests/meta_workflow_guard/test_guard_rules.py`.
- Capture evidence under the Task 39 active folder before closeout.