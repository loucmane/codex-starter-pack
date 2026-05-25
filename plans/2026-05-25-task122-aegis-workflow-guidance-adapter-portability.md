---
session_id: 2026-05-25-002
work_context: task122-aegis-workflow-guidance-adapter-portability
handler_target: .taskmaster/tasks/task_122.md
task_ids: [122]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/
  - .taskmaster/tasks/task_122.md
  - .taskmaster/tasks/task_122.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 122 Advance Aegis Workflow Guidance and Adapter Portability

## Header
- **Session ID (S)**: 2026-05-25-002
- **Work Context (W)**: task122-aegis-workflow-guidance-adapter-portability
- **Handler Target (H)**: .taskmaster/tasks/task_122.md
- **Task IDs**: 122
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/, .taskmaster/tasks/task_122.md, .taskmaster/tasks/task_122.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Advance Aegis Workflow Guidance and Adapter Portability | docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Advance Aegis Workflow Guidance and Adapter Portability | scripts/codex-task; docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/IMPLEMENTATION.md; scripts/_aegis_installer.py; aegis_mcp/server.py; docs/aegis/live-acceptance-matrix.md; docs/aegis/agent-adapter-contract.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/reports/task122-verification.md; docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/`
- `.taskmaster/tasks/task_122.md`
- `.taskmaster/tasks/task_122.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `122`

## Branch Policy
- Working branch: `feat/task-122-aegis-workflow-guidance-adapter-portability`

## Amendments & Versioning
- 2026-05-25 - Task 122 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 122 and its subtasks.
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
