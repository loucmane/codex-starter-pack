---
session_id: 2026-05-14-008
work_context: task65-template-quality-scoring
handler_target: .taskmaster/tasks/task_065.txt
task_ids: [65]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/
  - .taskmaster/tasks/task_065.txt
  - .taskmaster/tasks/task_065.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 65 Build Template Quality Scoring

## Header
- **Session ID (S)**: 2026-05-14-008
- **Work Context (W)**: task65-template-quality-scoring
- **Handler Target (H)**: .taskmaster/tasks/task_065.txt
- **Task IDs**: 65
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/, .taskmaster/tasks/task_065.txt, .taskmaster/tasks/task_065.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Design the wizard flow, prompt contract, and workflow boundary for Build Template Quality Scoring | docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | Implement the wizard CLI, helper integration, and documentation for Build Template Quality Scoring | scripts/codex-task; docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260514-task65-template-quality-scoring-ACTIVE/`
- `.taskmaster/tasks/task_065.txt`
- `.taskmaster/tasks/task_065.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `65`

## Branch Policy
- Working branch: `feat/task-65-template-quality-scoring`

## Amendments & Versioning
- 2026-05-14 - Task 65 kickoff created via the guided wizard flow.
- 2026-05-14 - Scope reconciled to a deterministic non-destructive template quality scorecard; live dashboards, CI gate installation, trend backends, scheduler behavior, notifications, and template mutation are out of scope.
- 2026-05-14 - Implemented `python3 scripts/codex-task template quality-score`, report documentation, focused tests, and a sample task-local scorecard.
- 2026-05-14 - Marked Taskmaster Task 65 and subtasks done, generated the final strict quality scorecard, and prepared final verification evidence under the Task 65 work-tracking reports folder.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 65 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: after PR merge, archive `20260514-task65-template-quality-scoring-ACTIVE` and capture post-archive audit/guard evidence.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- [x] Wizard design note under `designs/`
- [x] Tracker/session entries for kickoff and scope progress
- [x] Stored implementation test evidence and sample scorecard output
- [x] Stored final plan-sync, audit, Taskmaster health, guard, and diff-check evidence

## Emergency Bypass Protocol
- No bypass authorized.
