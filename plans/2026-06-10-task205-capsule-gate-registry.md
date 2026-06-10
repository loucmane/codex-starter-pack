---
session_id: 2026-06-10-005
work_context: task205-capsule-gate-registry
handler_target: .taskmaster/tasks/task_205.md
task_ids: [205]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/
  - .taskmaster/tasks/task_205.md
  - .taskmaster/tasks/task_205.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 205 Capsule PR-1d: gate registry and verification classification

## Header
- **Session ID (S)**: 2026-06-10-005
- **Work Context (W)**: task205-capsule-gate-registry
- **Handler Target (H)**: .taskmaster/tasks/task_205.md
- **Task IDs**: 205
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/, .taskmaster/tasks/task_205.md, .taskmaster/tasks/task_205.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-1d boundary: seed-once brief.json config asset (new kind config), command normalization rules, verification classification, scope-record inference + once-only nudge | docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/designs/gate-registry-scope.md | completed |
| plan-step-implement | Implement brief.json asset + schema kind, gate matching in gate_lib record path, scope records, aegis scope set, sync-hook nudge; mirror both copies | .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Fixture suite incl. cd-prefix/-C/--dir variants, seed-once upgrade test, scope inference/nudge tests, full suite + guard stack; evidence under reports/capsule-gate-registry/ | docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task205-capsule-gate-registry-ACTIVE/`
- `.taskmaster/tasks/task_205.md`
- `.taskmaster/tasks/task_205.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `205`

## Branch Policy
- Working branch: `feat/task-205-capsule-gate-registry`

## Amendments & Versioning
- 2026-06-10 - Task 205 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 205 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md sections 2/2.1 and designs/gate-registry-scope.md.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: brief.json must never be clobbered on upgrade (seed-once); the sync-hook nudge must be failure-proof; pattern values stay per-repo config.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
