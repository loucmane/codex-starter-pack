---
session_id: 2026-06-03-001
work_context: task152-ci-shadow-cascade-validation
handler_target: .github/workflows/ci.yml
task_ids: [152]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/
  - .github/workflows/ci.yml
  - aegis_foundation/taskmaster_toolchain.py
  - aegis_foundation/reconcile_shadow_apply.py
  - tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
  - tests/meta_workflow_guard/test_ci_workflows.py
  - .taskmaster/tasks/task_152.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 152 Add CI sacrificial cascade validation for reconcile shadow apply

## Header
- **Session ID (S)**: 2026-06-03-001
- **Work Context (W)**: task152-ci-shadow-cascade-validation
- **Handler Target (H)**: .github/workflows/ci.yml
- **Task IDs**: 152
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/, .github/workflows/ci.yml, aegis_foundation/taskmaster_toolchain.py, aegis_foundation/reconcile_shadow_apply.py, tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py, tests/meta_workflow_guard/test_ci_workflows.py, .taskmaster/tasks/task_152.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the CI toolchain binding and no-write validation boundary for Task 152 | docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Provision pinned Taskmaster in CI, emit bound shadow cascade artifacts, and cover both state.json baseline branches | .github/workflows/ci.yml; aegis_foundation/taskmaster_toolchain.py; aegis_foundation/reconcile_shadow_apply.py; docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused, no-Taskmaster, adjacent-suite, guard, and Taskmaster health evidence | docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/reports/ci-shadow-cascade-validation/verification-summary.md; docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260603-task152-ci-shadow-cascade-validation-ACTIVE/`
- `.github/workflows/ci.yml`
- `.taskmaster/tasks/task_152.md`
- `aegis_foundation/taskmaster_toolchain.py`
- `aegis_foundation/reconcile_shadow_apply.py`
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`
- `tests/meta_workflow_guard/test_ci_workflows.py`
- `tests/`
- Taskmaster Task `152`

## Branch Policy
- Working branch: `feat/task-152-ci-shadow-cascade-validation`

## Amendments & Versioning
- 2026-06-03 - Task 152 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 152 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: Task 153 must still validate the actual post-merge approved-context trigger and partial-apply rollback behavior before any live write path can be enabled.

## Conflict & Scope Declaration
- Related plans: Tasks 144-151 reconcile read-only, precision, rollback, preview, disabled scaffold, and shadow apply contracts.
- Guard cross-check: Task 152 must add CI evidence only; it must not introduce an apply flag, MCP apply tool, or governed-repo Taskmaster mutation.

## Evidence Checklist
- Tracker/session entries for kickoff and implementation progress
- CI workflow contract tests for pinned Taskmaster provisioning and cascade artifact capture
- Focused shadow apply tests covering both `state.json` baseline branches
- Stored verification summary for local focused, no-Taskmaster, adjacent-suite, guard, and Taskmaster health checks

## Emergency Bypass Protocol
- No bypass authorized.
