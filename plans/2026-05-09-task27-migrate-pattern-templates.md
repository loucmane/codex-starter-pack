---
session_id: 2026-05-09-003
work_context: task27-migrate-pattern-templates
handler_target: .taskmaster/tasks/task_027.txt
task_ids: [27]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/
  - .taskmaster/tasks/task_027.txt
  - templates/patterns/index.md
  - templates/metadata/template-metadata-policy.json
  - templates/registry/compatibility-map.json
plan_version: v1
emergency_bypass: false
---

# Plan - Task 27 Migrate Pattern Templates

## Header
- **Session ID (S)**: 2026-05-09-003
- **Work Context (W)**: task27-migrate-pattern-templates
- **Handler Target (H)**: .taskmaster/tasks/task_027.txt
- **Task IDs**: 27
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/, .taskmaster/tasks/task_027.txt, .taskmaster/tasks/task_027.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical Task 27 wording against the current portable pattern foundation | docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/designs/pattern-template-scope-reconciliation.md | completed |
| plan-step-implement | Add the missing modular pattern index, compatibility redirect, metadata policy coverage, and focused tests | templates/patterns/index.md; templates/registry/compatibility-map.json; templates/metadata/template-metadata-policy.json; tests/meta_workflow_guard/test_guard_rules.py; tests/meta_workflow_guard/test_template_registry.py | completed |
| plan-step-verify | Store focused test, registry, audit, and guard evidence; refresh handoff docs; confirm Taskmaster status | docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/reports/pattern-template-migration/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260509-task27-migrate-pattern-templates-ACTIVE/`
- `.taskmaster/tasks/task_027.txt`
- `templates/PATTERNS.md`
- `templates/patterns/index.md`
- `templates/registry/compatibility-map.json`
- `templates/registry/index.json`
- `templates/metadata/template-metadata-policy.json`
- `templates/metadata/template-inventory.txt`
- `templates/metadata/template-summary.csv`
- `templates/metadata/template-overview.md`
- `tests/`
- Taskmaster Task `27`

## Branch Policy
- Working branch: `feat/task-27-migrate-pattern-templates`

## Amendments & Versioning
- 2026-05-09 - Task 27 kickoff created via the guided wizard flow.
- 2026-05-09 - Reconciled historical pattern migration scope against the current portable foundation and narrowed implementation to concrete pattern discovery/enforcement gaps.
- 2026-05-09 - Implemented the pattern-family index, concrete legacy redirect, metadata-policy rule, and focused tests; verification evidence is being collected under the active report folder.
- 2026-05-09 - Completed verification with focused pytest, work-tracking audit, guard, Taskmaster health, and diff-check evidence.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 27 and its subtasks.
  3. Review the pattern-template scope reconciliation artifact before changing pattern or registry behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: create PR, merge, then archive the Task 27 work-tracking folder in a separate post-merge cleanup commit.

## Conflict & Scope Declaration
- Related plans: Tasks 8/13 registry and compatibility work, Task 21 template frontmatter schema, Task 25 Phase 0 scanner validation.
- Guard cross-check: pattern files are now governed by the metadata policy and must keep valid frontmatter.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff, scope, and implementation progress
- Stored focused test, audit, and guard evidence once verification lands

## Emergency Bypass Protocol
- No bypass authorized.
