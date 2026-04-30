---
session_id: 2026-04-26-001
work_context: task3-port-ssot-scanner-suite
handler_target: .taskmaster/tasks/task_003.txt
task_ids: [3]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/
  - .taskmaster/tasks/task_003.txt
  - scripts/template-ssot-scanner/
  - tests/
plan_version: v1
emergency_bypass: false
---

# Plan - Task 3 Port SSOT Scanner Suite to Codex

## Header
- **Session ID (S)**: 2026-04-26-001
- **Work Context (W)**: task3-port-ssot-scanner-suite
- **Handler Target (H)**: .taskmaster/tasks/task_003.txt
- **Task IDs**: 3
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/, .taskmaster/tasks/task_003.txt, scripts/template-ssot-scanner/, tests/
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define scanner foundation reconciliation scope and stale-baseline safety rules | docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/designs/scanner-suite-reconciliation.md | completed |
| plan-step-implement | Audit current scanner suite in the full Codex foundation context and apply only proven remaining gaps | scripts/template-ssot-scanner/; docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/reports/ssot-scanner-suite/scanner-foundation-audit.md | completed |
| plan-step-verify | Store scanner/test/guard evidence and confirm Taskmaster status | docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/reports/ssot-scanner-suite/; docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260426-task3-port-ssot-scanner-suite-ACTIVE/`
- `.taskmaster/tasks/task_003.txt`
- `scripts/template-ssot-scanner/`
- `tests/`
- Taskmaster Task `3`

## Branch Policy
- Working branch: `feat/task-3-port-ssot-scanner-suite`

## Amendments & Versioning
- 2026-04-26 - Task 3 kickoff created via the guided wizard flow.
- 2026-04-26 - Corrected kickoff scope to scanner-suite foundation reconciliation and completed the scope gate before scanner work.
- 2026-04-26 - Completed scanner audit and implementation hardening across Taskmaster subtasks 3.1-3.8; verification remains pending.
- 2026-04-26 - Completed verification with plan sync, guard, work-tracking audit, scanner runner, coverage, performance, and combined tests.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 3 and its subtasks.
  3. Review the scanner reconciliation artifact before changing scanner code.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: prepare commit/PR handoff.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Scanner foundation reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored scanner audit, test, and guard evidence once the implementation boundary is known

## Emergency Bypass Protocol
- No bypass authorized.
