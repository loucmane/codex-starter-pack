---
session_id: 2026-05-08-011
work_context: task22-template-discovery-api
handler_target: .taskmaster/tasks/task_022.txt
task_ids: [22]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/
  - .taskmaster/tasks/task_022.txt
  - scripts/template_registry.py
  - tests/meta_workflow_guard/test_template_registry.py
plan_version: v1
emergency_bypass: false
---

# Plan - Task 22 Build Template Discovery API

## Header
- **Session ID (S)**: 2026-05-08-011
- **Work Context (W)**: task22-template-discovery-api
- **Handler Target (H)**: .taskmaster/tasks/task_022.txt
- **Task IDs**: 22
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/, .taskmaster/tasks/task_022.txt, scripts/template_registry.py, tests/meta_workflow_guard/test_template_registry.py
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical REST, Redis, and GraphQL wording against the current portable template registry | docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/designs/template-discovery-api-scope-reconciliation.md | completed |
| plan-step-implement | Implement the smallest proven in-process discovery API facade with focused registry tests | scripts/template_registry.py; tests/meta_workflow_guard/test_template_registry.py; docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/reports/template-discovery-api/tests-2026-05-08-template-registry.txt | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/reports/template-discovery-api/tests-2026-05-08-full.txt; docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/reports/template-discovery-api/work-tracking-audit-2026-05-08.txt; docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/reports/template-discovery-api/guard-2026-05-08.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260508-task22-template-discovery-api-ACTIVE/`
- `.taskmaster/tasks/task_022.txt`
- `scripts/template_registry.py`
- `tests/meta_workflow_guard/test_template_registry.py`
- `tests/`
- Taskmaster Task `22`

## Branch Policy
- Working branch: `feat/task-22-template-discovery-api`

## Amendments & Versioning
- 2026-05-08 - Task 22 kickoff created via the guided wizard flow.
- 2026-05-08 - Scope reconciled against current portable foundation; REST, Redis, and GraphQL service work excluded from this task.
- 2026-05-08 - Implemented `TemplateDiscoveryAPI` over `TemplateRegistry` with focused registry tests passing.
- 2026-05-08 - Verification evidence captured for full pytest, plan sync, work-tracking audit, guard, and diff-check.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 22 and its subtasks.
  3. Review the scope reconciliation artifact before changing registry behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the discovery API grounded in the existing `TemplateRegistry` instead of creating a parallel service runtime.

## Conflict & Scope Declaration
- Related plans: Task 8 template registry/discovery system, Task 21 frontmatter schema, Task 61 discovery optimization.
- Guard cross-check: registry API changes must preserve portable repo-structure behavior and current template metadata enforcement.

## Evidence Checklist
- Scope reconciliation note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the discovery API facade lands

## Emergency Bypass Protocol
- No bypass authorized.
