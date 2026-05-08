---
session_id: 2026-05-08-007
work_context: task20-ci-cd-pipeline
handler_target: .taskmaster/tasks/task_020.txt
task_ids: [20]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/
  - .github/workflows/ci.yml
  - tests/meta_workflow_guard/test_ci_workflows.py
  - .taskmaster/tasks/task_020.txt
plan_version: v1
emergency_bypass: false
---

# Plan - Task 20 Setup CI/CD Pipeline

## Header
- **Session ID (S)**: 2026-05-08-007
- **Work Context (W)**: task20-ci-cd-pipeline
- **Handler Target (H)**: .taskmaster/tasks/task_020.txt
- **Task IDs**: 20
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/, .github/workflows/ci.yml, tests/meta_workflow_guard/test_ci_workflows.py, .taskmaster/tasks/task_020.txt
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical CI/CD wording against current GitHub Actions, guard, drift, hooks, metrics, Taskmaster, and portable foundation systems | docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/designs/ci-cd-scope-reconciliation.md | completed |
| plan-step-implement | Add the missing Python test-suite CI matrix and regression coverage for the workflow contract | .github/workflows/ci.yml; tests/meta_workflow_guard/test_ci_workflows.py; docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/`
- `.taskmaster/tasks/task_020.txt`
- `.github/workflows/ci.yml`
- `tests/meta_workflow_guard/test_ci_workflows.py`
- Taskmaster Task `20`

## Branch Policy
- Working branch: `feat/task-20-ci-cd-pipeline`

## Amendments & Versioning
- 2026-05-08 - Task 20 kickoff created via the guided wizard flow.
- 2026-05-08 - Scope corrected from a broad greenfield CI/CD pipeline to the proven current gap: Python test-suite CI matrix coverage.
- 2026-05-08 - Implemented `.github/workflows/ci.yml` and workflow contract tests.
- 2026-05-08 - Final verification passed and Taskmaster Task 20 was marked done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 20 and its subtasks.
  3. Review the CI/CD scope reconciliation artifact before changing workflow behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: confirm the GitHub PR checks run the new Python matrix after this branch is pushed.

## Conflict & Scope Declaration
- Related plans: Task 9 hook parity, Task 15 Serena enforcement, Task 84 timestamp guard, Task 97 metrics dashboard.
- Guard cross-check: keep existing guard/drift/metrics workflows intact and add only the missing full-test CI path.

## Evidence Checklist
- CI/CD scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored workflow-contract test, full pytest, Taskmaster health, guard, audit, plan-sync, and diff-check evidence

## Emergency Bypass Protocol
- No bypass authorized.
