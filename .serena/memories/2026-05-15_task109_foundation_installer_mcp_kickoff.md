# Task 109 Foundation Installer/MCP Kickoff - 2026-05-15

Task 109 was created after the original 108-task backlog reached 108/108 done. Purpose: turn the completed Codex starter-pack foundation into a reusable portable system for new and existing repositories.

Current branch: `feat/task-109-foundation-installer-mcp`.

Taskmaster state:
- Parent task: 109 - Build Portable Foundation Installer and MCP Distribution Contract, status `in-progress`.
- Subtasks:
  - 109.1 Document installer architecture and distribution decision - done.
  - 109.2 Define foundation manifest, profiles, and install-plan schema - pending.
  - 109.3 Design CLI installer lifecycle and verification commands - pending.
  - 109.4 Specify fixture, idempotence, rollback, and cross-agent tests - pending.
  - 109.5 Define MCP wrapper contract and evidence handoff - pending.

Key decision: deterministic CLI/library core with optional MCP wrapper. The CLI/library owns inspect, plan-install, install, verify, update, rollback, manifest handling, reports, and tests. The MCP server should be an agent-facing control plane over that same core, exposing tools/resources/prompts without duplicating installer logic.

Main design artifact: `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md`.

Relevant workflow files:
- Session: `sessions/2026/05/2026-05-15-008-task109-foundation-installer-mcp.md`
- Plan: `plans/2026-05-15-task109-foundation-installer-mcp.md`
- Tracker: `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/TRACKER.md`

Important finding: AI-backed `task-master add-task --prompt ...` hung through the Claude Code provider. The task was created with manual Taskmaster fields instead to avoid another model rewriting the agreed scope.

Next logical step: 109.2, define `.codex/foundation-manifest.json`, project profiles, install-plan schema, conflict classes, and dry-run/apply semantics.