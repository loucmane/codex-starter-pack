---
session_id: 2026-08-26-001
work_context: ga-k9sd-beads-first-guidance
handler_target: scripts/codex-task
bead_ids: [ga-k9sd]
branch_policy: codex/ga-k9sd-beads-first-guidance
evidence_summary:
  - docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/
  - bead:ga-k9sd
  - scripts/codex-task
  - scripts/codex-guard
  - docs/operations/codex-wsl-reboot-readiness.md
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-k9sd Beads-first workflow authority and reboot hardening

## Header
- **Session ID (S)**: 2026-08-26-001
- **Work Context (W)**: ga-k9sd-beads-first-guidance
- **Handler Target (H)**: scripts/codex-task
- **Bead IDs**: ga-k9sd
- **Branch Policy**: codex/ga-k9sd-beads-first-guidance
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/, bead:ga-k9sd, scripts/codex-task, scripts/codex-guard, docs/operations/codex-wsl-reboot-readiness.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Beads-first workflow authority and reboot hardening | docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement Beads-first workflow authority and reboot hardening through the reviewed helper surface | scripts/codex-task; scripts/codex-guard; docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/`
- `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, `README.md`
- `scripts/codex-task`
- `scripts/codex-guard`
- `.claude/scripts/readiness.sh`
- `aegis_foundation/assets/.claude/scripts/readiness.sh`
- `.claude/engine/claude-readiness.md`, `.claude/engine/runtime-contract.md`
- `aegis_foundation/assets/scripts/codex-task`
- `aegis_foundation/assets/scripts/codex-guard`
- `aegis_foundation/reboot_readiness.py`
- `scripts/codex-wsl-readiness`, `scripts/install-codex-wsl-readiness`
- `scripts/windows/gas-city-wsl-bootstrap.ps1`, `scripts/windows/install-gas-city-wsl-bootstrap.ps1`
- `docs/operations/codex-wsl-reboot-readiness.md`
- `tests/`
- Primary bead `ga-k9sd`

## Branch Policy
- Working branch: `codex/ga-k9sd-beads-first-guidance`

## Amendments & Versioning
- 2026-08-26 - Bead `ga-k9sd` kickoff created through the bead-native source workflow.
- 2026-08-26 - Scope marked complete after primary-bead readback, historical ACTIVE-folder adjudication, and Fable's reboot-package review.
- 2026-08-26 - Scope amended to repair the readiness migration blocker with a fail-closed bead-native source path while retaining numeric Taskmaster compatibility.
- 2026-08-26 - Scope amended after the first installation stopped safely on Task Scheduler principal-name normalization: compare the returned principal and current operator by canonical SID while preserving the current-user, Limited task contract.
- 2026-08-26 - Scope amended after the scheduled-task smoke exposed Windows PowerShell 5.1 incompatibilities: replace unreliable nested-process `$LASTEXITCODE` capture, remove unsupported `ConvertFrom-Json -Depth`, and require executable-doctor end-to-end evidence before reinstalling.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-k9sd` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/active/20260826-ga-k9sd-beads-first-guidance-ACTIVE/TRACKER.md` before changing implementation.
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
