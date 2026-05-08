# Decisions

- 2026-05-08 — Implement Task 31 as `python3 scripts/codex-task compaction checkpoint`, not as a parallel rollback manager. Rollback remains the recovery/risk-control path; compaction checkpointing is the continuation path for context reset.
- 2026-05-08 — The helper must preserve active workflow state. It must not archive work tracking, clear `sessions/current`, clear `plans/current`, generate commit guidance, or end the session.
- 2026-05-08 — Compaction memories are written as durable `.serena/memories/*.md` files by the helper, while separate MCP Serena memories remain the verification evidence for agent continuity when finalizing the task.
