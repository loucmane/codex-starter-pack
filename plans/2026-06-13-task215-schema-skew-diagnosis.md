---
session_id: 2026-06-13-001
work_context: task215-schema-skew-diagnosis
handler_target: scripts/_aegis_installer.py
task_ids: [215]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_215.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 215 Verify schema-skew self-diagnosis

## Header
- **Session ID (S)**: 2026-06-13-001
- **Work Context (W)**: task215-schema-skew-diagnosis
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 215
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_215.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Verify schema-skew self-diagnosis | docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Verify schema-skew self-diagnosis | scripts/codex-task; docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260613-task215-schema-skew-diagnosis-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_215.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `215`

## Branch Policy
- Working branch: `feat/task-215-schema-skew-diagnosis`

## Amendments & Versioning
- 2026-06-13 - Task 215 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 215 and its subtasks.
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
