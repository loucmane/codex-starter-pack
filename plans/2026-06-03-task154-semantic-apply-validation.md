---
session_id: 2026-06-03-003
work_context: task154-semantic-apply-validation
handler_target: aegis_foundation/reconcile_shadow_apply.py
task_ids: [154]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/
  - aegis_foundation/reconcile_shadow_apply.py
  - .taskmaster/tasks/task_154.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 154 Add semantic blast-radius validation for reconcile apply

## Header
- **Session ID (S)**: 2026-06-03-003
- **Work Context (W)**: task154-semantic-apply-validation
- **Handler Target (H)**: aegis_foundation/reconcile_shadow_apply.py
- **Task IDs**: 154
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/, aegis_foundation/reconcile_shadow_apply.py, .taskmaster/tasks/task_154.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Add semantic blast-radius validation for reconcile apply | docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Add semantic blast-radius validation for reconcile apply | scripts/codex-task; docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260603-task154-semantic-apply-validation-ACTIVE/`
- `aegis_foundation/reconcile_shadow_apply.py`
- `.taskmaster/tasks/task_154.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `154`

## Branch Policy
- Working branch: `feat/task-154-semantic-apply-validation`

## Amendments & Versioning
- 2026-06-03 - Task 154 kickoff created via the guided wizard flow.
- 2026-06-03 - Scope evidence captured for semantic apply validation before source edits.
- 2026-06-03 - Semantic apply validation implementation and focused tests completed.
- 2026-06-03 - Verification evidence captured for focused, adjacent, lint, core regression, guard, and Taskmaster health checks.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 154 and its subtasks.
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
