---
session_id: 2025-10-27-001
work_context: task89-work-tracking
handler_target: templates/workflows/taskmaster/
task_ids: [89]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/
  - reports/work-tracking-enforcement/*
plan_version: v1
emergency_bypass: false
---

# Plan – Task 89 Work-Tracking Workflow Enforcement

## Header
- **Session ID (S)**: 2025-10-27-001
- **Work Context (W)**: task89-work-tracking
- **Handler Target (H)**: templates/workflows/taskmaster/
- **Task IDs**: 89
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/, reports/work-tracking-enforcement/*
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                               | Evidence                                                                                                   | Status     |
|---------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|------------|
| plan-step-scope     | Define work-tracking enforcement requirements and affected artifacts      | docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/designs/work-tracking-enforcement-scope.md | completed  |
| plan-step-implement | Author workflow/guard/helper updates and document enforcement procedures   | docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/IMPLEMENTATION.md; templates/workflows/taskmaster/work-tracking-enforcement.md; scripts/codex-guard; scripts/codex-task | completed |
| plan-step-verify    | Record guard/tests evidence and update Taskmaster + work-tracking records | docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/reports/work-tracking-enforcement/guard-2025-10-27-baseline.txt | pending    |
| plan-step-emergency | _Optional_ – only if bypass required                                       | Waiver + post-mortem plan                                                                                  | n/a        |

## Scope
- `docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/`
- `docs/ai/work-tracking/archive/20251021-task88-taskmaster-alignment-COMPLETED/`
- `templates/workflows/taskmaster/*`
- `scripts/codex-guard`
- `scripts/codex-task`
- `reports/work-tracking-enforcement/*`

## Branch Policy
- Working branch: `feat/task-89-work-tracking-enforcement`

## Amendments & Versioning
- _None yet_

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Review Task 88 archive tracker for enforcement patterns.
  2. Run `python3 scripts/codex-task plan sync` after tracker updates.
  3. Use `codex-task work-tracking audit` at session start to highlight stale folders.
- Outstanding risks/todos: define guard expectations for multi-day active folders and enforce Serena memory usage.

## Conflict & Scope Declaration
- Related plans: Task 88 alignment (reference for enforcement baseline).
- Guard cross-check: ensure `git diff --name-only` stays within scoped templates/scripts/work-tracking folders.

## Evidence Checklist
- Guard logs under `reports/work-tracking-enforcement/`
- Pytest outputs for enforcement guard tests
- Tracker/session entries summarizing workflow updates

## Emergency Bypass Protocol
- No bypass authorized.

## Completion
- Archive plan and active folder when enforcement workflow + guard helpers are implemented, documented, and verified.
