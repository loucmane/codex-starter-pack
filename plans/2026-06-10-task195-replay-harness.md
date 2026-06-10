---
session_id: 2026-06-10-009
work_context: task195-replay-harness
handler_target: .taskmaster/tasks/task_195.md
task_ids: [195]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/
  - .taskmaster/tasks/task_195.md
  - .taskmaster/tasks/task_195.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 195 Aegis vNext Phase 0 replay harness

## Header
- **Session ID (S)**: 2026-06-10-009
- **Work Context (W)**: task195-replay-harness
- **Handler Target (H)**: .taskmaster/tasks/task_195.md
- **Task IDs**: 195
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/, .taskmaster/tasks/task_195.md, .taskmaster/tasks/task_195.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the harness boundary: corpus schema + labels, state fixtures, E01/E29 goldens, ledger ingestion, replay CLI + CI suite | docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/designs/replay-harness-scope.md | completed |
| plan-step-implement | Implement aegis_foundation/replay.py, corpora, E01/E29 goldens, ledger ingestion, aegis replay CLI | aegis_foundation/cli.py; docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Corpus suites green with correct expectations (FP baseline, must-fire, adversarial incl. expected gaps), full suite + guard stack | docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task195-replay-harness-ACTIVE/`
- `.taskmaster/tasks/task_195.md`
- `.taskmaster/tasks/task_195.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `195`

## Branch Policy
- Working branch: `feat/task-195-replay-harness`

## Amendments & Versioning
- 2026-06-10 - Task 195 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 195 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: replay must run the REAL gate code, never a reimplementation; expectations must encode known FN gaps explicitly so the harness cannot lie by omission.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
