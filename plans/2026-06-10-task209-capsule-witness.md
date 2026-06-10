---
session_id: 2026-06-10-008
work_context: task209-capsule-witness
handler_target: .taskmaster/tasks/task_209.md
task_ids: [209]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/
  - .taskmaster/tasks/task_209.md
  - .taskmaster/tasks/task_209.md
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 209 Capsule PR-3.5: delivery witness v0

## Header
- **Session ID (S)**: 2026-06-10-008
- **Work Context (W)**: task209-capsule-witness
- **Handler Target (H)**: .taskmaster/tasks/task_209.md
- **Task IDs**: 209
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/, .taskmaster/tasks/task_209.md, .taskmaster/tasks/task_209.md, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Pin the PR-3.5 boundary: four local checks + CI-mode split (ledger does not travel to CI), delivery report output, workflow wiring, required-check flip stays with the owner | docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/designs/witness-scope.md | completed |
| plan-step-implement | Implement witness_lib.py, aegis witness CLI (--base/--json/--ci), gate classification, aegis-witness workflow, mirrors | aegis_foundation/cli.py; docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Fixture tests (scope mapping, diff accounting, test-deletion escalation, verification-at-HEAD, done-flip containment, CI split), live witness run on this branch, full suite + guard stack | docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/TRACKER.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260610-task209-capsule-witness-ACTIVE/`
- `.taskmaster/tasks/task_209.md`
- `.taskmaster/tasks/task_209.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `209`

## Branch Policy
- Working branch: `feat/task-209-capsule-witness`

## Amendments & Versioning
- 2026-06-10 - Task 209 kickoff created via the guided wizard flow.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 209 and its subtasks.
  3. Read AEGIS_CAPSULE_SPEC.md section 5.1 and designs/witness-scope.md.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: witness must stay zero-LLM and deterministic; CI mode must not pretend to verify what the ledger cannot prove there; never re-implement CI greenness.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Wizard design note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
