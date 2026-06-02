# Findings

- 2026-06-02 — Task 147 must remain report/contract-only. Reconcile implementation,
  CLI, MCP, and parser surfaces were intentionally left untouched.
- 2026-06-02 — The real isolated Taskmaster done cascade changes only
  `.taskmaster/tasks/tasks.json` and generated markdown `.taskmaster/tasks/task_042.md`.
  `.taskmaster/state.json` is present but unchanged by the done cascade.
- 2026-06-02 — The repo-specific `scripts/codex-task taskmaster generate-one` helper is
  intentionally checkout-bound and not suitable as an isolated fixture primitive; native
  `task-master generate` is used inside the temp fixture for generated markdown refresh.
