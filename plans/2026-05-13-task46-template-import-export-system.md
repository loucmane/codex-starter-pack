---
session_id: 2026-05-13-006
work_context: task46-template-import-export-system
handler_target: .taskmaster/tasks/task_046.txt
task_ids: [46]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/
  - .taskmaster/tasks/task_046.txt
  - .taskmaster/tasks/task_046.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 46 Create Template Import/Export System

## Header
- **Session ID (S)**: 2026-05-13-006
- **Work Context (W)**: task46-template-import-export-system
- **Handler Target (H)**: .taskmaster/tasks/task_046.txt
- **Task IDs**: 46
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/, .taskmaster/tasks/task_046.txt, .taskmaster/tasks/task_046.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical template import/export scope against the current registry, metadata, bootstrap, lifecycle, and sync foundation | docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/designs/template-import-export-scope-reconciliation.md | completed |
| plan-step-implement | Implement the selected non-destructive template bundle-plan helper and focused regression coverage | scripts/codex-task; tests/meta_workflow_guard/test_codex_task.py; docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/reports/template-import-export-system/bundle-plan-2026-05-13.json; docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/reports/template-import-export-system/tests-2026-05-13-codex-task.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/reports/template-import-export-system/guard-2026-05-13.txt; docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/reports/template-import-export-system/taskmaster-health-2026-05-13.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260513-task46-template-import-export-system-ACTIVE/`
- `.taskmaster/tasks/task_046.txt`
- `.taskmaster/tasks/task_046.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `46`

## Branch Policy
- Working branch: `feat/task-46-template-import-export-system`

## Amendments & Versioning
- 2026-05-13 - Task 46 kickoff created via the guided wizard flow.
- 2026-05-13 - Scope reconciled to a local non-destructive template bundle-plan helper rather than marketplace/signing/package extraction work.
- 2026-05-13 - Implemented `codex-task template bundle-plan`, generated real bundle-plan evidence, and captured focused `test_codex_task.py` regression output.
- 2026-05-13 - Taskmaster Task 46 and subtasks 46.1/46.2 marked done; verification evidence captured.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 46 and its subtasks.
  3. Review `designs/template-import-export-scope-reconciliation.md` before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep import/export behavior grounded in the existing registry, metadata, bootstrap, lifecycle, and sync helpers rather than creating a parallel package manager.

## Conflict & Scope Declaration
- Related plans: Tasks 8, 13, 21, 22, 29, 30, 58, and 100 define registry, metadata, compatibility, lifecycle, sync, versioning, and bootstrap boundaries.
- Guard cross-check: bundle planning must remain non-destructive and preserve plan/tracker/session compliance.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
