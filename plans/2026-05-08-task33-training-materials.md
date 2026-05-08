---
session_id: 2026-05-08-009
work_context: task33-training-materials
handler_target: .taskmaster/tasks/task_033.txt
task_ids: [33]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/
  - .taskmaster/tasks/task_033.txt
  - templates/guides/training/foundation-onboarding.md
  - templates/guides/index.md
  - tests/meta_workflow_guard/test_training_materials.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 33 Setup Training Materials

## Header
- **Session ID (S)**: 2026-05-08-009
- **Work Context (W)**: task33-training-materials
- **Handler Target (H)**: .taskmaster/tasks/task_033.txt
- **Task IDs**: 33
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/, .taskmaster/tasks/task_033.txt, templates/guides/training/foundation-onboarding.md, templates/guides/index.md, tests/meta_workflow_guard/test_training_materials.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical training-material wording against current portable foundation and runtime docs | docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/designs/training-materials-scope-reconciliation.md | completed |
| plan-step-implement | Add current foundation onboarding/training material, guide navigation, and focused tests | templates/guides/training/foundation-onboarding.md; templates/guides/index.md; tests/meta_workflow_guard/test_training_materials.py; docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/reports/training-materials/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/`
- `.taskmaster/tasks/task_033.txt`
- `templates/guides/training/foundation-onboarding.md`
- `templates/guides/index.md`
- `tests/meta_workflow_guard/test_training_materials.py`
- `tests/`
- Taskmaster Task `33`

## Branch Policy
- Working branch: `feat/task-33-training-materials`

## Amendments & Versioning
- 2026-05-08 - Task 33 kickoff created via the guided wizard flow.
- 2026-05-08 - Corrected plan scope from generic wizard wording to current training/onboarding material after evidence review.
- 2026-05-08 - Added current foundation onboarding training, repaired guide-hub navigation, and added focused training-material tests.
- 2026-05-08 - Stored training tests, full pytest, Serena, Taskmaster health, plan-sync, work-tracking audit, guard, and diff-check evidence; Taskmaster Task 33 is done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 33 and its subtasks.
  3. Review the training scope reconciliation artifact before changing guide behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: PR checks still need to pass before merge; keep broader historical guide cleanup separate from this focused training-material task.

## Conflict & Scope Declaration
- Related plans: Task 31 compaction protocol, Task 8 template registry, Task 29 template lifecycle, Task 103/105/106 Claude runtime adapter and smoke tests, Task 99 portable foundation.
- Guard cross-check: training material must use governed guide metadata and should point to current existing files.

## Evidence Checklist
- Training scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored focused training-material, metadata/guide guard selection, full pytest, Taskmaster health, plan-sync, work-tracking audit, guard, and diff-check evidence under `reports/training-materials/`
- Serena memory: `.serena/memories/2026-05-08_task33_training_materials.md`

## Emergency Bypass Protocol
- No bypass authorized.
