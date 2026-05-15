---
session_id: 2026-05-15-008
work_context: task109-foundation-installer-mcp
handler_target: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
task_ids: [109]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
  - .taskmaster/tasks/task_109.md
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 109 Portable Foundation Installer and MCP Distribution Contract

## Header
- **Session ID (S)**: 2026-05-15-008
- **Work Context (W)**: task109-foundation-installer-mcp
- **Handler Target (H)**: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
- **Task IDs**: 109
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/, docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md, .taskmaster/tasks/task_109.md, docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Document the portable foundation installer and MCP distribution architecture, including alternatives, chosen direction, manifest/profile model, tool contract, and test strategy | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md | completed |
| plan-step-implement | Implement or further specify the manifest/profile schema, CLI command surface, fixture strategy, and MCP wrapper contract from the approved architecture | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status, guard, work-tracking audit, and diff-check | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/`
- `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md`
- `.taskmaster/tasks/task_109.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `109`

## Branch Policy
- Working branch: `feat/task-109-foundation-installer-mcp`

## Amendments & Versioning
- 2026-05-15 - Task 109 kickoff created via the guided wizard flow.
- 2026-05-15 - Corrected the generic kickoff plan wording to the actual installer/MCP architecture scope and completed plan-step-scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 109 and its subtasks.
  3. Review the foundation installer/MCP architecture artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the MCP server as a wrapper around the deterministic CLI/library core rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Foundation installer/MCP architecture note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
