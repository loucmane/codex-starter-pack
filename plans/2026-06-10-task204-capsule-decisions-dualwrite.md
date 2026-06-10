---
session_id: 2026-06-10-004
work_context: task204-capsule-decisions-dualwrite
handler_target: .taskmaster/tasks/task_204.md
task_ids: [204]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/
  - .taskmaster/tasks/task_204.md
  - .taskmaster/tasks/task_204.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 204 Capsule PR-1c: gate-decisions dual-write

## Header
- **Session ID (S)**: 2026-06-10-004
- **Work Context (W)**: task204-capsule-decisions-dualwrite
- **Handler Target (H)**: .taskmaster/tasks/task_204.md
- **Task IDs**: 204
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/, .taskmaster/tasks/task_204.md, .taskmaster/tasks/task_204.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-1c boundary from AEGIS_CAPSULE_SPEC.md section 2: dual-write mechanics, session attribution via Payload, parity key, and the explicit not-in-this-PR list (no JSONL freeze, no history migration) | docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/designs/decisions-dualwrite-scope.md | completed |
| plan-step-implement | Extend Payload with session_id/cwd, dual-write append_gate_decision to the ledger as gate_decision events (best-effort), mirror both gate_lib copies | .claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/IMPLEMENTATION.md | pending |
| plan-step-verify | Fixture-driven parity tests (JSONL twin in ledger by payload_digest), failure-isolation tests, full suite + guard stack; evidence under reports/capsule-decisions-dualwrite/ | docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task204-capsule-decisions-dualwrite-ACTIVE/`
- `.taskmaster/tasks/task_204.md`
- `.taskmaster/tasks/task_204.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `204`

## Branch Policy
- Working branch: `feat/task-204-capsule-decisions-dualwrite`

## Amendments & Versioning
- 2026-06-10 - Task 204 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 204 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md section 2 (gate-decisions migration) and designs/decisions-dualwrite-scope.md.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: ledger append must never break or delay a gate decision; JSONL stays primary; do not freeze or migrate JSONL in this PR.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
