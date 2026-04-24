---
session_id: 2026-04-24-004
work_context: task97-template-metrics-dashboard
handler_target: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-metrics-dashboard-draft.md
task_ids: [97]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/
  - docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-metrics-dashboard-draft.md
  - .taskmaster/tasks/task_097.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 97 Template Metrics Dashboard

## Header
- **Session ID (S)**: 2026-04-24-004
- **Work Context (W)**: task97-template-metrics-dashboard
- **Handler Target (H)**: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-metrics-dashboard-draft.md
- **Task IDs**: 97
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/, docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-metrics-dashboard-draft.md, .taskmaster/tasks/task_097.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the metrics schema, source inventory, and output contract for Template Metrics Dashboard | docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/designs/template-metrics-dashboard-design.md | completed |
| plan-step-implement | Build the metrics generator, repo-level report directory, and automation wiring for Template Metrics Dashboard | scripts/template-metrics-dashboard; reports/template-metrics/README.md; docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store dashboard evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/reports/template-metrics-dashboard/; docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task97-template-metrics-dashboard-ACTIVE/`
- `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-metrics-dashboard-draft.md`
- `.taskmaster/tasks/task_097.txt`
- `scripts/template-metrics-dashboard`
- `reports/template-drift/`
- `.plan_state/sync.log`
- `tests/`
- `.github/workflows/`
- Taskmaster Task `97`

## Branch Policy
- Working branch: `feat/task-97-template-metrics-dashboard`

## Amendments & Versioning
- 2026-04-24 - Task 97 kickoff created via the guided wizard flow.
- 2026-04-24 - Normalized the kickoff artifacts after the wizard baseline fix so the plan reflects the actual metrics dashboard scope.
- 2026-04-24 - Completed the scope and implementation phases after landing the metrics generator, report docs, tests, and CI automation.
- 2026-04-24 - Completed verification after storing dashboard outputs, passing guard/tests, and marking Taskmaster Task 97 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 97 and its subtasks.
  3. Review the metrics dashboard design artifact and the archived draft baseline.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the metrics dashboard grounded in existing repo data sources rather than introducing a separate datastore or service.

## Conflict & Scope Declaration
- Related plans: Task 95 drift reporting, Task 96 guided kickoff flow, and Task 97 dashboard aggregation.
- Guard cross-check: dashboard automation must reuse existing report sources and avoid creating a second enforcement authority.

## Evidence Checklist
- Metrics design note under `designs/`
- Tracker/session entries for kickoff repair and implementation progress
- Stored script output, tests, and guard evidence under the Task 97 reports folder

## Emergency Bypass Protocol
- No bypass authorized.
