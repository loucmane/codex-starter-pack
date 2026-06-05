---
session_id: 2026-06-05-002
work_context: task163-node24-actions-runtime
handler_target: .github/workflows/ci.yml
task_ids: [163]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/
  - .github/workflows/ci.yml
  - .github/workflows/codex-guard.yml
  - .github/workflows/meta-workflow-guard.yml
  - tests/meta_workflow_guard/test_ci_workflows.py
  - .taskmaster/tasks/task_163.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 163 Update GitHub Actions for Node 24 runner transition

## Header
- **Session ID (S)**: 2026-06-05-002
- **Work Context (W)**: task163-node24-actions-runtime
- **Handler Target (H)**: .github/workflows/ci.yml
- **Task IDs**: 163
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/, .github/workflows/ci.yml, .github/workflows/codex-guard.yml, .github/workflows/meta-workflow-guard.yml, tests/meta_workflow_guard/test_ci_workflows.py, .taskmaster/tasks/task_163.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the minimal Node 24 JavaScript-action runtime opt-in while preserving action versions, Taskmaster Node 22, and read-only Aegis evidence boundaries | docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Add the Node 24 runtime opt-in to GitHub Actions workflows and pin the contract with workflow tests without changing artifact-producing Python logic | .github/workflows/ci.yml; .github/workflows/codex-guard.yml; .github/workflows/meta-workflow-guard.yml; tests/meta_workflow_guard/test_ci_workflows.py; docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove workflow parsing and runtime contract locally, then verify real PR artifacts after CI runs | tests/meta_workflow_guard/test_ci_workflows.py; docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260605-task163-node24-actions-runtime-ACTIVE/`
- `.github/workflows/ci.yml`
- `.github/workflows/codex-guard.yml`
- `.github/workflows/meta-workflow-guard.yml`
- `tests/meta_workflow_guard/test_ci_workflows.py`
- `.taskmaster/tasks/task_163.md`
- Taskmaster Task `163`

## Branch Policy
- Working branch: `feat/task-163-node24-actions-runtime`

## Amendments & Versioning
- 2026-06-05 - Task 163 kickoff created via the guided wizard flow.
- 2026-06-05 - Scope narrowed to `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` runtime opt-in without action major-version bumps.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 163 and its subtasks.
  3. Review the Node 24 runtime opt-in and artifact upload contract before changing action versions.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: inspect the PR CI artifacts after the first Node 24 runtime run and confirm the `$RUNNER_TEMP/aegis-shadow/` artifact layout is unchanged.

## Conflict & Scope Declaration
- Related plans: Tasks 158, 161, 162, and 164 shadow evidence/toolchain validation.
- Guard cross-check: CI runtime maintenance must not alter Aegis apply, enablement, artifact-producing Python logic, candidate classes, or Taskmaster's Node 22 toolchain identity.

## Evidence Checklist
- Workflow runtime opt-in in CI and guard workflows
- Regression test pinning action versions and Taskmaster Node 22
- PR CI artifact inspection after the runtime opt-in runs on GitHub

## Emergency Bypass Protocol
- No bypass authorized.
