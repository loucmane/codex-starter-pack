# Task 101 Add Cross-Project Compatibility Fixtures – Implementation Notes

## Planned Workstreams
- Define the fixture families and the repo-shape assumptions each one should exercise.
- Add tests or fixture helpers that bootstrap alternate repo layouts without relying on this repo's default roots.
- Verify that guard, metrics, and related helpers resolve configured paths consistently across those shapes.
- Keep the suite focused on compatibility coverage rather than building sample apps.

## Completed Work
- Added `tests/meta_workflow_guard/cross_project_fixtures.py` as a reusable repo-shape fixture layer.
- Extended repo-structure tests to validate all four fixture families against the config loader.
- Extended bootstrap tests so `codex-task bootstrap init` is exercised across each repo-shape override set.
- Extended guard tests so template metadata drift is validated under non-default template roots.
- Extended metrics tests so work-tracking and kickoff-session discovery are validated under non-default roots.
