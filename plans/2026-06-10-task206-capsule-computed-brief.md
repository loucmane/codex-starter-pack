---
session_id: 2026-06-10-006
work_context: task206-capsule-computed-brief
handler_target: .taskmaster/tasks/task_206.md
task_ids: [206]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/
  - .taskmaster/tasks/task_206.md
  - .taskmaster/tasks/task_206.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 206 Capsule PR-2a: computed aegis brief

## Header
- **Session ID (S)**: 2026-06-10-006
- **Work Context (W)**: task206-capsule-computed-brief
- **Handler Target (H)**: .taskmaster/tasks/task_206.md
- **Task IDs**: 206
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/, .taskmaster/tasks/task_206.md, .taskmaster/tasks/task_206.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-2a boundary: brief_lib.py compiler, 8 computed fields with STALE semantics, 5-check sentinel + canary, risk-seed consumption, aegis brief + --check CLI | docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/designs/computed-brief-scope.md | completed |
| plan-step-implement | Implement brief_lib.py (compile, sentinel, canary, render, capsule files), aegis brief CLI + gate classification, mirrors | aegis_foundation/cli.py; docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Fixture-repo tests per field, sentinel/canary tests, --check budget tests, live brief-vs-reality check in this repo, full suite + guard stack | docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task206-capsule-computed-brief-ACTIVE/`
- `.taskmaster/tasks/task_206.md`
- `.taskmaster/tasks/task_206.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `206`

## Branch Policy
- Working branch: `feat/task-206-capsule-computed-brief`

## Amendments & Versioning
- 2026-06-10 - Task 206 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 206 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md sections 3-3.2 and designs/computed-brief-scope.md.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: compile must never fail at read time (STALE beats error); gh is second-class (timeout + cached last-success); canary can never be silently green.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
