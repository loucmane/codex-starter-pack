# Findings

- 2026-06-09 — HP-Coach exposed a recovery deadlock: doctor preview reported one safe `workflow.normalize_plan_table` action, but both CLI and MCP `aegis repair --apply` were blocked because readiness was already BLOCKED by the malformed completed observation state.
- 2026-06-09 — The fix must support both CLI and MCP repair apply because the Claude PreToolUse hook governs both channels.
