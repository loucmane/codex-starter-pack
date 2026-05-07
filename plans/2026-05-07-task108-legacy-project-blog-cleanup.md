---
session_id: 2026-05-07-011
work_context: task108-legacy-project-blog-cleanup
handler_target: .taskmaster/tasks/task_108.md
task_ids: [108]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/
  - .taskmaster/tasks/task_108.md
  - templates/PROJECT-BLOG.md
  - scripts/template-ssot-scanner/security_validator.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 108 Clean Legacy PROJECT-BLOG Security Finding

## Header
- **Session ID (S)**: 2026-05-07-011
- **Work Context (W)**: task108-legacy-project-blog-cleanup
- **Handler Target (H)**: .taskmaster/tasks/task_108.md
- **Task IDs**: 108
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/, .taskmaster/tasks/task_108.md, templates/PROJECT-BLOG.md, scripts/template-ssot-scanner/security_validator.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile legacy PROJECT-BLOG.md content against the Task 18 security report and portable foundation scope | docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/designs/legacy-project-blog-scope-reconciliation.md | completed |
| plan-step-implement | Remove legacy PROJECT-BLOG.md from the portable template set and update its small live reference surface | templates/metadata/template-overview.md; templates/tools/index.md; docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/reports/legacy-project-blog-cleanup/security-validation-2026-05-07.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/reports/legacy-project-blog-cleanup/guard-2026-05-07.txt; docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/reports/legacy-project-blog-cleanup/taskmaster-health-2026-05-07.txt; docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/`
- `.taskmaster/tasks/task_108.md`
- `templates/PROJECT-BLOG.md`
- `templates/shared/tools/tool-selection-matrix.md`
- `templates/tools/index.md`
- `templates/metadata/template-overview.md`
- `templates/metadata/template-summary.csv`
- `templates/metadata/template-inventory.txt`
- `scripts/template-ssot-scanner/migration_detector.py`
- `scripts/template-ssot-scanner/safe_reorganize.py`
- `tests/`
- Taskmaster Task `108`

## Branch Policy
- Working branch: `feat/task-108-legacy-project-blog-cleanup`

## Amendments & Versioning
- 2026-05-07 - Task 108 kickoff created via the guided wizard flow.
- 2026-05-07 - Scope corrected from wizard placeholder wording to legacy PROJECT-BLOG cleanup.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 108 and its subtasks.
  3. Review the legacy PROJECT-BLOG scope reconciliation before changing template content.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: none for Task 108; final verification confirms the baseline is clean without weakening `security_validator.py`.

## Conflict & Scope Declaration
- Related plans: Task 18 security validator, Task 1 codebase analysis, Task 87 legacy monolith replacement.
- Guard cross-check: no scanner rules or allowlists should be weakened for this cleanup.

## Evidence Checklist
- Scope reconciliation under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored security report, scanner tests, guard, audit, diff-check, and Taskmaster health evidence

## Emergency Bypass Protocol
- No bypass authorized.
