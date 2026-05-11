---
session_id: 2026-05-11-002
work_context: task32-documentation-suite
handler_target: .taskmaster/tasks/task_032.txt
task_ids: [32]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/
  - .taskmaster/tasks/task_032.txt
  - .taskmaster/tasks/task_032.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 32 Create Documentation Suite

## Header
- **Session ID (S)**: 2026-05-11-002
- **Work Context (W)**: task32-documentation-suite
- **Handler Target (H)**: .taskmaster/tasks/task_032.txt
- **Task IDs**: 32
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/, .taskmaster/tasks/task_032.txt, .taskmaster/tasks/task_032.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical documentation-suite wording against the current portable foundation and identify the proven current gap | docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/designs/documentation-suite-scope-reconciliation.md | completed |
| plan-step-implement | Modernize the user-facing documentation entrypoints and fix malformed documentation hub links | CODEX.md; templates/USER-GUIDE.md; templates/guides/index.md; templates/guides/quickstart/getting-started.md; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/reports/documentation-suite/markdown-link-check-2026-05-11.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/reports/documentation-suite/plan-sync-2026-05-11.txt; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/reports/documentation-suite/work-tracking-audit-2026-05-11.txt; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/reports/documentation-suite/guard-2026-05-11.txt; docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/reports/documentation-suite/diff-check-2026-05-11.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/`
- `.taskmaster/tasks/task_032.txt`
- `CODEX.md`
- `templates/USER-GUIDE.md`
- `templates/guides/index.md`
- `templates/guides/quickstart/getting-started.md`
- Taskmaster Task `32`

## Branch Policy
- Working branch: `feat/task-32-documentation-suite`

## Amendments & Versioning
- 2026-05-11 - Task 32 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 32 and its subtasks.
  3. Review the documentation-suite scope reconciliation before changing documentation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the documentation update focused on the proven user-facing entrypoint gap rather than broad legacy wording churn.

## Conflict & Scope Declaration
- Related plans: Task 1 codebase analysis, Task 4 backlog alignment, Tasks 99-102 portable foundation work, Task 107 direct Git execution mode.
- Guard cross-check: documentation changes must preserve plan/tracker/session compliance and current direct-Git guidance.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored markdown-link, guard, audit, plan-sync, and diff-check evidence once documentation updates land

## Emergency Bypass Protocol
- No bypass authorized.
