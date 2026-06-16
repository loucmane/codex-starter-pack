---
session_id: 2026-06-16-002
work_context: task190-prd-bootstrap-flow
handler_target: scripts/_aegis_installer.py
task_ids: [190]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/
  - scripts/_aegis_installer.py
  - aegis_foundation/assets/scripts/_aegis_installer.py
  - tests/meta_workflow_guard/test_prd_bootstrap_states.py
  - .taskmaster/tasks/task_190.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 190 Support fresh-project PRD bootstrap continuation flow

## Header
- **Session ID (S)**: 2026-06-16-002
- **Work Context (W)**: task190-prd-bootstrap-flow
- **Handler Target (H)**: scripts/_aegis_installer.py
- **Task IDs**: 190
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/, scripts/_aegis_installer.py, .taskmaster/tasks/task_190.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile current next_action bootstrap + design the 5 fresh-project states (empty-state split, PRD detection, dispatch order) via design workflow | docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/designs/wizard-flow.md | completed |
| plan-step-implement | _empty_taskmaster_state + _prd_state + 5 next_action bootstrap states + 5 CONTINUATION_BRIEF_BY_STATE entries; assets mirror; tests | scripts/_aegis_installer.py; docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Design + adversarial-review workflows (verdict ship); 12 new + 4 updated tests; full suite 1699 passed (parallel); evidence stored | docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/reports/task190-prd-bootstrap-flow/tests-2026-06-16-final.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260616-task190-prd-bootstrap-flow-ACTIVE/`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `tests/meta_workflow_guard/test_prd_bootstrap_states.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `.taskmaster/tasks/task_190.md`
- Taskmaster Task `190`

## Branch Policy
- Working branch: `feat/task-190-prd-bootstrap-flow`

## Amendments & Versioning
- 2026-06-16 - Task 190 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 190 and its subtasks.
  3. Review the wizard design artifact before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the wizard grounded in the existing helper commands rather than creating a parallel workflow engine.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
