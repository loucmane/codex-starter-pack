---
session_id: 2026-05-11-004
work_context: task39-guard-auto-fix-mode
handler_target: .taskmaster/tasks/task_039.txt
task_ids: [39]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/
  - .taskmaster/tasks/task_039.txt
  - scripts/codex-guard
plan_version: v1
emergency_bypass: false
---

# Plan - Task 39 Implement Auto-Fix Mode for Guard

## Header
- **Session ID (S)**: 2026-05-11-004
- **Work Context (W)**: task39-guard-auto-fix-mode
- **Handler Target (H)**: scripts/codex-guard
- **Task IDs**: 39
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/, .taskmaster/tasks/task_039.txt, scripts/codex-guard
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical auto-fix scope against the current guard and define the safe initial fix boundary | docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/designs/guard-auto-fix-scope-reconciliation.md | completed |
| plan-step-implement | Implement bounded preview-first guard auto-fix support and focused tests | scripts/codex-guard; tests/meta_workflow_guard/test_guard_rules.py; docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/reports/guard-auto-fix-mode/tests-2026-05-11-guard-rules.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/reports/guard-auto-fix-mode/guard-2026-05-11-final.txt; docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/reports/guard-auto-fix-mode/taskmaster-show-39-2026-05-11.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260511-task39-guard-auto-fix-mode-ACTIVE/`
- `.taskmaster/tasks/task_039.txt`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/test_guard_rules.py`
- `tests/`
- Taskmaster Task `39`

## Branch Policy
- Working branch: `feat/task-39-guard-auto-fix-mode`

## Amendments & Versioning
- 2026-05-11 - Task 39 kickoff created via the guided wizard flow.
- 2026-05-11 - Scope corrected from generic wizard scaffolding to bounded `scripts/codex-guard` auto-fix mode.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 39 and its subtasks.
  3. Review the guard auto-fix scope artifact before changing guard behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep auto-fix bounded, preview-first, and validation-backed; do not infer missing workflow evidence.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: auto-fix must not bypass plan/tracker/session compliance or hide remaining guard failures.

## Evidence Checklist
- Guard auto-fix scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
