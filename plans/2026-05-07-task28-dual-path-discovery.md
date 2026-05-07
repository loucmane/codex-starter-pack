---
session_id: 2026-05-07-009
work_context: task28-dual-path-discovery
handler_target: .taskmaster/tasks/task_028.txt
task_ids: [28]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/
  - .taskmaster/tasks/task_028.txt
  - .taskmaster/tasks/task_028.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 28 Dual-Path Discovery

## Header
- **Session ID (S)**: 2026-05-07-009
- **Work Context (W)**: task28-dual-path-discovery
- **Handler Target (H)**: .taskmaster/tasks/task_028.txt
- **Task IDs**: 28
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/, .taskmaster/tasks/task_028.txt, .taskmaster/tasks/task_028.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Reconcile historical dual-path discovery wording against the current registry, compatibility map, and portable foundation | docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/designs/dual-path-discovery-scope-reconciliation.md | completed |
| plan-step-implement | Extend the existing TemplateRegistry discovery chain with structured traces, usage metrics, cache warming, and deterministic miss suggestions | scripts/template_registry.py; tests/meta_workflow_guard/test_template_registry.py; docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store focused test/guard/audit evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/reports/dual-path-discovery/; docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260507-task28-dual-path-discovery-ACTIVE/`
- `.taskmaster/tasks/task_028.txt`
- `scripts/template_registry.py`
- `tests/meta_workflow_guard/test_template_registry.py`
- `tests/`
- Taskmaster Task `28`

## Branch Policy
- Working branch: `feat/task-28-dual-path-discovery`

## Amendments & Versioning
- 2026-05-07 - Task 28 kickoff created via the guided wizard flow.
- 2026-05-07 - Corrected the generic kickoff plan to the actual current-state dual-path discovery scope after reading Task 8, Task 13, Task 1, Task 4, and portable-foundation evidence.
- 2026-05-07 - Implemented registry discovery traces, in-memory path metrics, cache warming, and deterministic miss suggestions with focused registry tests.
- 2026-05-07 - Marked Taskmaster Task 28 and subtasks 28.1/28.2 done after pre-close verification passed.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 28 and its subtasks.
  3. Review the dual-path discovery scope reconciliation before changing registry behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: after PR merge, archive this Task 28 work-tracking folder from `main` and capture post-archive guard/audit evidence.

## Conflict & Scope Declaration
- Related plans: Task 8 template registry system, Task 13 compatibility mapping table, Task 21 frontmatter schema, Tasks 99-102 portable foundation.
- Guard cross-check: discovery behavior must preserve configured roots from `.codex/config.toml` and avoid hardcoded repo-only path assumptions.

## Evidence Checklist
- Dual-path discovery scope reconciliation under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored focused registry test evidence under `reports/dual-path-discovery/`
- Final guard/audit/diff-check evidence

## Emergency Bypass Protocol
- No bypass authorized.
