---
session_id: 2026-07-14-002
work_context: task251-aegis-advisory-pending-closeout
handler_target: scripts/_aegis_installer.py
task_ids: [251]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_251.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 251 Fix Aegis Advisory Pending Delivery Closeout Semantics

## Header
- **Session ID (S)**: 2026-07-14-002
- **Work Context (W)**: task251-aegis-advisory-pending-closeout
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 251
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/, scripts/_aegis_installer.py, .taskmaster/tasks/task_251.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the shared pending-state classifier, fail-closed boundary, preserved-evidence lifecycle, and Blog non-mutation boundary | docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/designs/wizard-flow.md | completed |
| plan-step-implement | Implement mode-aware pending semantics in the upstream and packaged Aegis runtime, bounded output, guidance, fixtures, and documentation | scripts/_aegis_installer.py; aegis_foundation/assets/scripts/_aegis_installer.py; docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove advisory preservation, strict fail-closed behavior, dry-run immutability, output budgets, source/package parity, and safe Blog retry guidance | docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/reports/aegis-advisory-pending-closeout/task-verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_foundation/output_budget.py`
- `docs/aegis/` and `aegis_foundation/assets/docs/aegis/`
- `.taskmaster/tasks/task_251.md`
- `tests/`
- Taskmaster Task `251`

## Branch Policy
- Working branch: `feat/task-251-aegis-advisory-pending-closeout`

## Amendments & Versioning
- 2026-07-14 - Task 251 kickoff created via the guided wizard flow.
- 2026-07-14 - Replaced the generic wizard-template scope with the Task 251 pending-state classifier and Blog non-mutation contract.
- 2026-07-14 - Completed the shared classifier, advisory/strict gate semantics, bounded output, replay fixture, runtime/docs parity, and downstream-safe retry documentation.
- 2026-07-14 - Stored focused, replay, repository-wide, parity, workflow, and non-temp reconcile verification evidence; no Blog rollout was attempted.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 251 and its subtasks.
  3. Review the pending-state classification artifact before changing verification or closeout behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve advisory evidence without allowing malformed or required tracking to pass; keep all agent-facing summaries context-bounded.

## Conflict & Scope Declaration
- Related plans: Tasks 221, 238, 245, 248, 249, and 250 establish queue classification, output budgets, continuation, Codex hooks, and delivery semantics.
- Guard cross-check: strict enforcement and untrusted pending state remain fail-closed; Blog rollout is a separate attended operation.

## Evidence Checklist
- Pending-state lifecycle design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the runtime implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
