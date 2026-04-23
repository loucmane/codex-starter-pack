---
session_id: 2026-04-22-002
work_context: task92-expand-workflow-guard-coverage
handler_target: scripts/codex-guard
task_ids: [92]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/
  - docs/ai/work-tracking/archive/20260421-task91-standardize-template-metadata-COMPLETED/
  - scripts/codex-guard
  - tests/meta_workflow_guard/
plan_version: v1
emergency_bypass: false
---

# Plan – Task 92 Expand Workflow Guard Coverage

## Header
- **Session ID (S)**: 2026-04-22-002
- **Work Context (W)**: task92-expand-workflow-guard-coverage
- **Handler Target (H)**: scripts/codex-guard
- **Task IDs**: 92
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/, docs/ai/work-tracking/archive/20260421-task91-standardize-template-metadata-COMPLETED/, scripts/codex-guard, tests/meta_workflow_guard/
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                      | Evidence                                                                                              | Status    |
|---------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| plan-step-scope     | Audit current guard coverage and compare it to the Task 91 roadmap | docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/designs/guard-coverage-audit.md | completed |
| plan-step-implement | Implement prioritized guard additions, docs updates, and helper alignment | docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify    | Store evidence, rerun validations/tests, and refresh handoff docs | docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ – only if bypass required                             | Waiver + post-mortem plan                                                                             | n/a       |

## Scope
- `docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/`
- `docs/ai/work-tracking/archive/20260421-task91-standardize-template-metadata-COMPLETED/`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/`
- relevant workflow/template docs touched by new guard coverage

## Branch Policy
- Working branch: `feat/task-92-expand-workflow-guard-coverage`

## Amendments & Versioning
- 2026-04-22 — Kickoff scope starts with a guard-gap audit plus explicit backlog capture for the broader portability roadmap exposed by Task 91.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Review the archived Task 91 portability roadmap before changing guard scope.
  2. Audit current `scripts/codex-guard` coverage against workflow expectations and missing enforcement points.
  3. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: distinguish repo-specific guard gaps from broader cross-project foundation work so Task 92 stays focused while the new follow-on tasks capture the portability agenda.

## Conflict & Scope Declaration
- Related plans: Task 91 metadata standardization, Task 89 work-tracking enforcement, Task 88 Taskmaster alignment.
- Guard cross-check: keep initial Task 92 changes focused on audit, session/work-tracking setup, and backlog alignment before broader enforcement edits land.

## Evidence Checklist
- Guard coverage audit note under `designs/`
- Tracker/session entries for branch creation, archive/scaffold, and Taskmaster state
- Serena memory for Task 92 kickoff
- Stored guard/test evidence once implementation begins

## Emergency Bypass Protocol
- No bypass authorized.

## Completion
- 2026-04-23 — Task 92 guard additions, documentation, regression evidence, and Taskmaster closeout completed. Archive the active folder after merge/PR lifecycle is complete.
