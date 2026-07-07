# Task 230 Scope - Computed Capsule Orientation Fields

## Goal

Add deterministic orientation fields to the computed capsule so a fresh or resumed
agent can see the active Taskmaster task, active subtask when present, and a concise
next action without PR-3 narration.

## In Scope

- Extend `.claude/scripts/brief_lib.py` and the managed asset copy at
  `aegis_foundation/assets/.claude/scripts/brief_lib.py`.
- Populate `task_truth.active_task`, `task_truth.active_subtask`,
  `task_truth.next_action`, and `task_truth.orientation_source`.
- Derive orientation from existing mechanical sources only:
  current branch task id, `.aegis/state/current-work.json`, and Taskmaster task state.
- Render the new fields in the computed capsule markdown/injection.
- Add focused tests in the existing capsule test suite.

## Out of Scope

- Stop checkpoints.
- SessionEnd distill.
- Lazy narration.
- LLM-authored capsule fields.
- PR-4 retirement or removal of sessions/plans/trackers/closeout scaffolding.
- New delivery witness behavior.

## Acceptance

- Focused capsule tests prove branch-derived task/subtask orientation and rendered
  `next_action`.
- Live and managed asset copies remain byte-identical.
- Taskmaster health, dependency validation, work-tracking audit, guard validation, and
  `git diff --check` pass before delivery.
