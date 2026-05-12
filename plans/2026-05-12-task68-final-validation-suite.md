---
session_id: 2026-05-12-001
work_context: task68-final-validation-suite
handler_target: .taskmaster/tasks/task_068.txt
task_ids: [68]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/
  - .taskmaster/tasks/task_068.txt
  - scripts/codex-task
  - tests/meta_workflow_guard/test_codex_task.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 68 Implement Final Validation Suite

## Header
- **Session ID (S)**: 2026-05-12-001
- **Work Context (W)**: task68-final-validation-suite
- **Handler Target (H)**: .taskmaster/tasks/task_068.txt
- **Task IDs**: 68
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/, .taskmaster/tasks/task_068.txt, scripts/codex-task, tests/meta_workflow_guard/test_codex_task.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical final-validation requirements against the current portable foundation and identify the proven current-state gap | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/designs/final-validation-scope-reconciliation.md | completed |
| plan-step-implement | Implement a final-validation suite helper that orchestrates existing validators, captures per-check evidence, and renders sign-off outputs | scripts/codex-task; tests/meta_workflow_guard/test_codex_task.py; templates/engine/validation/foundation-adoption-guide.md | completed |
| plan-step-verify | Store final validation evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-132639-final-validation-suite.json; docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/`
- `.taskmaster/tasks/task_068.txt`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/engine/validation/foundation-adoption-guide.md`
- Taskmaster Task `68`

## Branch Policy
- Working branch: `feat/task-68-final-validation-suite`

## Amendments & Versioning
- 2026-05-12 - Task 68 kickoff created via the guided wizard flow.
- 2026-05-12 - Scope reconciled from broad historical final-validation wording to a current foundation final-suite orchestrator.
- 2026-05-12 - Implemented and verified the final validation suite helper with Taskmaster Task 68 marked done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 68 and its subtasks.
  3. Review the final-validation scope reconciliation before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: none for Task 68 implementation; archive work tracking after merge.

## Conflict & Scope Declaration
- Related plans: Task 52 CI/CD gates, Task 62 agent compatibility, Task 40 canary rollout, Tasks 16/24 performance and cost validation.
- Guard cross-check: final validation must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- [x] Final validation scope note under `designs/`
- [x] Tracker/session entries for kickoff and implementation progress
- [x] Stored test, final-suite, guard, audit, and diff-check evidence

## Emergency Bypass Protocol
- No bypass authorized.
