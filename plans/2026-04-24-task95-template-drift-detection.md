---
session_id: 2026-04-24-002
work_context: task95-template-drift-detection
handler_target: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-drift-detection-draft.md
task_ids: [95]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/
  - docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-drift-detection-draft.md
  - scripts/codex-guard
  - tests/meta_workflow_guard
  - .taskmaster/tasks/task_095.txt
plan_version: v1
emergency_bypass: false
---

# Plan - Task 95 Template Drift Detection

## Header
- **Session ID (S)**: 2026-04-24-002
- **Work Context (W)**: task95-template-drift-detection
- **Handler Target (H)**: docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-drift-detection-draft.md
- **Task IDs**: 95
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/, docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-drift-detection-draft.md, scripts/codex-guard, tests/meta_workflow_guard, .taskmaster/tasks/task_095.txt
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Finalize the drift-detection design, target mappings, and report contract against the current guard architecture | docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/designs/template-drift-design.md | completed |
| plan-step-implement | Add the drift-check command, reporting outputs, and automation docs with focused regression coverage | scripts/codex-guard; tests/meta_workflow_guard; reports/template-drift/ | completed |
| plan-step-verify | Store task evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/`
- `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/template-drift-detection-draft.md`
- `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/designs/enforcement-framework-draft.md`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/`
- `reports/template-drift/`
- Taskmaster Task `95`

## Branch Policy
- Working branch: `feat/task-95-template-drift-detection`

## Amendments & Versioning
- 2026-04-24 - Task 95 kickoff after Task 94 merge and archive.
- 2026-04-24 - Scope baseline defined: implement drift detection as a `codex-guard` subcommand with text and JSON report outputs plus repo-level stored reports.
- 2026-04-24 - Implementation completed: drift-check command, repo-level reports, focused tests, and CI automation are in place; final verification and closeout evidence remain.
- 2026-04-24 - Verification completed: drift-check strict pass, pytest pass, plan sync pass, guard pass, and Taskmaster shows Task 95 plus subtasks 95.1-95.5 as done.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 95 and subtasks `95.1` through `95.5`.
  3. Re-read the archived drift-detection draft and the current `scripts/codex-guard` command structure before implementation.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the first implementation focused on deterministic template/canonical-doc drift checks and avoid over-designing AST-level comparison before the report contract exists.

## Conflict & Scope Declaration
- Related plans: Task 94 enforcement sequencing, Tasks 96-97 follow-on operator/dashboard work.
- Guard cross-check: extend the existing guard tooling rather than creating a competing enforcement entrypoint.

## Evidence Checklist
- Task 95 design note under `designs/`
- Tracker/session entries for Task 95 kickoff, Taskmaster status, and design decisions
- Stored drift reports under `reports/template-drift/`
- Guard/test evidence once the drift-check command lands

## Emergency Bypass Protocol
- No bypass authorized.
