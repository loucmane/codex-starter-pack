---
session_id: 2026-06-09-001
work_context: task183-safe-repair-while-blocked
handler_target: .claude/scripts/gate_lib.py
task_ids: [183]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/
  - .claude/scripts/gate_lib.py
  - .taskmaster/tasks/task_183.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 183 Allow safe Aegis repair while readiness is blocked

## Header
- **Session ID (S)**: 2026-06-09-001
- **Work Context (W)**: task183-safe-repair-while-blocked
- **Handler Target (H)**: .claude/scripts/gate_lib.py
- **Task IDs**: 183
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/, .claude/scripts/gate_lib.py, .taskmaster/tasks/task_183.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the safe repair recovery boundary for BLOCKED readiness | docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Allow only project-confined Aegis repair apply through the BLOCKED readiness gate | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py; docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Cover CLI/MCP repair apply and non-repair blocking regressions | tests/claude_adapter/test_pretooluse_gates.py; docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260609-task183-safe-repair-while-blocked-ACTIVE/`
- `.claude/scripts/gate_lib.py`
- `.taskmaster/tasks/task_183.md`
- `tests/`
- Taskmaster Task `183`

## Branch Policy
- Working branch: `feat/task-183-safe-repair-while-blocked`

## Amendments & Versioning
- 2026-06-09 - Task 183 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 183 and its subtasks.
  3. Review the safe-repair gate boundary before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep BLOCKED-state recovery limited to Aegis safe repair apply; do not generalize it to arbitrary repair-adjacent commands.

## Conflict & Scope Declaration
- Related plans: Tasks 180-182 observation-mode hardening.
- Guard cross-check: safe repair apply is permitted only after target-dir confinement and before normal pending-tracking enforcement.

## Evidence Checklist
- Decision note documenting the safe repair boundary
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence for the safe repair gate fix

## Emergency Bypass Protocol
- No bypass authorized.
