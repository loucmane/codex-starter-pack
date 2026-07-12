---
session_id: 2026-07-13-002
work_context: task239-worktree-subagent-capture-audit
handler_target: aegis_foundation/worktree_capture_audit.py
task_ids: [239]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/
  - aegis_foundation/worktree_capture_audit.py
  - .taskmaster/tasks/task_239.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 239 Audit Aegis Capture Across Worktrees And Subagents

## Header
- **Session ID (S)**: 2026-07-13-002
- **Work Context (W)**: task239-worktree-subagent-capture-audit
- **Handler Target (H)**: aegis_foundation/worktree_capture_audit.py
- **Task IDs**: 239
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/, aegis_foundation/worktree_capture_audit.py, .taskmaster/tasks/task_239.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the diagnostic-only cause taxonomy, secret-free evidence schema, live/fixture matrix, classification rules, and rollback boundary | docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/designs/worktree-capture-audit-contract.md | completed |
| plan-step-implement | Implement deterministic collection/classification/replay and run disposable worktree/client scenarios without changing recorder behavior | aegis_foundation/worktree_capture_audit.py; docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/`
- `aegis_foundation/worktree_capture_audit.py`
- `.taskmaster/tasks/task_239.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `239`

## Branch Policy
- Working branch: `feat/task-239-worktree-subagent-capture-audit`

## Amendments & Versioning
- 2026-07-13 - Task 239 kickoff created via the guided wizard flow.
- 2026-07-13 - Replaced generic wizard wording with the binding C3 diagnostic-only contract; Task 240 remains the sole runtime-fix authority.
- 2026-07-13 - Completed deterministic and live audit implementation. The Git-common-dir store and teardown behavior are supported; Claude attribution is degraded and Codex child capture is unsupported.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 239 and its subtasks.
  3. Review the worktree-capture audit contract before changing the harness.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: publish the exact Task 239 scope, collect hosted checks, then complete Taskmaster/archive lifecycle without selecting or implementing the Task 240 correction.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Worktree/subagent capture audit contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Secret-free replay fixture, live coverage report, tests, guard evidence, and before/after non-mutation proof

## Emergency Bypass Protocol
- No bypass authorized.
