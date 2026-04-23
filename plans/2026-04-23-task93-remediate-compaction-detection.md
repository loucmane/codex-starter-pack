---
session_id: 2026-04-23-002
work_context: task93-remediate-compaction-detection
handler_target: templates/behaviors/session/compaction-detection.md
task_ids: [93]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/
  - templates/behaviors/session/compaction-detection.md
  - templates/workflows/session/compaction.md
  - templates/handlers/triggers/session/prepare-compaction.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 93 Remediate Compaction Detection Behavior

## Header
- **Session ID (S)**: 2026-04-23-002
- **Work Context (W)**: task93-remediate-compaction-detection
- **Handler Target (H)**: templates/behaviors/session/compaction-detection.md
- **Task IDs**: 93
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/, templates/behaviors/session/compaction-detection.md, templates/workflows/session/compaction.md, templates/handlers/triggers/session/prepare-compaction.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description                                                      | Evidence                                                                                              | Status    |
|---------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| plan-step-scope     | Evaluate current compaction behavior, templates, and failure modes | docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/designs/compaction-behavior-audit.md | completed |
| plan-step-implement | Rewrite or retire stale compaction detection behavior and update docs | docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify    | Store regression evidence, guard output, and final handoff state | docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required                             | Waiver + post-mortem plan                                                                             | n/a       |

## Scope
- `docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/`
- `templates/behaviors/session/compaction-detection.md`
- `templates/behaviors/session/compaction-preparation.md`
- `templates/workflows/session/compaction.md`
- `templates/handlers/triggers/session/prepare-compaction.md`
- relevant guard/tests only if the compaction behavior requires enforceable validation

## Branch Policy
- Working branch: `feat/task-93-remediate-compaction-detection`

## Amendments & Versioning
- 2026-04-23 - Kickoff after Task 92 merge. Start by auditing the compaction templates and documented handoff flow before changing behavior.
- 2026-04-23 - Scope audit completed. Decision: retire deprecated `compaction-detection.md` as executable behavior and update aggregate/guard references accordingly.
- 2026-04-23 - Implementation and verification completed: deprecated compaction guidance retired, aggregate docs split, guard canonical docs updated, and focused regression/guard evidence captured.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 93 and subtasks `93.1` through `93.5`.
  3. Inspect the compaction behavior/template files before editing them.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: avoid another template-only patch that leaves behavior ambiguous; the scope decision must state whether stale compaction detection is rewritten or retired.

## Conflict & Scope Declaration
- Related plans: Task 92 workflow guard coverage, Task 89 work-tracking enforcement, Task 85 session continuation.
- Guard cross-check: keep initial Task 93 changes focused on audit, session/work-tracking setup, and behavior decision before implementation edits land.

## Evidence Checklist
- Compaction behavior audit note under `designs/`
- Tracker/session entries for branch creation, Task 92 archive, Task 93 scaffold, and Taskmaster state
- Stored guard/test evidence once implementation begins

## Emergency Bypass Protocol
- No bypass authorized.
