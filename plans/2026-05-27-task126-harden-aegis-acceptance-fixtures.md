---
session_id: 2026-05-27-002
work_context: task126-harden-aegis-acceptance-fixtures
handler_target: tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
task_ids: [126]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260527-task126-harden-aegis-acceptance-fixtures-ACTIVE/
  - tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
  - .taskmaster/tasks/task_126.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 126 Harden Aegis Acceptance Fixture Verification

## Header
- **Session ID (S)**: 2026-05-27-002
- **Work Context (W)**: task126-harden-aegis-acceptance-fixtures
- **Handler Target (H)**: tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
- **Task IDs**: 126
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260527-task126-harden-aegis-acceptance-fixtures-ACTIVE/, tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py, .taskmaster/tasks/task_126.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the acceptance fixture policy and identify brittle web workflow assertions | docs/ai/work-tracking/active/20260527-task126-harden-aegis-acceptance-fixtures-ACTIVE/designs/acceptance-fixture-policy.md | completed |
| plan-step-implement | Add semantic assertion helpers, refactor brittle web assertions, and update acceptance docs | tests/meta_workflow_guard/aegis_acceptance_assertions.py; tests/meta_workflow_guard/test_aegis_acceptance_assertions.py; tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py; docs/aegis/live-acceptance-matrix.md | completed |
| plan-step-verify | Run semantic helper, web workflow, Aegis fixture, Taskmaster, plan, work-tracking, guard, and diff checks | docs/ai/work-tracking/active/20260527-task126-harden-aegis-acceptance-fixtures-ACTIVE/reports/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260527-task126-harden-aegis-acceptance-fixtures-ACTIVE/`
- `tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`
- `.taskmaster/tasks/task_126.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `126`

## Branch Policy
- Working branch: `feat/task-126-harden-aegis-acceptance-fixtures`

## Amendments & Versioning
- 2026-05-27 - Task 126 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 126 and its subtasks.
  3. Review the acceptance fixture policy before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep semantic fixture checks focused on acceptance evidence rather than redesigning Aegis runtime behavior.

## Conflict & Scope Declaration
- Related plans: Task 125 public adoption flow and Task 122 workflow guidance portability.
- Guard cross-check: acceptance fixture changes must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Acceptance fixture policy note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
