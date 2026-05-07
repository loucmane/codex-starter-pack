# Decisions

- 2026-05-07 — Implement rollback as a non-destructive `scripts/codex-task rollback` helper, not as automatic reset/restore execution.
- 2026-05-07 — Keep optional git tagging explicit via `--create-tag`; checkpoint manifests are useful without creating tags during every task.
- 2026-05-07 — Treat Serena memory backup as inventory capture in the checkpoint manifest. Do not copy or rewrite memory files as part of rollback.
