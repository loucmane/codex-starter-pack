# Task 100 Build Foundation Bootstrap Layer – Implementation Notes

## Planned Workstreams
- Define the bootstrap command surface under `scripts/codex-task`.
- Identify the starter assets required for a new repo: repo-local config, metadata policy, and workflow roots.
- Make bootstrap behavior migration-safe for repos that already contain workflow directories or template docs.
- Add tests that cover empty-repo setup and pre-existing-file behavior.

## Completed Work
- Added `codex-task bootstrap init` to scaffold starter foundation assets into a target repository.
- Seeded bootstrap outputs with a repo-local `.codex/config.toml`, metadata policy file, setup notes, and workflow root directories.
- Kept bootstrap non-destructive by default and added explicit `--force` handling for starter-file refreshes.
- Added regression coverage for empty-repo bootstrap, existing-repo preservation, and forced starter-file refresh.
- Updated shared tool/workflow docs to describe when bootstrap should be used relative to kickoff.
