---
session_id: 2026-06-02-011
work_context: task151-reconcile-shadow-apply-artifacts
handler_target: docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/
task_ids: [151]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/
  - docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/
  - .taskmaster/tasks/task_151.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 151 Add reconcile shadow apply artifacts

## Header
- **Session ID (S)**: 2026-06-02-011
- **Work Context (W)**: task151-reconcile-shadow-apply-artifacts
- **Handler Target (H)**: docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/
- **Task IDs**: 151
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/, docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/, .taskmaster/tasks/task_151.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define shadow-mode boundaries: CI artifact evidence, local declared report path, sacrificial-clone validation, and no live mutation | docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement shadow report builders, sacrificial clone validation, CI context proof artifact capture, contract docs, and tests | aegis_foundation/reconcile_shadow_apply.py; tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py; docs/aegis/reconcile-shadow-apply-contract.md | completed |
| plan-step-verify | Store focused and adjacent test evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/verification-summary.md; docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/`
- `docs/ai/work-tracking/active/20260602-task151-reconcile-shadow-apply-artifacts-ACTIVE/reports/reconcile-shadow-apply-artifacts/`
- `.taskmaster/tasks/task_151.md`
- `aegis_foundation/reconcile_shadow_apply.py`
- `.github/workflows/ci.yml`
- `docs/aegis/reconcile-shadow-apply-contract.md`
- `docs/aegis/reconcile-promotion-contract.md`
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`
- Taskmaster Task `151`

## Branch Policy
- Working branch: `feat/task-151-reconcile-shadow-apply-artifacts`

## Amendments & Versioning
- 2026-06-02 - Task 151 kickoff created via the guided workflow kickoff.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 151 and its subtasks.
  3. Review `docs/aegis/reconcile-shadow-apply-contract.md` before changing shadow behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep shadow mode artifact-only; Task 152 is the first possible task that may introduce live write code and must re-prove default-off inertness.

## Conflict & Scope Declaration
- Related plans: Tasks 144-150 reconcile promotion and disabled scaffold contracts.
- Guard cross-check: shadow mode must not add `--apply`, MCP apply tools, executable command strings, live Taskmaster mutation, Git writes, or workflow-state writes.

## Evidence Checklist
- Shadow contract under `docs/aegis/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence for focused and adjacent reconcile checks

## Emergency Bypass Protocol
- No bypass authorized.
