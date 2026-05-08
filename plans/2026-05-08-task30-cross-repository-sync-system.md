---
session_id: 2026-05-08-003
work_context: task30-cross-repository-sync-system
handler_target: .taskmaster/tasks/task_030.txt
task_ids: [30]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/
  - .taskmaster/tasks/task_030.txt
  - scripts/codex-task
  - tests/meta_workflow_guard/test_codex_task.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 30 Build Cross-Repository Sync System

## Header
- **Session ID (S)**: 2026-05-08-003
- **Work Context (W)**: task30-cross-repository-sync-system
- **Handler Target (H)**: .taskmaster/tasks/task_030.txt
- **Task IDs**: 30
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/, .taskmaster/tasks/task_030.txt, scripts/codex-task, tests/meta_workflow_guard/test_codex_task.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile the historical cross-repository sync wording against the current portable foundation and select the proven remaining gap | docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/designs/cross-repository-sync-scope-reconciliation.md | completed |
| plan-step-implement | Implement the selected non-destructive cross-repository sync planner and regression tests | scripts/codex-task; tests/meta_workflow_guard/test_codex_task.py; docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/reports/cross-repository-sync-system/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/`
- `.taskmaster/tasks/task_030.txt`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- Taskmaster Task `30`

## Branch Policy
- Working branch: `feat/task-30-cross-repository-sync-system`

## Amendments & Versioning
- 2026-05-08 - Task 30 kickoff created via the guided wizard flow.
- 2026-05-08 - Scope reconciled against the portable foundation. Task 30 will implement a non-destructive cross-repository sync planner, not auto PR generation, bidirectional sync, or a dashboard.
- 2026-05-08 - Implemented `python3 scripts/codex-task sync plan` with JSON/runbook outputs and focused regression coverage.
- 2026-05-08 - Verified Task 30 with sync-plan evidence, pytest, Taskmaster health, plan sync, work-tracking audit, guard, diff-check, and Serena memory.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 30 and its subtasks.
  3. Review `docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/designs/cross-repository-sync-scope-reconciliation.md` before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the sync planner non-destructive and grounded in existing drift/bootstrap/adoption helpers rather than creating an autonomous sync service.

## Conflict & Scope Declaration
- Related plans: Task 95 drift detection, Task 98 repo-structure config, Tasks 100-102 portable foundation adoption, Task 23 rehearsal planning.
- Guard cross-check: sync planning must preserve plan/tracker/session compliance and must not create branches, commits, pushes, PRs, or bidirectional file writes.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Sync plan/runbook evidence under `reports/cross-repository-sync-system/`
- Stored test, Taskmaster, plan-sync, audit, guard, diff-check, and Serena evidence

## Emergency Bypass Protocol
- No bypass authorized.
