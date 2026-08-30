---
session_id: 2026-08-30-004
work_context: ga-k0ry-evidence-workflow-v1
handler_target: plugins/gas-city-workflow
bead_ids: [ga-k0ry]
branch_policy: codex/ga-k0ry-evidence-workflow-v1
evidence_summary:
  - docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE
  - plugins/gas-city-workflow
  - docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/designs/evidence-workflow-v1-contract.md
  - bead:ga-k0ry
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-k0ry Evidence workflow v1 — frozen-run schema, validators, and HPFetcher shadow pilot

## Header
- **Session ID (S)**: 2026-08-30-004
- **Work Context (W)**: ga-k0ry-evidence-workflow-v1
- **Handler Target (H)**: plugins/gas-city-workflow
- **Bead IDs**: ga-k0ry
- **Branch Policy**: codex/ga-k0ry-evidence-workflow-v1
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE, plugins/gas-city-workflow, docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/designs/evidence-workflow-v1-contract.md, bead:ga-k0ry, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Evidence workflow v1 — frozen-run schema, validators, and HPFetcher shadow pilot | docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/designs/evidence-workflow-v1-contract.md | completed |
| plan-step-implement | Implement the generic frozen-run schema, skill, five validators, and fail-closed fixtures | plugins/gas-city-workflow; tests/meta_workflow_guard; docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-profile | Add the digest-bound project-owned HPFetcher profile and bundle builders without changing domain verdict logic | commit:7ee1f35a9260a27090720197b4487164b427df54; run:hpf-nqzf-batch13-shadow-20260830-001 | completed |
| plan-step-pilot | Run one authorized report-only frozen shadow pilot with seal/dispatch/release ordering, Fable readback, zero residue, and authoritative-output parity | bead:hpf-nqzf; run:hpf-nqzf-batch13-shadow-20260830-001; repair-run:pending | in_progress |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE`
- `plugins/gas-city-workflow`
- project-owned HPFetcher evidence profile and bundle builders in an isolated `loucmane/hp-coach` worktree
- `scripts/codex-task`
- `scripts/codex-guard`
- `tests/`
- Primary bead `ga-k0ry`

## Branch Policy
- Working branch: `codex/ga-k0ry-evidence-workflow-v1`

## Amendments & Versioning
- 2026-08-30 - Bead `ga-k0ry` kickoff created through the bead-native source workflow.
- 2026-08-30 - Adopted the reviewed five-script v1 cut: generic code remains plugin-owned; domain profile/builders remain project-owned; authoritative mode is structurally unavailable.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-k0ry` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/active/20260830-ga-k0ry-evidence-workflow-v1-ACTIVE/TRACKER.md` before changing implementation.
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
