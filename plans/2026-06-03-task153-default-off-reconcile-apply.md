---
session_id: 2026-06-03-002
work_context: task153-default-off-reconcile-apply
handler_target: aegis_foundation/reconcile_apply_runtime.py
task_ids: [153]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/
  - aegis_foundation/reconcile_apply_runtime.py
  - .taskmaster/tasks/task_153.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 153 Add default-off reconcile apply write apparatus

## Header
- **Session ID (S)**: 2026-06-03-002
- **Work Context (W)**: task153-default-off-reconcile-apply
- **Handler Target (H)**: aegis_foundation/reconcile_apply_runtime.py
- **Task IDs**: 153
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/, aegis_foundation/reconcile_apply_runtime.py, .taskmaster/tasks/task_153.md, tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Confirm Task 153 boundary: default-off internal write apparatus only, no live enablement or agent-facing route | docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Implement scaffold evaluator extension, internal apply runtime, snapshot rollback, terminal rollback failure handling, audit records, and idempotency | aegis_foundation/reconcile_apply_scaffold.py; aegis_foundation/reconcile_apply_runtime.py; tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py; docs/aegis/ | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster/guard status | docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/reports/default-off-reconcile-apply/verification-summary.md; docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260603-task153-default-off-reconcile-apply-ACTIVE/`
- `aegis_foundation/reconcile_apply_runtime.py`
- `aegis_foundation/reconcile_apply_scaffold.py`
- `.taskmaster/tasks/task_153.md`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py`
- `docs/aegis/reconcile-promotion-contract.md`
- `docs/aegis/reconcile-disabled-apply-scaffold-contract.md`
- `docs/aegis/reconcile-shadow-apply-contract.md`
- `tests/`
- Taskmaster Task `153`

## Branch Policy
- Working branch: `feat/task-153-default-off-reconcile-apply`

## Amendments & Versioning
- 2026-06-03 - Task 153 kickoff created via the guided wizard flow.
- 2026-06-03 - Plan corrected from generic wizard template wording to the actual reconcile apply write-apparatus scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 153 and its subtasks.
  3. Review `aegis_foundation/reconcile_apply_runtime.py` and the Task 153 tests before changing apply behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep apply default-off and unreachable from agent-facing surfaces; future enablement remains a separate task.
- Verification complete: focused Task 153 tests, adjacent reconcile safety matrix, Taskmaster health, work-tracking audit, S:W:H:E guard, and whitespace check passed.

## Conflict & Scope Declaration
- Related plans: Tasks 144-152 reconcile promotion, side-effect oracle, precision corpus, rollback contract, inert preview, disabled scaffold, shadow apply, and CI cascade validation.
- Guard cross-check: Task 153 must not add `--apply`, MCP apply, codex-task apply, preview/report execution, or production/default enablement.

## Evidence Checklist
- Tracker/session entries for kickoff and implementation progress
- Stored focused and adjacent reconcile pytest evidence
- Contract documentation updated to reflect Task 153's default-off write-apparatus boundary

## Emergency Bypass Protocol
- No bypass authorized.
