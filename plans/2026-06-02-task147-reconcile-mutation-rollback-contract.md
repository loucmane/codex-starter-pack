---
session_id: 2026-06-02-007
work_context: task147-reconcile-mutation-rollback-contract
handler_target: docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/
task_ids: [147]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/
  - docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/
  - .taskmaster/tasks/task_147.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 147 Define Reconcile Mutation Rollback and Blast-Radius Proposal Contract

## Header
- **Session ID (S)**: 2026-06-02-007
- **Work Context (W)**: task147-reconcile-mutation-rollback-contract
- **Handler Target (H)**: docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/
- **Task IDs**: 147
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/, docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/, .taskmaster/tasks/task_147.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the report-only rollback/blast-radius proposal boundary for future reconcile mutation | docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Add test-only contract helper, rollback tests, and reconcile contract documentation | tests/meta_workflow_guard/reconcile_mutation_rollback_contract.py; docs/aegis/reconcile-mutation-rollback-contract.md | completed |
| plan-step-verify | Store verification evidence and confirm reconcile implementation surfaces remain unchanged | docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/verification-summary.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/`
- `docs/ai/work-tracking/active/20260602-task147-reconcile-mutation-rollback-contract-ACTIVE/reports/reconcile-mutation-rollback-contract/`
- `.taskmaster/tasks/task_147.txt`
- `tests/meta_workflow_guard/`
- `docs/aegis/`
- `tests/`
- Taskmaster Task `147`

## Branch Policy
- Working branch: `feat/task-147-reconcile-mutation-rollback-contract`

## Amendments & Versioning
- 2026-06-02 - Task 147 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 147 and its subtasks.
  3. Review `docs/aegis/reconcile-mutation-rollback-contract.md`.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep Task 147 report/contract-only; do not add reconcile mutation flags or behavior changes.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: reconcile implementation, CLI, MCP, and parser surfaces must remain report-only.

## Evidence Checklist
- Rollback contract docs under `docs/aegis/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
