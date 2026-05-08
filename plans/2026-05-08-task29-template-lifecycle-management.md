---
session_id: 2026-05-08-008
work_context: task29-template-lifecycle-management
handler_target: .taskmaster/tasks/task_029.txt
task_ids: [29]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/
  - .taskmaster/tasks/task_029.txt
  - templates/metadata/template-lifecycle-policy.json
  - scripts/template_lifecycle.py
  - tests/meta_workflow_guard/test_template_lifecycle.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 29 Create Template Lifecycle Management

## Header
- **Session ID (S)**: 2026-05-08-008
- **Work Context (W)**: task29-template-lifecycle-management
- **Handler Target (H)**: .taskmaster/tasks/task_029.txt
- **Task IDs**: 29
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/, .taskmaster/tasks/task_029.txt, templates/metadata/template-lifecycle-policy.json, scripts/template_lifecycle.py, tests/meta_workflow_guard/test_template_lifecycle.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical lifecycle wording against current template metadata, registry, and portable foundation systems | docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/designs/template-lifecycle-scope-reconciliation.md | completed |
| plan-step-implement | Add lifecycle policy, audit helper, schema fields, and regression tests for the proven current-state gap | templates/metadata/template-lifecycle-policy.json; scripts/template_lifecycle.py; tests/meta_workflow_guard/test_template_lifecycle.py; docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/reports/template-lifecycle-management/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task29-template-lifecycle-management-ACTIVE/`
- `.taskmaster/tasks/task_029.txt`
- `templates/metadata/template-frontmatter.schema.json`
- `templates/metadata/template-lifecycle-policy.json`
- `scripts/template_lifecycle.py`
- `tests/`
- Taskmaster Task `29`

## Branch Policy
- Working branch: `feat/task-29-template-lifecycle-management`

## Amendments & Versioning
- 2026-05-08 - Task 29 kickoff created via the guided wizard flow.
- 2026-05-08 - Corrected plan scope from generic wizard wording to template lifecycle management after evidence review.
- 2026-05-08 - Added lifecycle policy, audit helper, schema lifecycle fields, deprecated tombstone metadata, and lifecycle regression tests.
- 2026-05-08 - Stored lifecycle, registry/guard, full pytest, lifecycle audit, Taskmaster health, plan sync, work-tracking audit, guard, diff-check, and Serena evidence; Taskmaster Task 29 is done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 29 and its subtasks.
  3. Review the lifecycle scope reconciliation artifact before changing template lifecycle behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: PR checks still need to pass before merge; keep lifecycle behavior audit-only unless a later task explicitly authorizes file archival or bulk metadata migration.

## Conflict & Scope Declaration
- Related plans: Task 8 template registry, Task 21 frontmatter schema, Task 58 robust versioning, Task 91 metadata policy, Task 99 portable foundation.
- Guard cross-check: lifecycle policy must preserve existing governed template metadata and avoid invalidating compatibility statuses without a migration plan.

## Evidence Checklist
- Lifecycle scope note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored focused lifecycle, registry/metadata guard, lifecycle audit, full pytest, Taskmaster health, plan-sync, work-tracking audit, guard, and diff-check evidence under `reports/template-lifecycle-management/`
- Serena memory: `.serena/memories/2026-05-08_task29_template_lifecycle_management.md`

## Emergency Bypass Protocol
- No bypass authorized.
