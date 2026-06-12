---
session_id: 2026-06-11-005
work_context: task213-per-session-ab
handler_target: .claude/scripts/brief_lib.py
task_ids: [213]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/
  - .claude/scripts/brief_lib.py
  - .taskmaster/tasks/task_213.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 213 Per-session hashed capsule A/B assignment

## Header
- **Session ID (S)**: 2026-06-11-005
- **Work Context (W)**: task213-per-session-ab
- **Handler Target (H)**: .claude/scripts/brief_lib.py
- **Task IDs**: 213
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/, .claude/scripts/brief_lib.py, .taskmaster/tasks/task_213.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Per-session hashed capsule A/B assignment | docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Per-session hashed capsule A/B assignment | scripts/codex-task; docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260611-task213-per-session-ab-ACTIVE/`
- `.claude/scripts/brief_lib.py`
- `.taskmaster/tasks/task_213.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `213`

## Branch Policy
- Working branch: `feat/task-213-per-session-ab`

## Amendments & Versioning
- 2026-06-11 - Task 213 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 213 and its subtasks.
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
