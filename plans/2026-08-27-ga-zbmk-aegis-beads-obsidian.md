---
session_id: 2026-08-27-001
work_context: ga-zbmk-aegis-beads-obsidian
handler_target: aegis_foundation/obsidian_vault.py
bead_ids: [ga-zbmk]
branch_policy: codex/ga-zbmk-aegis-beads-obsidian
evidence_summary:
  - docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED
  - aegis_foundation/obsidian_vault.py
  - bead:ga-zbmk
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-zbmk Aegis beads-first authority and Obsidian closeout gate

## Header
- **Session ID (S)**: 2026-08-27-001
- **Work Context (W)**: ga-zbmk-aegis-beads-obsidian
- **Handler Target (H)**: aegis_foundation/obsidian_vault.py
- **Bead IDs**: ga-zbmk
- **Branch Policy**: codex/ga-zbmk-aegis-beads-obsidian
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED, aegis_foundation/obsidian_vault.py, bead:ga-zbmk, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Aegis beads-first authority and Obsidian closeout gate | docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED/FINDINGS.md | completed |
| plan-step-implement | Implement Aegis beads-first authority and Obsidian closeout gate through the reviewed helper surface | aegis_foundation/obsidian_vault.py; docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED`
- `.serena/memories/2026-08-27_ga-zbmk-aegis-beads-obsidian.md`
- `aegis_foundation/work_authority.py`
- `aegis_foundation/obsidian_vault.py`
- `aegis_foundation/legacy_projection.py`
- `aegis_foundation/cli.py`
- `tests/claude_adapter/test_work_authority.py`
- `tests/claude_adapter/test_obsidian_vault.py`
- `tests/meta_workflow_guard/reconcile_side_effect_oracle.py`
- `tests/meta_workflow_guard/test_aegis_invocation_contract.py`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py`
- `tests/meta_workflow_guard/test_aegis_release_distribution.py`
- `tests/meta_workflow_guard/test_continuation_contract.py`
- `tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py`
- `docs/aegis/obsidian-vault-projection.md`
- `docs/aegis/LEDGER_SCHEMA.md`
- `docs/aegis/legacy-shadow-sweh-projection-contract.md`
- `docs/aegis/beads-first-authority-and-obsidian-gate.md`
- Primary bead `ga-zbmk`

## Branch Policy
- Working branch: `codex/ga-zbmk-aegis-beads-obsidian`

## Amendments & Versioning
- 2026-08-27 - Bead `ga-zbmk` kickoff created through the bead-native source workflow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-zbmk` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/archive/20260827-ga-zbmk-aegis-beads-obsidian-COMPLETED/TRACKER.md` before changing implementation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve bead authority and avoid allocating shadow Taskmaster work.

## Conflict & Scope Declaration
- Related plans: `plans/2026-08-26-ga-k9sd-beads-first-guidance.md` established the bead-native source-workflow seam; this plan consumes that seam but does not modify any of its declared paths.
- Guard cross-check: bead-native work must preserve plan/tracker/session compliance.

## Evidence Checklist
- Bead readback and reviewed authority
- Tracker/session entries for implementation progress
- Focused tests and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
