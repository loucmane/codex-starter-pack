# Decisions

- 2026-05-07 10:11 CEST - Prioritize Task 104 ahead of Taskmaster's reported next Task 10. Rationale: targeted Taskmaster generation is a foundation-hardening fix that reduces repeated dirty task-file cleanup across all subsequent tasks.
- 2026-05-07 10:11 CEST - Use manual kickoff for Task 104 instead of `codex-task wizard kickoff`. Rationale: the wizard currently runs broad `task-master generate`, which would repeat the exact failure mode Task 104 is designed to eliminate.
- 2026-05-07 10:13 CEST - Keep Task 104 scoped to targeted generation, not repository-wide generated-task format migration. Existing `.txt` task files should stay `.txt` unless a future task explicitly migrates the generated task-file format.
