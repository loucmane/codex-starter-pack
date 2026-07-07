---
session_id: 2026-07-07-002
work_context: task231-aegis-update-command
handler_target: aegis_foundation/cli.py
task_ids: [231]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/
  - aegis_foundation/cli.py
  - .taskmaster/tasks/task_231.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 231 Unified Aegis project update command

## Header
- **Session ID (S)**: 2026-07-07-002
- **Work Context (W)**: task231-aegis-update-command
- **Handler Target (H)**: aegis_foundation/cli.py
- **Task IDs**: 231
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/, aegis_foundation/cli.py, .taskmaster/tasks/task_231.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the one-repo update command contract and the out-of-scope fleet/MCP/rollback work | docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/designs/project-update-command.md | completed |
| plan-step-implement | Implement the shared installer primitive, CLI/wrapper command wiring, tests, and documentation | scripts/_aegis_installer.py; aegis_foundation/cli.py; scripts/codex-task; tests/meta_workflow_guard/test_aegis_installer.py; docs/aegis/update-rollback.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260707-task231-aegis-update-command-ACTIVE/`
- `aegis_foundation/cli.py`
- `.taskmaster/tasks/task_231.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `231`

## Branch Policy
- Working branch: `feat/task-231-aegis-update-command`

## Amendments & Versioning
- 2026-07-07 - Task 231 kickoff created through the guided task flow.
- 2026-07-07 - Replaced generated wizard wording with the actual composed update-command scope.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 231 and its subtasks.
  3. Review the project update command design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep `aegis update` grounded in existing installer primitives rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: update flow must preserve installer-managed file safety and report strict verification failures without hiding them.

## Evidence Checklist
- Project update command design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
