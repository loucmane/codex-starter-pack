---
session_id: 2026-07-11-003
work_context: task244-derivable-source-closeout
handler_target: scripts/_source_workflow_state.py
task_ids: [244]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/
  - docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/designs/source-closeout-derivation-contract.md
  - scripts/_source_workflow_state.py
  - .claude/scripts/readiness.sh
  - scripts/codex-guard
plan_version: v2
emergency_bypass: false
---

# Plan - Task 244 Make Upstream Source Closeout State Derivable

## Header
- **Session ID (S)**: 2026-07-11-003
- **Work Context (W)**: task244-derivable-source-closeout
- **Handler Target (H)**: scripts/_source_workflow_state.py
- **Task IDs**: 244
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: source closeout derivation contract, source-only resolver, canonical and packaged readiness/guard assets, focused lifecycle tests, and live Task 237/244 dogfood
- **Plan Version**: v2
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define fail-closed source-checkout detection, completed archive derivation, installed-target exclusion, and rollback | docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/designs/source-closeout-derivation-contract.md; docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/DECISIONS.md | completed |
| plan-step-implement | Add one source-only resolver consumed by readiness and guard, keeping installed-target behavior unchanged | scripts/_source_workflow_state.py; .claude/scripts/readiness.sh; aegis_foundation/assets/.claude/scripts/readiness.sh; scripts/codex-guard; aegis_foundation/assets/scripts/codex-guard | completed |
| plan-step-verify | Exercise positive and negative derivation, archive, next kickoff, CI-clean checkout, mirror parity, guard, and live closeout dogfood | tests/meta_workflow_guard/test_source_checkout_closeout.py; tests/meta_workflow_guard/test_guard_rules.py; tests/meta_workflow_guard/test_codex_task.py; docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/reports/derivable-source-closeout/task-verification.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/`
- `scripts/_source_workflow_state.py`
- `.claude/scripts/readiness.sh`
- `aegis_foundation/assets/.claude/scripts/readiness.sh`
- `scripts/codex-guard`
- `aegis_foundation/assets/scripts/codex-guard`
- `tests/meta_workflow_guard/test_source_checkout_closeout.py`
- focused existing guard and codex-task tests
- `docs/aegis/source-checkout-closeout-contract.md`
- Taskmaster Task `244`

## Branch Policy
- Working branch: `feat/task-244-derivable-source-closeout`

## Amendments & Versioning
- 2026-07-11 - Task 244 kickoff created via the guided wizard flow.
- 2026-07-11 - Replaced the generic wizard plan with the fail-closed source closeout derivation contract; installed-target behavior and legacy work-tracking retention remain unchanged.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 244 and its subtasks.
  3. Review `designs/source-closeout-derivation-contract.md` before changing source lifecycle behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: reject false source-checkout detection, ambiguous archives, mismatched tracker identity, and any installed-target fallback that bypasses current-work state.

## Conflict & Scope Declaration
- Related tasks: 235 managed-update safety, 236 convergence roadmap, 237 mode-aware guidance, and the hybrid knowledge-vault follow-on.
- Guard cross-check: source derivation applies only when no installed manifest or current-work state exists; installed targets keep the current contract.

## Evidence Checklist
- Source closeout derivation contract under `designs/`
- Positive and fail-closed source/installed fixture coverage
- Canonical/package parity for modified managed assets
- Live Task 244 archive and completed-source readiness/guard evidence

## Emergency Bypass Protocol
- No bypass authorized.
