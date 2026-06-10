---
session_id: 2026-06-10-007
work_context: task207-capsule-injection
handler_target: .taskmaster/tasks/task_207.md
task_ids: [207]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/
  - .taskmaster/tasks/task_207.md
  - .taskmaster/tasks/task_207.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 207 Capsule PR-2b: SessionStart injection

## Header
- **Session ID (S)**: 2026-06-10-007
- **Work Context (W)**: task207-capsule-injection
- **Handler Target (H)**: .taskmaster/tasks/task_207.md
- **Task IDs**: 207
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/, .taskmaster/tasks/task_207.md, .taskmaster/tasks/task_207.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-2b boundary: render_injection degradation order + caps, sessionstart stamp+inject wiring, off-switch precedence, sync SessionStart entry | docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/designs/injection-scope.md | completed |
| plan-step-implement | Implement render_injection, gate_lib sessionstart inject path, session-brief.sh, renderer/settings/manifest wiring, mirrors | .claude/scripts/brief_lib.py; docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Stamp/inject/degradation/cap tests on real SessionStart fixtures, renderer tests, full suite + guard stack | docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task207-capsule-injection-ACTIVE/`
- `.taskmaster/tasks/task_207.md`
- `.taskmaster/tasks/task_207.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `207`

## Branch Policy
- Working branch: `feat/task-207-capsule-injection`

## Amendments & Versioning
- 2026-06-10 - Task 207 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 207 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md sections 3.3/3.4 and designs/injection-scope.md.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: SessionStart is synchronous — keep compile under ~2s and gh under its 800ms budget; injection must never fail (degrade, never error); off-switch must stamp the flag for the A/B falsifier.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
