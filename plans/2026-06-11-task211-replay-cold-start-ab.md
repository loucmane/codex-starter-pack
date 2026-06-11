---
session_id: 2026-06-11-004
work_context: task211-replay-cold-start-ab
handler_target: .taskmaster/tasks/task_211.txt
task_ids: [211]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/
  - .taskmaster/tasks/task_211.txt
  - .taskmaster/tasks/task_211.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 211 Capsule falsifier: replay-cold-start A/B harness

## Header
- **Session ID (S)**: 2026-06-11-004
- **Work Context (W)**: task211-replay-cold-start-ab
- **Handler Target (H)**: .taskmaster/tasks/task_211.txt
- **Task IDs**: 211
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/, .taskmaster/tasks/task_211.txt, .taskmaster/tasks/task_211.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the authentic-falsifier design: replay real cold-starts, capsule on/off worktrees, transcript cost metric, fresh-null guard, operator/CI split | docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/designs/coldstart-ab-scope.md | completed |
| plan-step-implement | Implement replay_coldstart.py (parser, worktree, aggregate+CI, decide, operator-gated run_live_ab) + fixtures | aegis_foundation/replay_coldstart.py; docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | 11 core tests (parser/meaningful-action/worktree/CI/decide/fresh-null/operator-gate) + full suite | docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260611-task211-replay-cold-start-ab-ACTIVE/`
- `.taskmaster/tasks/task_211.txt`
- `.taskmaster/tasks/task_211.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `211`

## Branch Policy
- Working branch: `feat/task-211-replay-cold-start-ab`

## Amendments & Versioning
- 2026-06-11 - Task 211 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 211 and its subtasks.
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
