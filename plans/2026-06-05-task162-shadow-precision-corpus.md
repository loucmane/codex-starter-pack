---
session_id: 2026-06-05-001
work_context: task162-shadow-precision-corpus
handler_target: aegis_foundation/reconcile_shadow_precision.py
task_ids: [162]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/
  - aegis_foundation/reconcile_shadow_precision.py
  - tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py
  - .github/workflows/ci.yml
  - .taskmaster/tasks/task_162.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 162 Build replayable precision corpus for shadow apply

## Header
- **Session ID (S)**: 2026-06-05-001
- **Work Context (W)**: task162-shadow-precision-corpus
- **Handler Target (H)**: aegis_foundation/reconcile_shadow_precision.py
- **Task IDs**: 162
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/, aegis_foundation/reconcile_shadow_precision.py, tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py, .github/workflows/ci.yml, .taskmaster/tasks/task_162.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the evidence-only replayable precision corpus boundary and preserve operational, cascade-smoke, and precision stream separation | docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/FINDINGS.md; docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/DECISIONS.md | completed |
| plan-step-implement | Build the reviewed real-git shadow precision corpus artifact, CI emission, stream classification, and contract documentation without adding apply or enablement surfaces | aegis_foundation/reconcile_shadow_precision.py; tests/fixtures/aegis/reconcile_shadow_precision_corpus.json; .github/workflows/ci.yml; docs/aegis/reconcile-shadow-apply-contract.md | completed |
| plan-step-verify | Prove the corpus replay, label-disposition gate, stream separation, CI workflow wiring, Taskmaster health, and no-whitespace regressions | tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py; tests/meta_workflow_guard/test_ci_workflows.py; docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260605-task162-shadow-precision-corpus-ACTIVE/`
- `aegis_foundation/reconcile_shadow_precision.py`
- `tests/fixtures/aegis/reconcile_shadow_precision_corpus.json`
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py`
- `tests/meta_workflow_guard/test_ci_workflows.py`
- `.github/workflows/ci.yml`
- `docs/aegis/reconcile-shadow-apply-contract.md`
- `.taskmaster/tasks/task_162.md`
- `.taskmaster/tasks/task_164.md`
- Taskmaster Task `162`

## Branch Policy
- Working branch: `feat/task-162-shadow-precision-corpus`

## Amendments & Versioning
- 2026-06-05 - Task 162 plan reconstructed during commit closeout after implementation and validation evidence was already captured.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 162 and follow-up Task 164.
  3. Review the precision corpus fixture and CI artifact contract before changing shadow evidence metrics.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: Task 164 must wire the CI precision corpus toolchain-staleness gate to a frozen validated baseline before any enablement-gate work relies on it.

## Conflict & Scope Declaration
- Related plans: Tasks 146, 158, 160, and 161 reconcile precision/shadow evidence groundwork.
- Guard cross-check: Task 162 is evidence-only. It must not add apply, enablement, MCP apply tools, agent-reachable mutation, or Taskmaster status mutation against the governed repo.

## Evidence Checklist
- Reviewed labeled precision corpus fixture
- Real-git synthetic replay artifact builder and CI emission under runner temp
- Stream-classification contract proving only the precision corpus counts toward enablement precision
- Focused and adjacent Aegis regression suites

## Emergency Bypass Protocol
- No bypass authorized.
