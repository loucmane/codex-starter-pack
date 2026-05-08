---
session_id: 2026-05-08-006
work_context: task31-compaction-protocol
handler_target: .taskmaster/tasks/task_031.txt
task_ids: [31]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/
  - scripts/codex-task
  - tests/meta_workflow_guard/test_codex_task.py
  - templates/workflows/session/compaction.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 31 Implement Compaction Protocol

## Header
- **Session ID (S)**: 2026-05-08-006
- **Work Context (W)**: task31-compaction-protocol
- **Handler Target (H)**: .taskmaster/tasks/task_031.txt
- **Task IDs**: 31
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/, scripts/codex-task, tests/meta_workflow_guard/test_codex_task.py, templates/workflows/session/compaction.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile the historical CompactionManager request against current rollback, session continuation, and Serena-memory systems | docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/designs/compaction-protocol-scope-reconciliation.md | completed |
| plan-step-implement | Implement the compaction continuation checkpoint helper, regression tests, and compaction protocol documentation | scripts/codex-task; tests/meta_workflow_guard/test_codex_task.py; templates/workflows/session/compaction.md; templates/behaviors/session/compaction-preparation.md; templates/handlers/triggers/session/prepare-compaction.md; templates/TOOLS.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/reports/compaction-protocol/tests-2026-05-08-codex-task.txt; docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/reports/compaction-protocol/guard-2026-05-08.txt; docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/reports/compaction-protocol/work-tracking-audit-2026-05-08.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task31-compaction-protocol-ACTIVE/`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/workflows/session/compaction.md`
- `templates/behaviors/session/compaction-preparation.md`
- `templates/handlers/triggers/session/prepare-compaction.md`
- `templates/TOOLS.md`
- Taskmaster Task `31`

## Branch Policy
- Working branch: `feat/task-31-compaction-protocol`

## Amendments & Versioning
- 2026-05-08 - Task 31 kickoff created via the guided wizard flow.
- 2026-05-08 - Scope corrected from a new `CompactionManager` to a compaction-specific continuation checkpoint helper that complements existing rollback and session systems.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 31 and its subtasks.
  3. Review the scope reconciliation artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: verify the helper writes durable checkpoint state while leaving the active session, active plan, and ACTIVE work-tracking folder intact.

## Conflict & Scope Declaration
- Related plans: Task 19 rollback checkpoints, Task 42 session continuation, Task 93 compaction/session-end split, Task 15 Serena evidence enforcement.
- Guard cross-check: compaction checkpointing must preserve plan/tracker/session compliance and must not behave like session end.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff, scope, implementation, and verification progress
- Focused pytest evidence for `tests/meta_workflow_guard/test_codex_task.py`
- Generated compaction manifest, resume message, Serena memory file, and compaction history entry
- Final plan sync, work-tracking audit, guard, and diff-check evidence

## Emergency Bypass Protocol
- No bypass authorized.
