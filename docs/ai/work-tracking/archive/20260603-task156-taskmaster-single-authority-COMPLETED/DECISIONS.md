# Decisions

- 2026-06-03 — _Pending_ — capture decisions with context.
# Decisions

- Do not call `task-master next` from Aegis; Taskmaster remains the external authority and Aegis remains read-only guidance.
- Treat only a missing `.taskmaster/tasks/tasks.json` path as Taskmaster absent.
- Report invalid Taskmaster payloads as repair-required rather than stale/missing task drift.
