# Findings

- 2026-05-15 — [S:20260515|W:task109-foundation-installer-mcp|H:task-master:add-task|E:cmd`task-master add-task --prompt ...`] The AI-backed Taskmaster add-task path can hang when routed through the Claude Code provider and optional MCP startup. Manual Taskmaster task creation is safer when the scope is already known.
- 2026-05-15 — [S:20260515|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md] Portability needs both installer mechanics and verification evidence. Copying files is insufficient unless target repos can prove guard, Taskmaster health, work-tracking audit, plan sync, diff-check, and agent runtime gates where applicable.
