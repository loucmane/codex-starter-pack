# Findings

- 2026-05-07 — Commit guidance was internally inconsistent. Some templates already allowed Codex to run Git/GitHub commands directly when SSH/GPG cache is active, while the canonical commit-format and commit-message handler still framed `gac` as mandatory/manual.
- 2026-05-07 — The conflict caused a live regression after Task 106: Codex returned a `gac "..."` handoff instead of using regular Git/GitHub commands after the user had delegated Git execution.
- 2026-05-07 — Taskmaster AI-backed `add-task` hung for this task, but manual Taskmaster fields succeeded and preserved Taskmaster as the source of truth without manual `tasks.json` edits.
- 2026-05-07 — The stale default was broader than the first three canonical files. Top-level convention, behavior, registry, matrix, tool-selection, session-end, and Git-command references also needed direct Git/default-mode alignment.
