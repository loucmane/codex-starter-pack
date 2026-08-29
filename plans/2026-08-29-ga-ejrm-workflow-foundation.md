---
session_id: 2026-08-29-003
work_context: ga-ejrm-workflow-foundation
handler_target: scripts/_source_workflow_state.py
bead_ids: [ga-ejrm]
branch_policy: codex/ga-ejrm-workflow-foundation
evidence_summary:
  - docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE
  - scripts/_source_workflow_state.py
  - bead:ga-ejrm
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-ejrm Transactional workflow foundation and reusable project plugin

## Header
- **Session ID (S)**: 2026-08-29-003
- **Work Context (W)**: ga-ejrm-workflow-foundation
- **Handler Target (H)**: scripts/_source_workflow_state.py
- **Bead IDs**: ga-ejrm
- **Branch Policy**: codex/ga-ejrm-workflow-foundation
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE, scripts/_source_workflow_state.py, bead:ga-ejrm, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Transactional workflow foundation and reusable project plugin | docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement Transactional workflow foundation and reusable project plugin through the reviewed helper surface | scripts/_source_workflow_state.py; docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE/IMPLEMENTATION.md | in-progress |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE`
- `scripts/_source_workflow_state.py`
- `scripts/codex-task`
- `scripts/codex-guard`
- `tests/`
- Primary bead `ga-ejrm`

## Branch Policy
- Working branch: `codex/ga-ejrm-workflow-foundation`

## Amendments & Versioning
- 2026-08-29 - Bead `ga-ejrm` kickoff created through the bead-native source workflow.
- 2026-08-29 - Scope completed and implementation expanded to the lifecycle transaction,
  versioned Gas City Workflow plugin, and two-stage Gas City Operations naming migration.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-ejrm` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/active/20260829-ga-ejrm-workflow-foundation-ACTIVE/TRACKER.md` before changing implementation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve bead authority and avoid allocating shadow Taskmaster work.

## Conflict & Scope Declaration
- Related plans: none declared at kickoff.
- Guard cross-check: bead-native work must preserve plan/tracker/session compliance.

## Evidence Checklist
- Bead readback and reviewed authority
- Tracker/session entries for implementation progress
- Focused tests and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.

<!-- AEGIS:BEGIN generated-sweh-projection -->
<!-- AEGIS:projection-state {"event_count": 5, "last_event_id": "5f440613b053428cbdda1d7230c50045", "schema": "legacy-shadow-sweh-projection-v1"} -->

## Generated S:W:H:E Projection

_Generated from the passive Aegis ledger. Human-authored content outside this block is preserved._

- [S:cb975924-bfd0-4d6e-902f-e305554714f2 W:main H:session E:ledger:1ec75e34673...] Session began via startup.
- [S:cb975924-bfd0-4d6e-902f-e305554714f2 W:main H:failure E:ledger:0ff29381316...] Bash failure recorded.
- [S:02b8396d-4342-4720-87bd-61045504170d W:main H:session E:ledger:144264708a4...] Session began via startup.
- [S:unknown W:codex/ga-ejrm-witness-fix H:witness E:ledger:5cc03307509...] Delivery witness FAIL recorded at fba7ff62f; report: .aegis/reports/witness-report.json.
- [S:unknown W:codex/ga-ejrm-workflow-foundation H:witness E:ledger:5f440613b05...] Delivery witness FAIL recorded at 48cee7e06; report: .aegis/reports/witness-report.json.

<!-- AEGIS:END generated-sweh-projection -->
