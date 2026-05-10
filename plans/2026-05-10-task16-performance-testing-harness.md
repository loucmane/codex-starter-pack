---
session_id: 2026-05-10-001
work_context: task16-performance-testing-harness
handler_target: .taskmaster/tasks/task_016.txt
task_ids: [16]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/
  - .taskmaster/tasks/task_016.txt
  - scripts/template-performance-harness
  - templates/metadata/template-performance-policy.json
plan_version: v1
emergency_bypass: false
---

# Plan - Task 16 Create Performance Testing Harness

## Header
- **Session ID (S)**: 2026-05-10-001
- **Work Context (W)**: task16-performance-testing-harness
- **Handler Target (H)**: .taskmaster/tasks/task_016.txt
- **Task IDs**: 16
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/, .taskmaster/tasks/task_016.txt, .taskmaster/tasks/task_016.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical performance-harness wording against the current portable foundation and select the proven implementation gap | docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/designs/performance-testing-scope-reconciliation.md | completed |
| plan-step-implement | Implement the portable performance policy, harness, report integration, CI wiring, and focused regression tests | scripts/template-performance-harness; templates/metadata/template-performance-policy.json; docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store performance report evidence, refresh handoff docs, run guard/tests, and confirm Taskmaster status | docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/`
- `.taskmaster/tasks/task_016.txt`
- `scripts/template-performance-harness`
- `templates/metadata/template-performance-policy.json`
- `reports/template-performance/`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `16`

## Branch Policy
- Working branch: `feat/task-16-performance-testing-harness`

## Amendments & Versioning
- 2026-05-10 - Task 16 kickoff created via the guided wizard flow.
- 2026-05-10 - Replaced generic wizard wording with the evidence-backed performance harness scope and marked `plan-step-scope` complete.
- 2026-05-10 - Added the performance policy, harness, report integration, CI wiring, and focused regression tests; marked `plan-step-implement` complete.
- 2026-05-10 - Captured full verification evidence and marked `plan-step-verify` complete.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 16 and its subtasks.
  3. Review the performance scope reconciliation before adding harness behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep Task 16 scoped to reportable performance measurement and regression classification; leave deep optimization to Task 61 unless this task proves a current bottleneck.

## Conflict & Scope Declaration
- Related plans: Task 1 performance baseline, Task 17 static monitoring, Task 25 Phase 0 validation, Task 45 scanner optimization, Task 61 discovery optimization.
- Guard cross-check: performance harness reports must preserve plan/tracker/session compliance and avoid committing scanner runtime output.

## Evidence Checklist
- Performance scope reconciliation under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored performance report, test, guard, plan-sync, audit, and Taskmaster evidence once implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
