---
session_id: 2026-05-07-005
work_context: task10-reference-fix-scripts
handler_target: .taskmaster/tasks/task_010.txt
task_ids: [10]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/
  - .taskmaster/tasks/task_010.txt
  - scripts/template-ssot-scanner/apply_reference_fixes.py
  - scripts/template-ssot-scanner/generate_fixes.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 10 Implement Reference Fix Scripts

## Header
- **Session ID (S)**: 2026-05-07-005
- **Work Context (W)**: task10-reference-fix-scripts
- **Handler Target (H)**: .taskmaster/tasks/task_010.txt
- **Task IDs**: 10
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/, .taskmaster/tasks/task_010.txt, scripts/template-ssot-scanner/apply_reference_fixes.py, scripts/template-ssot-scanner/generate_fixes.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical reference-fix task wording against the current portable foundation and scanner suite | docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/designs/scope-reconciliation.md | completed |
| plan-step-implement | Implement safe reference-fix runner, generated wrappers, documentation, and focused tests | scripts/template-ssot-scanner/apply_reference_fixes.py; scripts/template-ssot-scanner/generate_fixes.py; scripts/template-ssot-scanner/test_cli_behavior.py; scripts/template-ssot-scanner/README.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/reports/reference-fix-scripts/verification-2026-05-07.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/`
- `.taskmaster/tasks/task_010.txt`
- `scripts/template-ssot-scanner/apply_reference_fixes.py`
- `scripts/template-ssot-scanner/generate_fixes.py`
- `scripts/template-ssot-scanner/README.md`
- `scripts/template-ssot-scanner/test_cli_behavior.py`
- Taskmaster Task `10`

## Branch Policy
- Working branch: `feat/task-10-reference-fix-scripts`

## Amendments & Versioning
- 2026-05-07 - Task 10 kickoff created via the guided wizard flow.
- 2026-05-07 - Corrected generic kickoff plan wording to the current reference-fix scope and marked plan-step-scope complete.
- 2026-05-07 - Safe reference-fix runner, generated wrappers, docs, and tests completed; plan-step-implement marked complete.
- 2026-05-07 - Final validation passed and plan-step-verify marked complete.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 10 and its subtasks.
  3. Review `designs/scope-reconciliation.md` before changing scanner behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: commit, push, open PR, and archive after merge.

## Conflict & Scope Declaration
- Related plans: Task 7 baseline scanner outputs, Task 8 registry system, Task 99 portable foundation spec.
- Guard cross-check: reference-fix tooling must preserve dry-run safety and avoid untracked generated-script mutation as the primary implementation.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
