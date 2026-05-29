---
session_id: 2026-05-28-003
work_context: task129-aegis-doctor-repair-idempotency
handler_target: scripts/_aegis_installer.py
task_ids: [129]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/
  - scripts/_aegis_installer.py
  - .taskmaster/tasks/task_129.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 129 Aegis Doctor, Repair, and Idempotency Hardening

## Header
- **Session ID (S)**: 2026-05-28-003
- **Work Context (W)**: task129-aegis-doctor-repair-idempotency
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 129
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_129.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Document the Aegis state recovery model, idempotency boundaries, and safe repair policy before implementation | docs/aegis/state-recovery-model.md; docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Implement doctor/repair CLI and MCP surfaces plus replay-safe workflow behavior | scripts/_aegis_installer.py; aegis_foundation/cli.py; scripts/codex-task; aegis_mcp/server.py; .claude/scripts/gate_lib.py; docs/aegis/; aegis_foundation/assets/; docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused regression evidence, update handoff, and confirm Taskmaster status | tests/meta_workflow_guard/; docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/reports/doctor-repair/verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/`
- `scripts/_aegis_installer.py`
- `.taskmaster/tasks/task_129.md`
- `scripts/codex-task`
- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `docs/aegis/`
- `aegis_foundation/assets/`
- `tests/`
- Taskmaster Task `129`

## Branch Policy
- Working branch: `feat/task-129-aegis-doctor-repair-idempotency`

## Amendments & Versioning
- 2026-05-28 - Task 129 kickoff created via the guided wizard flow.
- 2026-05-28 - Plan corrected from generic wizard wording to the actual doctor/repair/idempotency scope.
- 2026-05-28 - Added doctor/repair core, CLI, MCP, hook-classifier, asset, and regression-test coverage.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 129 and its subtasks.
  3. Review `docs/aegis/state-recovery-model.md` before changing doctor/repair behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep doctor/repair grounded in the existing Aegis core and avoid hidden mutation in diagnostics.

## Conflict & Scope Declaration
- Related plans: Tasks 127 handoff repair, 128 closeout/local-start hardening.
- Guard cross-check: doctor must be read-only; repair must require explicit apply and avoid overwriting divergent user files.

## Evidence Checklist
- State recovery model in `docs/aegis/state-recovery-model.md`
- Tracker/session entries for scope, implementation, and verification progress
- Focused test and guard evidence once doctor/repair implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
