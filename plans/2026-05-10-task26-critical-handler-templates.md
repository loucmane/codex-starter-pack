---
session_id: 2026-05-10-004
work_context: task26-critical-handler-templates
handler_target: .taskmaster/tasks/task_026.txt
task_ids: [26]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/
  - .taskmaster/tasks/task_026.txt
  - .taskmaster/tasks/task_026.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 26 Migrate Critical Handler Templates

## Header
- **Session ID (S)**: 2026-05-10-004
- **Work Context (W)**: task26-critical-handler-templates
- **Handler Target (H)**: .taskmaster/tasks/task_026.txt
- **Task IDs**: 26
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/, .taskmaster/tasks/task_026.txt, .taskmaster/tasks/task_026.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical critical-handler migration wording against the current modular handler registry | docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/designs/critical-handler-templates-scope-reconciliation.md | completed |
| plan-step-implement | Implement the proven current-state gap: concrete handler-family index, registry alias resolution, compatibility redirect, and routing cleanup | scripts/template_registry.py; templates/handlers/index.md; templates/registry/index.json; templates/registry/compatibility-map.json; templates/matrices/mapping/keyword-to-handler.md; tests/meta_workflow_guard/test_template_registry.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/TRACKER.md; docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/reports/critical-handler-templates/ | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/`
- `.taskmaster/tasks/task_026.txt`
- `.taskmaster/tasks/task_026.txt`
- `scripts/template_registry.py`
- `templates/handlers/`
- `templates/registry/`
- `templates/matrices/mapping/keyword-to-handler.md`
- `tests/`
- Taskmaster Task `26`

## Branch Policy
- Working branch: `feat/task-26-critical-handler-templates`

## Amendments & Versioning
- 2026-05-10 - Task 26 kickoff created via the guided wizard flow.
- 2026-05-10 - Scope reconciliation completed; implementation narrowed to registry/discovery compatibility for already-modular critical handlers.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 26 and its subtasks.
  3. Review `docs/ai/work-tracking/active/20260510-task26-critical-handler-templates-ACTIVE/designs/critical-handler-templates-scope-reconciliation.md` before changing registry or handler behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the fix bounded to proven handler discovery/compatibility gaps rather than remigrating handler content.

## Conflict & Scope Declaration
- Related plans: Task 27 pattern-family compatibility redirect, Task 91 metadata policy, Task 8 registry foundation.
- Guard cross-check: handler edits must preserve template metadata compliance and registry compatibility behavior.

## Evidence Checklist
- Critical handler scope reconciliation under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the registry/handler compatibility implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
