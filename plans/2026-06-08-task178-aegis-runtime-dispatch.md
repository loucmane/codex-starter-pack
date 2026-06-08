---
session_id: 2026-06-08-001
work_context: task178-aegis-runtime-dispatch
handler_target: scripts/_aegis_installer.py
task_ids: [178]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/cli.py
  - aegis_mcp/server.py
  - .claude/scripts/gate_lib.py
  - tests/meta_workflow_guard/test_aegis_installer.py
  - tests/meta_workflow_guard/test_aegis_mcp_server.py
  - .taskmaster/tasks/task_178.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 178 Add Aegis dynamic runtime dispatch and update flow

## Header
- **Session ID (S)**: 2026-06-08-001
- **Work Context (W)**: task178-aegis-runtime-dispatch
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 178
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/, scripts/_aegis_installer.py, aegis_foundation/cli.py, aegis_mcp/server.py, .claude/scripts/gate_lib.py, tests/meta_workflow_guard/test_aegis_installer.py, tests/meta_workflow_guard/test_aegis_mcp_server.py, .taskmaster/tasks/task_178.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the dynamic runtime-dispatch boundary so downstream projects can update Aegis fixes without scaffold reinstall | docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/TRACKER.md | completed |
| plan-step-implement | Add dispatcher hook install assets, runtime.env pointer metadata, hook/runtime CLI commands, MCP tools, schemas, and packaged mirrors | scripts/_aegis_installer.py; aegis_foundation/cli.py; aegis_mcp/server.py; .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused regression evidence and confirm Taskmaster dependency health | docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260608-task178-aegis-runtime-dispatch-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `.claude/scripts/gate_lib.py`
- `schemas/aegis/foundation-manifest.schema.json`
- `aegis_foundation/assets/`
- `.taskmaster/tasks/task_178.md`
- `tests/`
- Taskmaster Task `178`

## Branch Policy
- Working branch: `feat/task-178-aegis-runtime-dispatch`

## Amendments & Versioning
- 2026-06-08 - Task 178 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 178 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: downstream projects need one bootstrap refresh to install dispatcher hooks; after that, runtime fixes flow through `aegis runtime update`.

## Conflict & Scope Declaration
- Related plans: Tasks 121, 157, 164, and 176 Aegis workflow hardening.
- Guard cross-check: runtime update is sanctioned Aegis maintenance, not task implementation or live apply enablement.

## Evidence Checklist
- Tracker/session entries for kickoff, implementation, verification, and Taskmaster status
- Focused installer, MCP, and gate regression suite
- Taskmaster dependency validation

## Emergency Bypass Protocol
- No bypass authorized.
