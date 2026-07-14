---
session_id: 2026-07-14-001
work_context: task250-autonomous-delivery-executor-stability
handler_target: .github/workflows/aegis-autonomous-delivery.yml
task_ids: [250]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/
  - docs/ai/work-tracking/archive/20260713-task249-codex-hook-update-migration-COMPLETED/
  - .serena/memories/2026-07-14_task250_autonomous_delivery_executor_stability.md
  - .github/workflows/aegis-autonomous-delivery.yml
  - scripts/aegis-delivery-policy
  - tests/fixtures/aegis/pr276-executor-self-unstable.json
  - tests/fixtures/aegis/pr278-workflow-run-executor.json
  - docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/task-verification.md
  - docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/pr278-executor-run-evidence.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 250 Stabilize Evidence-Gated Autonomous Delivery Executor

## Header
- **Session ID (S)**: 2026-07-14-001
- **Work Context (W)**: task250-autonomous-delivery-executor-stability
- **Handler Target (H)**: .github/workflows/aegis-autonomous-delivery.yml
- **Task IDs**: 250
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/, docs/ai/work-tracking/archive/20260713-task249-codex-hook-update-migration-COMPLETED/, .serena/memories/2026-07-14_task250_autonomous_delivery_executor_stability.md, .github/workflows/aegis-autonomous-delivery.yml, scripts/aegis-delivery-policy, tests/fixtures/aegis/pr276-executor-self-unstable.json, tests/fixtures/aegis/pr278-workflow-run-executor.json, docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/task-verification.md, docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/pr278-executor-run-evidence.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reproduce PR #276 and define a fail-closed executor self-status contract | docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/designs/executor-self-status-contract.md | completed |
| plan-step-implement | Add executor-phase exact-head check/status evidence and a second final trusted evaluation | scripts/aegis-delivery-policy; .github/workflows/aegis-autonomous-delivery.yml; tests/fixtures/aegis/pr276-executor-self-unstable.json | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/TRACKER.md | in-progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/`
- `docs/ai/work-tracking/archive/20260713-task249-codex-hook-update-migration-COMPLETED/`
- `.serena/memories/2026-07-14_task249_codex_hook_update_migration_closeout.md`
- `.serena/memories/2026-07-14_task250_autonomous_delivery_executor_stability.md`
- `.github/workflows/aegis-autonomous-delivery.yml`
- `scripts/aegis-delivery-policy`
- `aegis_foundation/assets/scripts/aegis-delivery-policy`
- `tests/meta_workflow_guard/test_aegis_delivery_policy.py`
- `tests/meta_workflow_guard/test_aegis_autonomous_delivery_workflow.py`
- `tests/fixtures/aegis/pr276-executor-self-unstable.json`
- `tests/fixtures/aegis/pr278-workflow-run-executor.json`
- `docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/task-verification.md`
- `docs/ai/work-tracking/active/20260714-task250-autonomous-delivery-executor-stability-ACTIVE/reports/autonomous-delivery-executor-stability/pr278-executor-run-evidence.md`
- `.taskmaster/tasks/task_250.md`
- `.taskmaster/tasks/task_249.md`
- `.taskmaster/tasks/tasks.json`
- Taskmaster Task `250`

## Branch Policy
- Working branch: `feat/task-250-autonomous-delivery-stability`

## Amendments & Versioning
- 2026-07-14 - Task 250 kickoff created via the guided wizard flow.
- 2026-07-14 - Live canary PR #278 showed that `workflow_run` executor jobs are anchored to trusted `main` and cannot appear in candidate-head checks. The verification step now includes a separate trusted Actions run/job evidence model and a second hosted canary attempt before closeout.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 250 and its subtasks.
  3. Review the executor self-status contract before changing delivery policy.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: hosted acceptance must prove the Checks API permission, live executor self-binding, ordinary canary merge, and exact-merge-SHA dispatch before PR #276 is retried.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Executor self-status contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Direct-telemetry PR #276 replay and adversarial regressions
- Direct-telemetry PR #278 `workflow_run` replay and trusted run/job regressions
- Stored local, hosted, canary, and post-merge verification evidence

## Emergency Bypass Protocol
- No bypass authorized.
