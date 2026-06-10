---
session_id: 2026-06-11-001
work_context: task200-mcp-version-handshake
handler_target: .taskmaster/tasks/task_200.md
task_ids: [200]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/
  - .taskmaster/tasks/task_200.md
  - .taskmaster/tasks/task_200.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 200 Aegis MCP CLI version handshake

## Header
- **Session ID (S)**: 2026-06-11-001
- **Work Context (W)**: task200-mcp-version-handshake
- **Handler Target (H)**: .taskmaster/tasks/task_200.md
- **Task IDs**: 200
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/, .taskmaster/tasks/task_200.md, .taskmaster/tasks/task_200.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the handshake design: startup fingerprint, per-call recheck in run_tool, refuse-mutations/warn-reads split, runtime_status surfacing | docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/designs/handshake-scope.md | completed |
| plan-step-implement | Implement runtime_fingerprint + run_tool staleness gate + runtime_status surfacing in aegis_mcp/server.py | aegis_mcp/server.py; docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | 5 handshake tests incl. the HP-Coach repro (stale repair refused before any plan), full suite + guard stack | docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260611-task200-mcp-version-handshake-ACTIVE/`
- `.taskmaster/tasks/task_200.md`
- `.taskmaster/tasks/task_200.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `200`

## Branch Policy
- Working branch: `feat/task-200-mcp-version-handshake`

## Amendments & Versioning
- 2026-06-11 - Task 200 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 200 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
