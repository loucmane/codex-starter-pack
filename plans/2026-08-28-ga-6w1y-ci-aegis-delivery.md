---
session_id: 2026-08-28-004
work_context: ga-6w1y-ci-aegis-delivery
handler_target: .github/workflows/ci.yml
bead_ids: [ga-6w1y]
branch_policy: codex/ga-6w1y-ci-aegis-delivery
evidence_summary:
  - docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE
  - bead:ga-6w1y
  - .github/workflows
  - aegis.delivery-policy.json
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ga-6w1y Repair CI and Aegis delivery contract

## Header
- **Session ID (S)**: 2026-08-28-004
- **Work Context (W)**: ga-6w1y-ci-aegis-delivery
- **Handler Target (H)**: .github/workflows/ci.yml
- **Bead IDs**: ga-6w1y
- **Branch Policy**: codex/ga-6w1y-ci-aegis-delivery
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE, bead:ga-6w1y, .github/workflows, aegis.delivery-policy.json
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and authority for Repair CI and Aegis delivery contract | docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Implement Repair CI and Aegis delivery contract through the reviewed helper surface | .github/workflows; aegis.delivery-policy.json; docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Capture tests, review evidence, and bead readback | docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE/TRACKER.md | in_progress |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE`
- `.github/workflows/`
- `.github/dependabot.yml`
- `aegis.delivery-policy.json`
- lockfile and supported-runtime metadata used by hosted CI
- workflow-focused tests and operator documentation
- `tests/`
- Primary bead `ga-6w1y`

## Branch Policy
- Working branch: `codex/ga-6w1y-ci-aegis-delivery`

## Amendments & Versioning
- 2026-08-28 - Bead `ga-6w1y` kickoff created through the bead-native source workflow.
- 2026-08-28 - Implementation completed: locked `uv` CI, Python 3.11-3.14,
  immutable action pins, explicit permissions/timeouts/concurrency, conditional legacy
  Taskmaster compatibility, Dependency Review/Dependabot, and merge-method parity.
- 2026-08-28 - Hosted exact-head verification passed every executable source check,
  including the full Python matrix and legacy compatibility. Dependency Review failed
  before analysis because the repository Dependency Graph is disabled. Repository
  policy readback also showed that only Python 3.11/3.12 are required and both guard
  workflows published the ambiguous context `guard`; the guard jobs were renamed to
  unique contexts so one consolidated settings update can enforce the complete suite.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Read primary bead `ga-6w1y` through the rig-scoped bead surface.
  3. Review `docs/ai/work-tracking/active/20260828-ga-6w1y-ci-aegis-delivery-ACTIVE/TRACKER.md` before changing implementation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: publish the amended signed exact head, enable Dependency
  Graph and the reviewed repository security features, require the uniquely named
  hosted checks in the active main-branch ruleset, and retain legacy Taskmaster only
  as conditional compatibility evidence.

## Conflict & Scope Declaration
- Related plans: none declared at kickoff.
- Guard cross-check: bead-native work must preserve plan/tracker/session compliance.

## Evidence Checklist
- Bead readback and reviewed authority
- Tracker/session entries for implementation progress
- Full locked suite (`2254 passed, 21 skipped`)
- Pinned Taskmaster 0.43.1 compatibility (`116 passed`)
- Focused tests, workflow parsing, lint, lock, and guard evidence
- Hosted exact-head workflow evidence and repository-setting readback
- Initial hosted run `33213345409`: Python 3.11-3.14, legacy Taskmaster compatibility,
  Codex Guard, Meta Workflow Guard, Aegis witness, and evidence-gated delivery passed.
- Dependency Review run `33213345623`: infrastructure refusal because Dependency Graph
  is disabled; no dependency analysis ran.
- Repository policy readback: merge-commit-only repository policy; active ruleset
  `19060058`; required checks currently only Python 3.11/3.12; zero PR review threads.

## Emergency Bypass Protocol
- No bypass authorized.
