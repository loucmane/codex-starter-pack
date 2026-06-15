---
session_id: 2026-06-15-001
work_context: task188-continuation-contract
handler_target: scripts/_aegis_installer.py
task_ids: [188]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_188.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 188 Install cross-agent natural continuation contract

## Header
- **Session ID (S)**: 2026-06-15-001
- **Work Context (W)**: task188-continuation-contract
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 188
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_188.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Install cross-agent natural continuation contract | docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Install cross-agent natural continuation contract | scripts/codex-task; docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260615-task188-continuation-contract-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_188.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `188`

## Branch Policy
- Working branch: `feat/task-188-continuation-contract`

## Amendments & Versioning
- 2026-06-15 - Task 188 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 188 and its subtasks.
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
