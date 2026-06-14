---
session_id: 2026-06-14-002
work_context: task221-drain-readonly
handler_target: scripts/_aegis_installer.py
task_ids: [221]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_221.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 221 Drain must not accrete read-only events into required closeout evidence

## Header
- **Session ID (S)**: 2026-06-14-002
- **Work Context (W)**: task221-drain-readonly
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 221
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_221.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Drain must not accrete read-only events into required closeout evidence | docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Drain must not accrete read-only events into required closeout evidence | scripts/codex-task; docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260614-task221-drain-readonly-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_221.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `221`

## Branch Policy
- Working branch: `feat/task-221-drain-readonly`

## Amendments & Versioning
- 2026-06-14 - Task 221 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 221 and its subtasks.
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
