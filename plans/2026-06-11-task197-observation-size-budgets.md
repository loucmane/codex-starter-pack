---
session_id: 2026-06-11-002
work_context: task197-observation-size-budgets
handler_target: .taskmaster/tasks/task_197.md
task_ids: [197]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/
  - .taskmaster/tasks/task_197.md
  - .taskmaster/tasks/task_197.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 197 Aegis observation report size budgets

## Header
- **Session ID (S)**: 2026-06-11-002
- **Work Context (W)**: task197-observation-size-budgets
- **Handler Target (H)**: .taskmaster/tasks/task_197.md
- **Task IDs**: 197
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/, .taskmaster/tasks/task_197.md, .taskmaster/tasks/task_197.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the size-budget design: baseline-ref + capped summaries + detail artifact, detection unchanged | docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/designs/size-budgets-scope.md | completed |
| plan-step-implement | Move baseline to ref file, summarize report fields, write detail artifact, allowed-prefix updates | scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Size-budget acceptance test (<100KB with 4000 blobs), observation suite, full suite | docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260611-task197-observation-size-budgets-ACTIVE/`
- `.taskmaster/tasks/task_197.md`
- `.taskmaster/tasks/task_197.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `197`

## Branch Policy
- Working branch: `feat/task-197-observation-size-budgets`

## Amendments & Versioning
- 2026-06-11 - Task 197 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 197 and its subtasks.
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
