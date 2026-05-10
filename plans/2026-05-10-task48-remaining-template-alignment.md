---
session_id: 2026-05-10-005
work_context: task48-remaining-template-alignment
handler_target: templates/handlers/index.md
task_ids: [48]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/
  - templates/handlers/index.md
  - .taskmaster/tasks/task_048.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 48 Remaining Template and Backlog Alignment

## Header
- **Session ID (S)**: 2026-05-10-005
- **Work Context (W)**: task48-remaining-template-alignment
- **Handler Target (H)**: templates/handlers/index.md
- **Task IDs**: 48
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/, templates/handlers/index.md, .taskmaster/tasks/task_048.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile Task 48 against the current portable foundation, remaining backlog, portability options, and agent adapter contract surface | docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/task48-scope-reconciliation.md; docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/remaining-backlog-alignment-audit.md; docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/foundation-portability-options.md; docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/agent-runtime-contract-map.md | completed |
| plan-step-implement | Apply only the proven current-state gap from scope reconciliation, or update Taskmaster to route follow-up implementation into the correct task | docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/IMPLEMENTATION.md; .taskmaster/tasks/task_048.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, run Taskmaster health/work-tracking audit/guard, and confirm Task 48 status | docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/`
- `templates/handlers/index.md`
- `templates/engine/core/portable-foundation-spec.md`
- `templates/engine/validation/foundation-adoption-guide.md`
- `.claude/engine/runtime-contract.md`
- `.taskmaster/tasks/task_048.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `48`

## Branch Policy
- Working branch: `feat/task-48-remaining-template-alignment`

## Amendments & Versioning
- 2026-05-10 - Task 48 kickoff created via the guided wizard flow.
- 2026-05-10 - Corrected the generic kickoff plan to Task 48's actual alignment scope and completed the scope gate.
- 2026-05-10 - Completed Task 48 as an alignment checkpoint; no broad template migration was selected because the audit routed follow-up work to Task 46 and Task 62.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 48 and its subtasks.
  3. Review the Task 48 scope reconciliation and backlog audit before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: parent Taskmaster descriptions for Task 46 and Task 62 still need reliable official update support before their old wording can be rewritten.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Task 48 scope reconciliation under `designs/`
- Remaining backlog alignment audit under `designs/`
- Foundation portability options decision under `designs/`
- Agent runtime contract mapping under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
