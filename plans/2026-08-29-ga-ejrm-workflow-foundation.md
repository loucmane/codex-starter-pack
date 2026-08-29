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
