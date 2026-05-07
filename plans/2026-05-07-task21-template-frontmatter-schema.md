---
session_id: 2026-05-07-008
work_context: task21-template-frontmatter-schema
handler_target: .taskmaster/tasks/task_021.txt
task_ids: [21]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/
  - .taskmaster/tasks/task_021.txt
  - .taskmaster/tasks/task_021.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 21 Template Frontmatter Schema

## Header
- **Session ID (S)**: 2026-05-07-008
- **Work Context (W)**: task21-template-frontmatter-schema
- **Handler Target (H)**: .taskmaster/tasks/task_021.txt
- **Task IDs**: 21
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/, .taskmaster/tasks/task_021.txt, .taskmaster/tasks/task_021.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical frontmatter-schema wording against the current Task 91 metadata policy and portable foundation | docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/designs/frontmatter-schema-scope-reconciliation.md | completed |
| plan-step-implement | Implement schema-backed, typed frontmatter validation through the existing metadata policy and guard path | scripts/codex-guard; templates/metadata/template-frontmatter.schema.json; docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/reports/template-frontmatter-schema/schema-validation-2026-05-07.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/reports/template-frontmatter-schema/final-verification-2026-05-07.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task21-template-frontmatter-schema-ACTIVE/`
- `.taskmaster/tasks/task_021.txt`
- `.taskmaster/tasks/task_021.txt`
- `scripts/codex-guard`
- `templates/metadata/template-frontmatter.schema.json`
- `templates/metadata/template-metadata-policy.json`
- `tests/`
- Taskmaster Task `21`

## Branch Policy
- Working branch: `feat/task-21-template-frontmatter-schema`

## Amendments & Versioning
- 2026-05-07 - Task 21 kickoff created via the guided wizard flow.
- 2026-05-07 - Scope corrected from generic wizard wording to schema-backed template metadata validation.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 21 and its subtasks.
  3. Review the frontmatter schema scope artifact before changing metadata enforcement.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep metadata enforcement policy-driven and avoid rewriting template families outside the scoped schema/guard gap.

## Conflict & Scope Declaration
- Related plans: Task 91 metadata standardization, Task 95 template drift detection, Task 99 portable foundation specification.
- Guard cross-check: schema validation must preserve the repo-local policy contract and cross-project template-root support.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
