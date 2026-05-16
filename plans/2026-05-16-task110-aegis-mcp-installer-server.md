---
session_id: 2026-05-16-002
work_context: task110-aegis-mcp-installer-server
handler_target: aegis_mcp/server.py
task_ids: [110]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/
  - aegis_mcp/server.py
  - scripts/aegis-mcp-server
  - .taskmaster/tasks/task_110.md
  - tests/meta_workflow_guard/test_aegis_mcp_server.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 110 Build Aegis MCP Installer Server

## Header
- **Session ID (S)**: 2026-05-16-002
- **Work Context (W)**: task110-aegis-mcp-installer-server
- **Handler Target (H)**: aegis_mcp/server.py
- **Task IDs**: 110
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/, aegis_mcp/server.py, scripts/aegis-mcp-server, .taskmaster/tasks/task_110.md, tests/meta_workflow_guard/test_aegis_mcp_server.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the Aegis MCP server boundary, tool/resource/prompt inventory, implementation sequence, and verification gates | docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/designs/aegis-mcp-server-scope.md | completed |
| plan-step-implement | Implement the MCP server module, stdio entrypoint, V1-backed tool handlers, read-only resources, workflow prompts, and tests | docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/`
- `aegis_mcp/server.py`
- `scripts/aegis-mcp-server`
- `.taskmaster/tasks/task_110.md`
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`
- `tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py`
- `tests/`
- Taskmaster Task `110`

## Branch Policy
- Working branch: `feat/task-110-aegis-mcp-installer-server`

## Amendments & Versioning
- 2026-05-16 - Task 110 kickoff created via the guided wizard flow.
- 2026-05-16 - Scope corrected from generic wizard wording to Aegis MCP server implementation boundaries.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 110 and its subtasks.
  3. Review `designs/aegis-mcp-server-scope.md` before changing MCP server behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the MCP server as a thin wrapper over `scripts/_aegis_installer.py`; do not duplicate installer logic or expose deferred mutating tools before deterministic core support exists.

## Conflict & Scope Declaration
- Related plans: Task 109 Aegis foundation installer contract, Task 62 agent compatibility layer, Task 103 Claude runtime adapter, Task 107 direct git execution mode.
- Guard cross-check: MCP tooling must preserve the Aegis gate contract and never tell agents to write `.aegis/` directly.

## Evidence Checklist
- Aegis MCP server scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
