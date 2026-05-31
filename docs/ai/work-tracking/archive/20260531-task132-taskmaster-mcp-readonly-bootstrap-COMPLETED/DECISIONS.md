# Decisions

- 2026-05-31 — Use a Taskmaster-specific MCP discovery allowlist in `gate_lib.py` before the generic MCP regexes. This prevents broad read-only verbs from widening Taskmaster permissions accidentally.
- 2026-05-31 — Normalize MCP tool names once with lowercasing plus dot/hyphen replacement, and support both `mcp__taskmaster_ai__*` and `mcp__taskmaster-ai__*` spellings.
- 2026-05-31 — Keep post-closeout Taskmaster completion behavior unchanged: matching `set_task_status done/completed` and generated-file refresh remain the only allowed post-closeout Taskmaster mutation path.
