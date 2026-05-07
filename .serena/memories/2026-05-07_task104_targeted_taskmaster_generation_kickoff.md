# Task 104 Kickoff - Targeted Taskmaster Generation

Date: 2026-05-07
Branch: feat/task-104-targeted-taskmaster-generation-helper
Session: sessions/2026/05/2026-05-07-001-task104-targeted-taskmaster-generation-helper.md
Plan: plans/2026-05-07-task104-targeted-taskmaster-generation-helper.md
Tracker: docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/TRACKER.md

Task 104 is intentionally prioritized before Taskmaster's reported next Task 10 because it fixes recurring Taskmaster task-file generation drift. The existing `codex-task wizard kickoff` currently calls broad `task-master generate`, so Task 104 started with manual session/plan/work-tracking scaffolding to avoid repeating the issue it is meant to solve.

Initial findings:
- `codex-task work-tracking scaffold` assumes `docs/ai/work-tracking/active/` exists and fails in a clean between-session state when that parent directory is absent.
- Taskmaster 0.43.1 can generate `task_*.md` while the repo currently tracks `task_*.txt`, and broad in-place generation can dirty unrelated generated task files.

Next steps:
1. Complete `designs/targeted-taskmaster-generation.md` with helper contract and Taskmaster 0.43.1 behavior.
2. Implement `python3 scripts/codex-task taskmaster generate-one --id <task-id>`.
3. Update wizard/status workflow docs to use targeted generation where broad generation is not needed.
4. Run focused tests, plan sync, work-tracking audit, guard, diff-check, pre-commit, and Taskmaster validation.