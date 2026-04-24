# Task 96 Interactive Template Wizard – Implementation Notes

## Planned Workstreams
- Add a `wizard kickoff` subcommand to `scripts/codex-task`.
- Reuse the existing work-tracking scaffold helper rather than duplicating artifact generation.
- Generate a compliant session file, plan file, current symlinks, and `sessions/state.json`.
- Update Taskmaster status and seed initial plan sync as part of kickoff.
- Add focused tests and document the new helper surface.
