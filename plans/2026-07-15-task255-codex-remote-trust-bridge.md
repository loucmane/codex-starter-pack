---
session_id: 2026-07-15-002
work_context: task255-codex-remote-trust-bridge
handler_target: aegis_foundation/codex_remote_trust.py
task_ids: [255]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/
  - aegis_foundation/codex_remote_trust.py
  - aegis_foundation/cli.py
  - tests/meta_workflow_guard/test_codex_remote_trust.py
  - docs/aegis/codex-remote-control-trust.md
plan_version: v2
emergency_bypass: false
---

# Plan - Task 255 Host-Scoped Codex Remote Control Trust Management

## Header
- **Session ID (S)**: 2026-07-15-002
- **Work Context (W)**: task255-codex-remote-trust-bridge
- **Handler Target (H)**: aegis_foundation/codex_remote_trust.py
- **Task IDs**: 255
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/, aegis_foundation/codex_remote_trust.py, aegis_foundation/cli.py, tests/meta_workflow_guard/test_codex_remote_trust.py, docs/aegis/codex-remote-control-trust.md
- **Plan Version**: v2
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Audit the active Codex homes and wrapper, define the host trust boundary, CLI contract, state model, and rollback invariants | docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/designs/codex-remote-trust-contract.md | completed |
| plan-step-implement | Implement the host module, nested CLI, managed config projection, locking, atomic writes, rollback, and diagnostics | aegis_foundation/codex_remote_trust.py; aegis_foundation/cli.py; docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Prove malformed-input refusal, context separation, preservation, idempotence, concurrency, rollback, hash-review behavior, package docs, and delivery readiness | tests/meta_workflow_guard/test_codex_remote_trust.py; docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/reports/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/`
- `aegis_foundation/codex_remote_trust.py`
- `aegis_foundation/cli.py`
- `docs/aegis/codex-remote-control-trust.md`
- `aegis_foundation/assets/docs/aegis/codex-remote-control-trust.md`
- `tests/meta_workflow_guard/test_codex_remote_trust.py`
- Taskmaster/session/plan/work-tracking projections for Task 255
- Taskmaster Task `255`

## Branch Policy
- Working branch: `feat/task-255-codex-remote-trust-bridge`

## Amendments & Versioning
- 2026-07-15 - Task 255 kickoff created via the guided wizard flow.
- 2026-07-15 - Replaced the generic wizard plan with the audited host-trust implementation contract (v2).

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 255 and its subtasks.
  3. Review `designs/codex-remote-trust-contract.md` before changing host trust behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: never blur project trust with Codex-owned exact-hook trust; never mutate the Blog checkout during upstream implementation.

## Conflict & Scope Declaration
- Related plans: Tasks 248-254 Codex hook adapter, migration, bootstrap, and portable trust verification.
- Guard cross-check: host config mutation must remain explicit, previewable, lock-protected, atomic, reversible, and outside project self-authorization.

## Evidence Checklist
- [x] Host trust contract under `designs/`
- [x] Focused unit and subprocess CLI results
- [x] Concurrency, rollback, idempotence, alias, and preservation evidence
- [x] Full source verification, guard, plan-sync, work-tracking, and archive-readiness evidence
- [ ] Protected CI, witness, and merge evidence

## Emergency Bypass Protocol
- No bypass authorized.
