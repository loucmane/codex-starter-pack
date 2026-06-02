---
session_id: 2026-06-02-010
work_context: task150-disabled-reconcile-apply-scaffold
handler_target: docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/
task_ids: [150]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/
  - docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/
  - .taskmaster/tasks/task_150.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 150 Add disabled reconcile apply scaffold

## Header
- **Session ID (S)**: 2026-06-02-010
- **Work Context (W)**: task150-disabled-reconcile-apply-scaffold
- **Handler Target (H)**: docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/
- **Task IDs**: 150
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/, docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/, .taskmaster/tasks/task_150.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the disabled apply scaffold boundary: proof allowlist, kill switch, audit model, zero mutation, and no governed-agent surface | docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement the disabled scaffold module, contract doc, promotion-doc updates, and meta-workflow tests | aegis_foundation/reconcile_apply_scaffold.py; tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py; docs/aegis/reconcile-disabled-apply-scaffold-contract.md | completed |
| plan-step-verify | Store focused and adjacent test evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/verification-summary.md; docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/`
- `docs/ai/work-tracking/active/20260602-task150-disabled-reconcile-apply-scaffold-ACTIVE/reports/disabled-reconcile-apply-scaffold/`
- `.taskmaster/tasks/task_150.md`
- `aegis_foundation/reconcile_apply_scaffold.py`
- `docs/aegis/reconcile-disabled-apply-scaffold-contract.md`
- `docs/aegis/reconcile-apply-path-proposal-contract.md`
- `docs/aegis/reconcile-promotion-contract.md`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py`
- Taskmaster Task `150`

## Branch Policy
- Working branch: `feat/task-150-disabled-reconcile-apply-scaffold`

## Amendments & Versioning
- 2026-06-02 - Task 150 kickoff created via the guided workflow kickoff.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 150 and its subtasks.
  3. Review the disabled apply scaffold contract before changing reconcile apply behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the scaffold disabled and unreachable from governed-agent surfaces until a later task deliberately enables a bounded apply path.

## Conflict & Scope Declaration
- Related plans: Tasks 144-149 reconcile promotion contracts and safety prerequisites.
- Guard cross-check: the scaffold must not add `--apply`, MCP apply tools, Taskmaster writes, Git writes, workflow-state writes, or any governed-agent apply route.

## Evidence Checklist
- Disabled scaffold contract under `docs/aegis/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence for focused and adjacent reconcile checks

## Emergency Bypass Protocol
- No bypass authorized.
