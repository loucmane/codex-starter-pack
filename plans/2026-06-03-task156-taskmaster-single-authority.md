---
session_id: 2026-06-03-005
work_context: task156-taskmaster-single-authority
handler_target: scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py
task_ids: [156]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/
  - scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py
  - .taskmaster/tasks/task_156.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 156 Make Taskmaster the single task authority for Aegis surfaces

## Header
- **Session ID (S)**: 2026-06-03-005
- **Work Context (W)**: task156-taskmaster-single-authority
- **Handler Target (H)**: scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py
- **Task IDs**: 156
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/, scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py, .taskmaster/tasks/task_156.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define Taskmaster-present valid/invalid authority boundaries and local fallback non-goals | docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/designs/taskmaster-single-authority-scope.md | completed |
| plan-step-implement | Implement Taskmaster state classification and suppress Aegis task-selection heuristics for Taskmaster-present projects | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; tests/meta_workflow_guard/test_aegis_installer.py | completed |
| plan-step-verify | Store focused pytest/lint evidence and confirm prior reconcile/apply safety suites still pass | docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/reports/taskmaster-single-authority/verification-summary.md; docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260603-task156-taskmaster-single-authority-ACTIVE/`
- `scripts/_aegis_installer.py tests/meta_workflow_guard/test_aegis_installer.py`
- `.taskmaster/tasks/task_156.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `156`

## Branch Policy
- Working branch: `feat/task-156-taskmaster-single-authority`

## Amendments & Versioning
- 2026-06-03 - Task 156 kickoff created via the guided wizard flow.
- 2026-06-03 - Replaced generic wizard plan language with Taskmaster single-authority scope, implementation, and verification evidence.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 156 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
