---
session_id: 2026-06-02-009
work_context: task149-reconcile-apply-path-proposal-contract
handler_target: docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/
task_ids: [149]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/
  - docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/
  - .taskmaster/tasks/task_149.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 149 Define reconcile apply-path proposal contract

## Header
- **Session ID (S)**: 2026-06-02-009
- **Work Context (W)**: task149-reconcile-apply-path-proposal-contract
- **Handler Target (H)**: docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/
- **Task IDs**: 149
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/, docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/, .taskmaster/tasks/task_149.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the missing invocation/confirmation model for future reconcile apply | docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Add contract docs and guard tests without enabling mutation | docs/aegis/reconcile-apply-path-proposal-contract.md; tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/verification-summary.md; docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/`
- `docs/ai/work-tracking/active/20260602-task149-reconcile-apply-path-proposal-contract-ACTIVE/reports/reconcile-apply-path-proposal-contract/`
- `.taskmaster/tasks/task_149.md`
- `docs/aegis/reconcile-apply-path-proposal-contract.md`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`
- `tests/`
- Taskmaster Task `149`

## Branch Policy
- Working branch: `feat/task-149-reconcile-apply-path-proposal-contract`

## Amendments & Versioning
- 2026-06-02 - Task 149 kickoff created via the guided workflow setup.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 149 and its subtasks.
  3. Review the apply-path proposal contract and Claude discussion prompt.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: discuss Task 149 with Claude before creating Task 150.

## Conflict & Scope Declaration
- Related plans: Tasks 144-148 reconcile promotion, side-effect, precision,
  rollback, and inert preview contracts.
- Guard cross-check: Task 149 must not enable mutation or expose apply through
  governed-agent surfaces.

## Evidence Checklist
- Apply-path proposal contract under `docs/aegis/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence under the active report directory

## Emergency Bypass Protocol
- No bypass authorized.
