# Task 184 Treat completed Aegis observations as terminal state – Implementation Notes

## Implemented
- Updated `.claude/scripts/readiness.sh` so in-progress observations still use observation-specific readiness, but completed observations are treated as terminal and fall back to normal branch/task readiness.
- Updated `scripts/_aegis_installer.py` so `next_action()` returns `state: observation_completed` for completed observations and suggests kickoff/observe-start instead of `observe stop`.
- Made `stop_observation()` idempotent for already-completed observations, returning `status: completed`, `idempotent: true`, and `already_completed: true`.
- Mirrored both changes into `aegis_foundation/assets/`.

## Tests
- Extended the observation-mode regression to assert completed observations:
  - produce `next_action.state == observation_completed`,
  - no longer include `observe stop` in copyable repairs,
  - fall back to the normal `branch 'main' does not contain a task ID` readiness block,
  - still block Taskmaster mutation until kickoff,
  - allow repeated `observe stop` as an idempotent completed response.
