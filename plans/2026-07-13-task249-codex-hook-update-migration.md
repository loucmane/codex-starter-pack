---
session_id: 2026-07-13-005
work_context: task249-codex-hook-update-migration
handler_target: scripts/_aegis_installer.py
task_ids: [249]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_249.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 249 Fix pre-adapter Codex manifest update migration

## Header
- **Session ID (S)**: 2026-07-13-005
- **Work Context (W)**: task249-codex-hook-update-migration
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 249
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_249.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the migration-order invariant and fail-closed boundaries for pre-adapter Codex manifests | docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/designs/update-migration-order.md | completed |
| plan-step-implement | Reorder project update apply, preserve manual-review refusal, and add Blog-shaped regression coverage | scripts/_aegis_installer.py; tests/meta_workflow_guard/test_codex_hook_adapter.py; docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/TRACKER.md | in-progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task249-codex-hook-update-migration-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_249.txt`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `249`

## Branch Policy
- Working branch: `feat/task-249-codex-hook-update-migration`

## Amendments & Versioning
- 2026-07-13 - Task 249 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 249 and its subtasks.
  3. Review the update-migration-order design artifact before changing installer behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: do not weaken direct runtime validation or allow a divergent operator-owned `.codex/hooks.json` to be overwritten.

## Conflict & Scope Declaration
- Related plans: Task 248 first-class Codex hook adapter and the deferred Blog rollout.
- Guard cross-check: update apply must remain plan-gated, fail closed on manual review, and produce a current-schema manifest before runtime metadata is advanced.

## Evidence Checklist
- Migration-order design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
