---
session_id: 2026-05-12-002
work_context: task36-template-governance-board
handler_target: .taskmaster/tasks/task_036.txt
task_ids: [36]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/
  - .taskmaster/tasks/task_036.txt
  - templates/metadata/template-governance-policy.json
  - scripts/template_governance.py
  - tests/meta_workflow_guard/test_template_governance.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 36 Implement Template Governance Board

## Header
- **Session ID (S)**: 2026-05-12-002
- **Work Context (W)**: task36-template-governance-board
- **Handler Target (H)**: .taskmaster/tasks/task_036.txt
- **Task IDs**: 36
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/, .taskmaster/tasks/task_036.txt, templates/metadata/template-governance-policy.json, scripts/template_governance.py, tests/meta_workflow_guard/test_template_governance.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical governance-board wording against the current portable foundation | docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/designs/template-governance-scope-reconciliation.md | completed |
| plan-step-implement | Add portable governance policy, non-mutating assessor CLI, and focused tests | templates/metadata/template-governance-policy.json; scripts/template_governance.py; tests/meta_workflow_guard/test_template_governance.py; docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/reports/template-governance-board/; docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/`
- `.taskmaster/tasks/task_036.txt`
- `templates/metadata/template-governance-policy.json`
- `scripts/template_governance.py`
- `tests/meta_workflow_guard/test_template_governance.py`
- `tests/`
- Taskmaster Task `36`

## Branch Policy
- Working branch: `feat/task-36-template-governance-board`

## Amendments & Versioning
- 2026-05-12 - Task 36 kickoff created via the guided wizard flow.
- 2026-05-12 - Scope corrected from generic wizard wording to portable template governance assessment.
- 2026-05-12 - Added template governance policy, non-mutating assessor CLI, and focused governance tests.
- 2026-05-12 - Stored final Task 36 evidence and marked Taskmaster Task 36 done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 36 and its subtasks.
  3. Review the governance scope reconciliation before changing helper behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the governance layer non-mutating and evidence-backed; do not add live meeting, voting, or notification infrastructure.

## Conflict & Scope Declaration
- Related plans: Task 29 lifecycle policy, Task 58 versioning policy, Task 35 emergency response, Tasks 94-95 enforcement groundwork.
- Guard cross-check: governance assessment must complement existing lifecycle/versioning helpers and produce evidence without becoming a second enforcement authority.

## Evidence Checklist
- Governance scope reconciliation under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the governance assessor lands

## Emergency Bypass Protocol
- No bypass authorized.
