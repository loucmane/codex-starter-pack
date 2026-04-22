---
session_id: 2026-04-21-002
work_context: task91-standardize-template-metadata
handler_target: templates/
task_ids: [91]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/
  - docs/ai/work-tracking/archive/20260421-task90-complete-engine-migration-COMPLETED/
  - templates/**/*.md
plan_version: v1
emergency_bypass: false
---

# Plan – Task 91 Standardize Template Metadata

## Header
- **Session ID (S)**: 2026-04-21-002
- **Work Context (W)**: task91-standardize-template-metadata
- **Handler Target (H)**: templates/
- **Task IDs**: 91
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/, docs/ai/work-tracking/archive/20260421-task90-complete-engine-migration-COMPLETED/, templates/**/*.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                        | Evidence                                                                                                      | Status    |
|---------------------|--------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|-----------|
| plan-step-scope     | Inventory metadata gaps and define the first-pass schema boundary  | docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md | completed |
| plan-step-implement | Batch-update target templates, extend the guard, and document changes | docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/IMPLEMENTATION.md          | completed |
| plan-step-verify    | Store evidence, validate guard/tests, and refresh handoff docs     | docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/reports/standardize-template-metadata/guard-2026-04-22-final.txt; docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/reports/standardize-template-metadata/tests-2026-04-22-guard.txt | completed |
| plan-step-emergency | _Optional_ – only if bypass required                               | Waiver + post-mortem plan                                                                                     | n/a       |

## Scope
- `docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/`
- `docs/ai/work-tracking/archive/20260421-task90-complete-engine-migration-COMPLETED/`
- `templates/**/*.md`
- `scripts/codex-guard`
- relevant metadata-alignment tests under `tests/`

## Branch Policy
- Working branch: `feat/task-91-standardize-template-metadata`

## Amendments & Versioning
- 2026-04-21 — Kickoff inventory established the initial scope: modular templates with partial/missing frontmatter need standardization, while aggregate docs and generated overviews may need a separate policy.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Review `designs/template-metadata-inventory.md` before changing any schema fields.
  2. Confirm which file classes are in-scope for canonical frontmatter enforcement.
  3. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: follow-on portability work should externalize more repo-structure assumptions, but Task 91’s metadata-enforcement rollout is complete for the current repo scope.

## Conflict & Scope Declaration
- Related plans: Task 90 engine migration reconciliation, Task 89 work-tracking enforcement, existing metadata alignment tests.
- Guard cross-check: keep early Task 91 edits focused on metadata inventory/schema definition before broad batch updates land.

## Evidence Checklist
- Inventory note under `designs/`
- Tracker/session entries for branch creation, archive/scaffold, and Taskmaster state
- Serena memory for Task 91 kickoff
- Guard/test evidence once implementation begins

## Emergency Bypass Protocol
- No bypass authorized.

## Completion
- Archive the Task 91 active folder when metadata rollout, guard extension, verification, and Taskmaster closeout are complete.
