---
session_id: 2026-08-29-002
work_context: ga-vqm2-recovery-certification
handler_target: Gas City managed-worker recovery and upgrade surfaces
bead_ids: [ga-vqm2]
branch_policy: codex/ga-vqm2-recovery-certification
evidence_summary:
  - docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED
  - Gas City managed-worker recovery and upgrade surfaces
  - bead:ga-vqm2
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-vqm2 Managed-worker recovery, drift, upgrades, and reboot survival

## Header
- **Session ID (S)**: 2026-08-29-002
- **Work Context (W)**: ga-vqm2-recovery-certification
- **Handler Target (H)**: Gas City managed-worker recovery and upgrade surfaces
- **Bead IDs**: ga-vqm2
- **Branch Policy**: codex/ga-vqm2-recovery-certification
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED, Gas City managed-worker recovery and upgrade surfaces, bead:ga-vqm2, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Managed-worker recovery, drift, upgrades, and reboot survival | docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED/FINDINGS.md | completed |
| plan-step-implement | Implement Managed-worker recovery, drift, upgrades, and reboot survival through the reviewed helper surface | Gas City managed-worker recovery and upgrade surfaces; docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED`
- `Gas City managed-worker recovery and upgrade surfaces`
- `scripts/codex-task`
- `scripts/codex-guard`
- `tests/`
- Primary bead `ga-vqm2`

## Branch Policy
- Working branch: `codex/ga-vqm2-recovery-certification`

## Amendments & Versioning
- 2026-08-29 - Bead `ga-vqm2` kickoff created through the bead-native source workflow.
- 2026-08-29 - Scope audit bound the remaining work to Blog linked-worktree metadata access, `ga-0szv` bundle/canary proof, `ga-bzn3` live delivery witness, and final recovery/reboot documentation and publication.
- 2026-08-29 - Blog access, watch-officer delivery, unread-mail recovery, tmux residue recovery, host readiness, live Obsidian indexing, durable recovery documentation, and `ga-0szv` future-project onboarding are complete. Final verification found only this coordinating bead active, with all project rigs suspended and zero sessions/residue.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-vqm2` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/archive/20260829-ga-vqm2-recovery-certification-COMPLETED/TRACKER.md` before changing implementation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: preserve bead authority; avoid shadow Taskmaster work, wildcard permissions, bespoke root scripts, and unnecessary reboot disruption.

## Conflict & Scope Declaration
- Related plans: none declared at kickoff.
- Guard cross-check: bead-native work must preserve plan/tracker/session compliance.

## Evidence Checklist
- Bead readback and reviewed authority
- Tracker/session entries for implementation progress
- Focused tests and guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
