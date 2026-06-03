---
session_id: 2026-06-03-004
work_context: task155-semantic-canonicalization-negatives
handler_target: tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
task_ids: [155]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/
  - tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
  - .taskmaster/tasks/task_155.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 155 Harden semantic canonicalization negative tests

## Header
- **Session ID (S)**: 2026-06-03-004
- **Work Context (W)**: task155-semantic-canonicalization-negatives
- **Handler Target (H)**: tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
- **Task IDs**: 155
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/, tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py, .taskmaster/tasks/task_155.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Harden semantic canonicalization negative tests | docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Harden semantic canonicalization negative tests | tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py; docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/reports/semantic-canonicalization-negatives/verification-summary.md; docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260603-task155-semantic-canonicalization-negatives-ACTIVE/`
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`
- `.taskmaster/tasks/task_155.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `155`

## Branch Policy
- Working branch: `feat/task-155-semantic-canonicalization-negatives`

## Amendments & Versioning
- 2026-06-03 - Task 155 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 155 and its subtasks.
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
