---
session_id: 2026-08-28-002
work_context: ga-p60k-gpg-readiness
handler_target: scripts/codex-gpg-readiness
bead_ids: [ga-p60k]
branch_policy: codex/ga-p60k-gpg-readiness-r2
evidence_summary:
  - docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE
  - scripts/codex-gpg-readiness
  - bead:ga-p60k
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-p60k Pin personal GPG readiness to the intended signing subkey

## Header
- **Session ID (S)**: 2026-08-28-002
- **Work Context (W)**: ga-p60k-gpg-readiness
- **Handler Target (H)**: scripts/codex-gpg-readiness
- **Bead IDs**: ga-p60k
- **Branch Policy**: codex/ga-p60k-gpg-readiness-r2
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE, scripts/codex-gpg-readiness, bead:ga-p60k, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Pin personal GPG readiness to the intended signing subkey | docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement Pin personal GPG readiness to the intended signing subkey through the reviewed helper surface | scripts/codex-gpg-readiness; docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE`
- `scripts/codex-gpg-readiness`
- `scripts/codex-task`
- `scripts/codex-guard`
- `tests/`
- Primary bead `ga-p60k`

## Branch Policy
- Working branch: `codex/ga-p60k-gpg-readiness-r2`

## Amendments & Versioning
- 2026-08-28 - Bead `ga-p60k` kickoff created through the bead-native source workflow.
- 2026-08-28 - Live GnuPG 2.4.4 evidence replaced cache-flag-only readiness with the
  equivalent exact-cache or expiring agent-epoch-signature proof contract.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-p60k` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/active/20260828-ga-p60k-gpg-readiness-ACTIVE/TRACKER.md` before changing implementation.
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
