---
session_id: 2026-07-12-004
work_context: task238-universal-context-budgets
handler_target: aegis_foundation/output_budget.py
task_ids: [238]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/
  - aegis_foundation/output_budget.py
  - .taskmaster/tasks/task_238.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 238 Enforce Universal Context Budgets Across Aegis Commands

## Header
- **Session ID (S)**: 2026-07-12-004
- **Work Context (W)**: task238-universal-context-budgets
- **Handler Target (H)**: aegis_foundation/output_budget.py
- **Task IDs**: 238
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/, aegis_foundation/output_budget.py, .taskmaster/tasks/task_238.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the universal output-budget contract, compatibility boundary, detail modes, artifact ownership, and fail-closed hard caps | docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/designs/context-budget-contract.md | completed |
| plan-step-implement | Implement the shared renderer and integrate status, next, readiness, doctor, verify, update, witness, replay, and closeout failure surfaces without changing command semantics | aegis_foundation/output_budget.py; aegis_foundation/cli.py; aegis_mcp/server.py; .claude/scripts/readiness.sh; aegis_foundation/replay.py; docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove 60-line/8-KiB defaults, bounded verbose and intentional full detail, exact category counts, complete artifacts, 0/10/3500/100000 fixtures, HP-Fetcher one-screen dogfood, rollback, and hosted CI | tests/; docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/reports/universal-context-budgets/task-verification.md; docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/HANDOFF.md | in-progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/`
- `aegis_foundation/output_budget.py`
- `aegis_foundation/cli.py`
- `aegis_foundation/replay.py`
- `aegis_mcp/server.py`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `.claude/scripts/readiness.sh`
- `aegis_foundation/assets/.claude/scripts/readiness.sh`
- `.claude/scripts/witness_lib.py`
- `aegis_foundation/assets/.claude/scripts/witness_lib.py`
- `docs/aegis/invocation-contract.md`
- `aegis_foundation/assets/docs/aegis/invocation-contract.md`
- `docs/aegis/aegis-usability-convergence-roadmap.md`
- `.taskmaster/tasks/task_238.md`
- `tests/`
- Taskmaster Task `238`

## Branch Policy
- Working branch: `feat/task-238-universal-context-budgets`

## Amendments & Versioning
- 2026-07-12 - Task 238 kickoff created via the guided wizard flow.
- 2026-07-12 - Replaced the generic wizard implementation wording with the binding C2 output-budget contract and added readiness because the active goal explicitly requires every agent-facing readiness surface to be bounded too.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 238 and its subtasks.
  3. Review `designs/context-budget-contract.md` before changing renderer or CLI behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep full internal payloads and report artifacts backward-compatible; bounded default JSON may sample collections but must retain top-level identity/status fields plus exact omission metadata; `--all` is intentional and must never be invoked implicitly by agent guidance.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Context-budget contract under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored fixture, HP-Fetcher dogfood, metrics, test, guard, witness, and hosted-CI evidence

## Emergency Bypass Protocol
- No bypass authorized.
