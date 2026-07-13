---
session_id: 2026-07-13-004
work_context: task241-quiet-deterministic-witness
handler_target: .claude/scripts/witness_lib.py
task_ids: [241]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/
  - .claude/scripts/witness_lib.py
  - .taskmaster/tasks/task_241.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 241 Deliver A Quiet Deterministic Witness Shipping Interface

## Header
- **Session ID (S)**: 2026-07-13-004
- **Work Context (W)**: task241-quiet-deterministic-witness
- **Handler Target (H)**: .claude/scripts/witness_lib.py
- **Task IDs**: 241
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/, .claude/scripts/witness_lib.py, .taskmaster/tasks/task_241.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define stable witness classes, exact-HEAD/worktree isolation, complete delivery artifacts, CI honesty, and rollback | docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/designs/quiet-witness-contract.md | completed |
| plan-step-implement | Implement the contract in the live and packaged witness libraries plus the CLI while preserving installed-target compatibility | .claude/scripts/witness_lib.py; aegis_foundation/assets/.claude/scripts/witness_lib.py; aegis_foundation/cli.py; docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Run adversarial and full regressions, dogfood the real shipping step, store measurements, refresh continuity, and validate Taskmaster/Aegis | tests/claude_adapter/test_witness.py; docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/reports/quiet-deterministic-witness/task-verification.md; docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/HANDOFF.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/`
- `.claude/scripts/witness_lib.py`
- `aegis_foundation/assets/.claude/scripts/witness_lib.py`
- `aegis_foundation/cli.py`
- `.taskmaster/tasks/task_241.md`
- `tests/claude_adapter/test_witness.py`
- `tests/claude_adapter/test_output_budget.py`
- `docs/aegis/`
- Taskmaster Task `241`

## Branch Policy
- Working branch: `feat/task-241-quiet-witness`

## Amendments & Versioning
- 2026-07-13 - Task 241 kickoff created via the guided wizard flow.
- 2026-07-13 - Replaced the generic wizard placeholder with the binding quiet-witness contract; no runtime implementation began before scope completion.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 241 and its subtasks.
  3. Review `designs/quiet-witness-contract.md` before changing witness behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve CI process-success for honest `not_derivable_in_ci`, keep full evidence out of bounded stdout, and never consume sibling-worktree verification.

## Conflict & Scope Declaration
- Related plans: Task 238 context budgets and Task 240 worktree/child attribution are binding dependencies; Task 243 consumes the resulting evidence.
- Guard cross-check: the witness remains a delivery boundary and does not retire the complementary legacy workflow.

## Evidence Checklist
- Quiet-witness contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stable-class, worktree-isolation, adversarial, output-budget, and dogfood evidence

## Emergency Bypass Protocol
- No bypass authorized.
