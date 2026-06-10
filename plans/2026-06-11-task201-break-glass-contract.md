---
session_id: 2026-06-11-003
work_context: task201-break-glass-contract
handler_target: .taskmaster/tasks/task_201.md
task_ids: [201]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/
  - .taskmaster/tasks/task_201.md
  - .taskmaster/tasks/task_201.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 201 Aegis break-glass recovery contract

## Header
- **Session ID (S)**: 2026-06-11-003
- **Work Context (W)**: task201-break-glass-contract
- **Handler Target (H)**: .taskmaster/tasks/task_201.md
- **Task IDs**: 201
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/, .taskmaster/tasks/task_201.md, .taskmaster/tasks/task_201.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the break-glass design: recovery contract mapping, one-shot rate-limited override token, tier-c never eligible, replay proofs | docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/designs/break-glass-scope.md | completed |
| plan-step-implement | Implement RECOVERY_CONTRACT + override token consume in gate_lib, aegis override CLI, sanction while BLOCKED, ledger audit | .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | 10 break-glass tests + replay corpus entries + full suite; recovery contract doc | docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260611-task201-break-glass-contract-ACTIVE/`
- `.taskmaster/tasks/task_201.md`
- `.taskmaster/tasks/task_201.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `201`

## Branch Policy
- Working branch: `feat/task-201-break-glass-contract`

## Amendments & Versioning
- 2026-06-11 - Task 201 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 201 and its subtasks.
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
