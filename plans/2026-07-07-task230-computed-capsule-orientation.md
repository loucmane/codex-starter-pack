---
session_id: 2026-07-07-001
work_context: task230-computed-capsule-orientation
handler_target: .claude/scripts/brief_lib.py
task_ids: [230]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/
  - .claude/scripts/brief_lib.py
  - .taskmaster/tasks/task_230.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 230 Computed capsule active-task orientation fields

## Header
- **Session ID (S)**: 2026-07-07-001
- **Work Context (W)**: task230-computed-capsule-orientation
- **Handler Target (H)**: .claude/scripts/brief_lib.py
- **Task IDs**: 230
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/, .claude/scripts/brief_lib.py, .taskmaster/tasks/task_230.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Computed capsule active-task orientation fields | docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Computed capsule active-task orientation fields | scripts/codex-task; docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260707-task230-computed-capsule-orientation-ACTIVE/`
- `.claude/scripts/brief_lib.py`
- `.taskmaster/tasks/task_230.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `230`

## Branch Policy
- Working branch: `feat/task-230-computed-capsule-orientation`

## Amendments & Versioning
- 2026-07-07 - Task 230 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 230 and its subtasks.
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
