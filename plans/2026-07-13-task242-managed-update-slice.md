---
session_id: 2026-07-13-004
work_context: task242-managed-update-slice
handler_target: .taskmaster/tasks/task_242.md
task_ids: [242]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/
  - .taskmaster/tasks/task_242.md
  - aegis_foundation/managed_update.py
  - tests/fixtures/aegis/managed-update-golden-plans.json
plan_version: v1
emergency_bypass: false
---

# Plan - Task 242 Extract The Managed-Update Slice From The Aegis Installer

## Header
- **Session ID (S)**: 2026-07-13-004
- **Work Context (W)**: task242-managed-update-slice
- **Handler Target (H)**: .taskmaster/tasks/task_242.md
- **Task IDs**: 242
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/, .taskmaster/tasks/task_242.md, aegis_foundation/managed_update.py, tests/fixtures/aegis/managed-update-golden-plans.json
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the managed-update extraction seam, compatibility adapters, safety invariants, and rollback boundary | docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/designs/managed-update-extraction.md | completed |
| plan-step-implement | Extract the authoritative core, preserve installer adapters/mirrors, and add Codex/HP-Fetcher/Blog golden plans | aegis_foundation/managed_update.py; tests/meta_workflow_guard/test_aegis_managed_update.py | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/reports/managed-update-slice/task-verification.md; docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/HANDOFF.md; docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/`
- `.taskmaster/tasks/task_242.md`
- `aegis_foundation/managed_update.py`
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `tests/fixtures/aegis/managed-update-golden-plans.json`
- `tests/meta_workflow_guard/test_aegis_managed_update.py`
- Taskmaster Task `242`

## Branch Policy
- Working branch: `feat/task-242-managed-update-slice`

## Amendments & Versioning
- 2026-07-13 - Task 242 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 242 and its subtasks.
  3. Review the managed-update extraction design and golden consumer fixture before changing installer behavior.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: require fresh exact-head hosted CI from a checkout outside `/tmp`, then deliver the stacked Task 242 PR after Task 240 without weakening fail-closed update classification.

## Conflict & Scope Declaration
- Related plans: Tasks 235, 237, 238, and 240 are completed prerequisites; Task 243 consumes this evidence.
- Guard cross-check: extraction must preserve source/package parity, installed-target bytes, and Task 242 lifecycle evidence.

## Evidence Checklist
- Managed-update extraction design under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Golden Codex/HP-Fetcher/Blog plans plus source/package and full-suite evidence
- Explicit baseline comparison for the unchanged `/tmp`-location reconcile assertion

## Emergency Bypass Protocol
- No bypass authorized.
