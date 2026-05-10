---
session_id: 2026-05-10-006
work_context: task38-phase1-reference-remediation
handler_target: .taskmaster/tasks/task_038.txt
task_ids: [38]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/
  - .taskmaster/tasks/task_038.txt
  - scripts/template-ssot-scanner/apply_reference_fixes.py
  - scripts/template-ssot-scanner/generate_fixes.py
  - templates/registry/compatibility-map.json
  - templates/engine/verify-phase1.sh
plan_version: v1
emergency_bypass: false
---

# Plan - Task 38 Execute Phase 1 Reference Remediation

## Header
- **Session ID (S)**: 2026-05-10-006
- **Work Context (W)**: task38-phase1-reference-remediation
- **Handler Target (H)**: .taskmaster/tasks/task_038.txt
- **Task IDs**: 38
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/, .taskmaster/tasks/task_038.txt, scripts/template-ssot-scanner/apply_reference_fixes.py, scripts/template-ssot-scanner/generate_fixes.py, templates/registry/compatibility-map.json, templates/engine/verify-phase1.sh
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile Phase 1 reference remediation expectations against the current portable foundation state and identify only actionable gaps | docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/designs/phase1-reference-remediation-scope.md | completed |
| plan-step-implement | Run dry-run reference remediation and implement only proven current-state gaps in priority order: engine, patterns, remaining references | scripts/template-ssot-scanner/apply_reference_fixes.py; scripts/template-ssot-scanner/generate_fixes.py; docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store dry-run, scanner, guard, rollback, Taskmaster health, and regression evidence; refresh handoff docs and Taskmaster status | docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/reports/phase1-reference-remediation/; docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260510-task38-phase1-reference-remediation-ACTIVE/`
- `.taskmaster/tasks/task_038.txt`
- `scripts/template-ssot-scanner/apply_reference_fixes.py`
- `scripts/template-ssot-scanner/generate_fixes.py`
- `templates/registry/compatibility-map.json`
- `templates/engine/verify-phase1.sh`
- `tests/`
- Taskmaster Task `38`

## Branch Policy
- Working branch: `feat/task-38-phase1-reference-remediation`

## Amendments & Versioning
- 2026-05-10 - Task 38 kickoff created via the guided wizard flow.
- 2026-05-10 - Corrected the generated plan from generic wizard wording to the actual Phase 1 reference remediation scope before implementation.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 38 and its subtasks.
  3. Review the scope reconciliation artifact before changing reference remediation behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: avoid executing stale old-project reference fixes literally; prove each remediation against current scanner output first.

## Conflict & Scope Declaration
- Related plans: Task 7 baseline scanner outputs, Task 10 reference fix scripts, Task 13 compatibility mapping table, Task 19 rollback mechanism, Task 23 migration rehearsal environment, Task 25 Phase 0 scanner validation.
- Guard cross-check: reference remediation must preserve current portable foundation behavior and pass guard/scanner validation.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored dry-run, scanner, rollback, test, guard, and Taskmaster health evidence once remediation scope is proven

## Emergency Bypass Protocol
- No bypass authorized.
