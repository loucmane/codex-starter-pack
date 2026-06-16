---
session_id: 2026-06-15-003
work_context: task225-doctor-repair-states
handler_target: scripts/_aegis_installer.py
task_ids: [225]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - .taskmaster/tasks/task_225.md
  - tests/
plan_version: v1
emergency_bypass: false
---

# Plan - Task 225 Surface doctor safe-repair vs manual-review states in aegis next

## Header
- **Session ID (S)**: 2026-06-15-003
- **Work Context (W)**: task225-doctor-repair-states
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 225
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_225.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design (via workflow) how next_action surfaces doctor safe-repair vs manual-review: severity-gated detection, injection after scaffold, normalize_plan_table exclusion | docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | _repair_plan_split + severity-gated repair branch in next_action (safe_repair_available / manual_review_repair) + CONTINUATION_BRIEF_BY_STATE entries; assets mirror; tests | scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Design + adversarial-review workflows; Finding #2 fixed + regression-tested; focused 20 + installer/MCP/replay/parity 175 + full suite green | docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/reports/task225-doctor-repair-states/tests-2026-06-15-final.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260615-task225-doctor-repair-states-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_225.md`
- `tests/`
- Taskmaster Task `225`

## Branch Policy
- Working branch: `feat/task-225-doctor-repair-states`

## Amendments & Versioning
- 2026-06-15 - Task 225 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 225 and its subtasks.
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
