---
session_id: 2026-07-06-001
work_context: task217-closeout-convergence-populate
handler_target: .taskmaster/tasks/task_217.txt
task_ids: [217]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260706-task217-closeout-convergence-populate-ACTIVE/
  - .taskmaster/tasks/task_217.txt
  - .taskmaster/tasks/task_217.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 217 One-shot closeout convergence for non-canonical usage

## Header
- **Session ID (S)**: 2026-07-06-001
- **Work Context (W)**: task217-closeout-convergence-populate
- **Handler Target (H)**: .taskmaster/tasks/task_217.txt
- **Task IDs**: 217
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260706-task217-closeout-convergence-populate-ACTIVE/, .taskmaster/tasks/task_217.txt, .taskmaster/tasks/task_217.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for One-shot closeout convergence for non-canonical usage | docs/ai/work-tracking/active/20260706-task217-closeout-convergence-populate-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the closeout populate helper, surgical handoff repair, and packaged installer mirror for One-shot closeout convergence for non-canonical usage | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; tests/meta_workflow_guard/test_aegis_installer.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | tests/meta_workflow_guard/test_aegis_installer.py; tests/meta_workflow_guard/test_assets_scripts_parity.py; tests/meta_workflow_guard/test_aegis_mcp_server.py | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260706-task217-closeout-convergence-populate-ACTIVE/`
- `.taskmaster/tasks/task_217.txt`
- `.taskmaster/tasks/task_217.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `217`

## Branch Policy
- Working branch: `feat/task-217-closeout-convergence-populate`

## Amendments & Versioning
- 2026-07-06 - Task 217 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 217 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence for the closeout populate implementation

## Emergency Bypass Protocol
- No bypass authorized.
