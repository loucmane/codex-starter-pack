---
session_id: 2026-06-05-003
work_context: task164-shadow-precision-toolchain-baseline
handler_target: aegis_foundation/reconcile_shadow_precision.py
task_ids: [164]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/
  - aegis_foundation/taskmaster_toolchain.py
  - .github/workflows/ci.yml
  - tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py
  - tests/meta_workflow_guard/test_ci_workflows.py
  - .taskmaster/tasks/task_164.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 164 Wire shadow precision CI toolchain staleness to frozen baseline

## Header
- **Session ID (S)**: 2026-06-05-003
- **Work Context (W)**: task164-shadow-precision-toolchain-baseline
- **Handler Target (H)**: aegis_foundation/reconcile_shadow_precision.py
- **Task IDs**: 164
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/, aegis_foundation/taskmaster_toolchain.py, .github/workflows/ci.yml, tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py, tests/meta_workflow_guard/test_ci_workflows.py, .taskmaster/tasks/task_164.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Identify the CI precision corpus self-comparison and keep scope to the shadow precision toolchain binding | docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/FINDINGS.md | completed |
| plan-step-implement | Add the validated CI baseline helper, wire CI to compare baseline vs current evidence, and document the contract | aegis_foundation/taskmaster_toolchain.py; .github/workflows/ci.yml; docs/aegis/reconcile-shadow-apply-contract.md; docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused pytest, whitespace, and Taskmaster health evidence | docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260605-task164-shadow-precision-toolchain-baseline-ACTIVE/`
- `aegis_foundation/taskmaster_toolchain.py`
- `.github/workflows/ci.yml`
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py`
- `tests/meta_workflow_guard/test_ci_workflows.py`
- `.taskmaster/tasks/task_164.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `164`

## Branch Policy
- Working branch: `feat/task-164-shadow-precision-toolchain-baseline`

## Amendments & Versioning
- 2026-06-05 - Task 164 kickoff created via the guided wizard flow.
- 2026-06-05 - Reframed the generic kickoff plan around the concrete precision corpus CI baseline implementation and completed scope/implement/verify locally.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 164 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: PR CI must emit and upload the precision corpus artifact so the real integration evidence can be inspected before Task 164 is marked done.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Tracker/session entries for kickoff and implementation progress
- Focused precision corpus and workflow-contract pytest evidence
- Taskmaster health and whitespace evidence
- PR CI artifact inspection before closeout

## Emergency Bypass Protocol
- No bypass authorized.
