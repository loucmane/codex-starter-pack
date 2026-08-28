---
session_id: 2026-08-28-001
work_context: ga-iqbd-modular-workflow-gate
handler_target: aegis_foundation/gate
bead_ids: [ga-iqbd]
branch_policy: codex/ga-iqbd-modular-workflow-gate
evidence_summary:
  - docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED
  - aegis_foundation/gate/readiness.py
  - aegis_foundation/gate/hooks/entrypoint.py
  - bead:ga-iqbd
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-iqbd Modularize Aegis workflow gate and retire Claude readiness monolith

## Header
- **Session ID (S)**: 2026-08-28-001
- **Work Context (W)**: ga-iqbd-modular-workflow-gate
- **Handler Target (H)**: aegis_foundation/gate
- **Bead IDs**: ga-iqbd
- **Branch Policy**: codex/ga-iqbd-modular-workflow-gate
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED, aegis_foundation/gate/readiness.py, aegis_foundation/gate/hooks/entrypoint.py, bead:ga-iqbd
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Modularize Aegis workflow gate and retire Claude readiness monolith | docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED/FINDINGS.md | completed |
| plan-step-implement | Implement Modularize Aegis workflow gate and retire Claude readiness monolith through the reviewed helper surface | aegis_foundation/gate/readiness.py; aegis_foundation/gate/hooks/entrypoint.py; docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED`
- `aegis_foundation/gate/**`
- `.claude/scripts/gate_lib.py`
- `.claude/scripts/readiness.sh`
- `aegis_foundation/assets/.claude/scripts/**`
- `scripts/codex-task`
- `scripts/codex-guard`
- `tests/`
- Primary bead `ga-iqbd`

## Branch Policy
- Working branch: `codex/ga-iqbd-modular-workflow-gate`

## Amendments & Versioning
- 2026-08-28 - Bead `ga-iqbd` kickoff created through the bead-native source workflow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-iqbd` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/archive/20260828-ga-iqbd-modular-workflow-gate-COMPLETED/TRACKER.md` before changing implementation.
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
