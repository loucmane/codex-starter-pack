# Findings

- 2026-05-31 — The generic MCP classifier already allowed broad read-only verbs such as `get_*`, but Taskmaster needed an explicit positive discovery allowlist so adjacent or unknown Taskmaster MCP actions cannot be treated as safe by broad regex drift.
- 2026-05-31 — The live-agent failure mode from Task 131 was a bootstrap discovery gap: agents need to identify the external Taskmaster numeric task while readiness is still `BLOCKED`, before Aegis can create the task branch/session/plan/work-tracking scaffold.
- 2026-05-31 — The safe boundary is narrow: `help`, `get_tasks`, `next_task`, and `get_task` are read-only; Taskmaster MCP mutations, aliases outside that set, and unknown Taskmaster MCP tools remain persistent by default.
