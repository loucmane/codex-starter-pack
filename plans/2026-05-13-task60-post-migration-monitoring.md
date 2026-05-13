---
session_id: 2026-05-13-005
work_context: task60-post-migration-monitoring
handler_target: .taskmaster/tasks/task_060.txt
task_ids: [60]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/
  - .taskmaster/tasks/task_060.txt
  - .taskmaster/tasks/task_060.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 60 Setup Post-Migration Monitoring

## Header
- **Session ID (S)**: 2026-05-13-005
- **Work Context (W)**: task60-post-migration-monitoring
- **Handler Target (H)**: .taskmaster/tasks/task_060.txt
- **Task IDs**: 60
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/, .taskmaster/tasks/task_060.txt, .taskmaster/tasks/task_060.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical production-monitoring scope against current static telemetry, migration-health, and migration KPI surfaces | docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/designs/post-migration-monitoring-scope-reconciliation.md | completed |
| plan-step-implement | Add a static post-migration monitoring packet over existing migration metrics and migration-health reports | scripts/codex-task; reports/post-migration-monitoring/README.md; tests/meta_workflow_guard/test_codex_task.py; docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/tests-2026-05-13-codex-task.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/taskmaster-show-60-2026-05-13.txt; docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/reports/post-migration-monitoring/taskmaster-health-2026-05-13.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/`
- `.taskmaster/tasks/task_060.txt`
- `.taskmaster/tasks/task_060.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `60`

## Branch Policy
- Working branch: `feat/task-60-post-migration-monitoring`

## Amendments & Versioning
- 2026-05-13 - Task 60 kickoff created via the guided wizard flow.
- 2026-05-13 - Reconciled Task 60 from live production-monitoring wording to a portable static post-migration monitoring packet.
- 2026-05-13 - Implemented `codex-task migration monitoring`, generated task-local monitoring evidence, and confirmed focused codex-task tests pass.
- 2026-05-13 - Marked Taskmaster Task 60 and subtasks done; captured handoff evidence and completion memory.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 60 and its subtasks.
  3. Review the post-migration monitoring scope reconciliation before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep monitoring static and evidence-backed; do not introduce live services, schedulers, alert delivery, or production observability integrations without a future task proving that runtime need.

## Conflict & Scope Declaration
- Related plans: Tasks 17, 37, 41, 55, 68, and 97 static telemetry/reporting foundation.
- Guard cross-check: monitoring work must preserve plan/tracker/session compliance and avoid fabricated live telemetry.

## Evidence Checklist
- Post-migration monitoring scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
