# Findings

- 2026-05-07 10:11 CEST - `python3 scripts/codex-task work-tracking scaffold` assumes `docs/ai/work-tracking/active/` exists. A correctly closed between-session repo may not have that directory, so the helper raised `FileNotFoundError` until the parent directory was created. Task 104 should make scaffold/startup helpers tolerate this clean state.
- 2026-05-07 10:11 CEST - `python3 scripts/codex-task wizard kickoff` currently calls broad `task-master generate` after `task-master set-status`. That is unsafe for Task 104 kickoff because the task exists specifically to replace broad generation with targeted task-file updates.
- 2026-05-07 10:13 CEST - Taskmaster `0.43.1` supports `task-master generate --output <dir>` but emits `task_*.md` files. This repo currently tracks `.taskmaster/tasks/task_*.txt`, so the helper needs extension/content compatibility instead of a blind copy.
