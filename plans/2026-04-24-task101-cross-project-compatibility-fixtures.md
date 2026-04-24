---
session_id: 2026-04-24-008
work_context: task101-cross-project-compatibility-fixtures
handler_target: templates/engine/core/portable-foundation-spec.md
task_ids: [101]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/
  - templates/engine/core/portable-foundation-spec.md
  - .taskmaster/tasks/task_101.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 101 Add Cross-Project Compatibility Fixtures

## Header
- **Session ID (S)**: 2026-04-24-008
- **Work Context (W)**: task101-cross-project-compatibility-fixtures
- **Handler Target (H)**: templates/engine/core/portable-foundation-spec.md
- **Task IDs**: 101
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/, templates/engine/core/portable-foundation-spec.md, .taskmaster/tasks/task_101.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Define the cross-project fixture matrix, validation boundaries, and repo-shape assumptions to test | docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/designs/cross-project-fixture-matrix.md | completed |
| plan-step-implement | Add repo-shape fixtures and verification coverage for bootstrap, guard, and path-resolution behavior | tests/; scripts/codex-task; scripts/codex-guard; docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task101-cross-project-compatibility-fixtures-ACTIVE/`
- `templates/engine/core/portable-foundation-spec.md`
- `docs/ai/work-tracking/archive/20260424-task100-foundation-bootstrap-layer-COMPLETED/`
- `scripts/_repo_structure.py`
- `tests/meta_workflow_guard/`
- `.taskmaster/tasks/task_101.txt`
- `scripts/codex-task`
- `scripts/codex-guard`
- `scripts/template-metrics-dashboard`
- Taskmaster Task `101`

## Branch Policy
- Working branch: `feat/task-101-cross-project-compatibility-fixtures`

## Amendments & Versioning
- 2026-04-24 - Task 101 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 101 status and the Task 100 bootstrap handoff.
  3. Review the fixture matrix before adding or changing any repo-shape tests.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the fixture suite config-driven and avoid writing tests that silently assume this repo's default layout.

## Conflict & Scope Declaration
- Related plans: Task 98 repo-structure externalization, Task 99 portable foundation spec, Task 100 bootstrap layer, Task 102 migration/adoption docs.
- Guard cross-check: compatibility fixtures must prove the portable foundation against alternate roots and template scopes instead of revalidating only this repo.

## Evidence Checklist
- Fixture matrix note under `designs/`
- Tracker/session entries for kickoff, fixture selection, and implementation progress
- Stored test and guard evidence showing alternate repo-shape coverage

## Emergency Bypass Protocol
- No bypass authorized.
