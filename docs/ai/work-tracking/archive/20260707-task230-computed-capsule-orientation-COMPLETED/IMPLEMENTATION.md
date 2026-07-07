# Task 230 Computed capsule active-task orientation fields – Implementation Notes

## Planned Workstreams
- Extend the computed capsule's `task_truth` object with deterministic orientation fields:
  `active_task`, `active_subtask`, `next_action`, and `orientation_source`.
- Derive orientation from mechanical sources only: current branch task id, Aegis
  current-work task id, and Taskmaster status fallback.
- Render the fields in capsule markdown/injection so a fresh or resumed agent can answer
  "what task am I on and what should I do next?" without PR-3 narration.
- Preserve managed asset parity by syncing `.claude/scripts/brief_lib.py` to
  `aegis_foundation/assets/.claude/scripts/brief_lib.py`.
- Add focused tests for branch-derived active task/subtask orientation and pending task
  next-action behavior.

## Implemented
- Added branch/current-work/Taskmaster orientation helpers to `brief_lib.py`.
- Added `task_truth.active_task`, `task_truth.active_subtask`, `task_truth.next_action`,
  and `task_truth.orientation_source`.
- Updated the capsule markdown renderer with a `Current work` line.
- Added regression tests in `tests/claude_adapter/test_brief_lib.py`.
