# Task 98 Externalize Repo Structure Configuration – Implementation Notes

## Planned Workstreams
- Define the repo-structure config contract and baseline inventory.
- Add a shared loader for repo-local path roots.
- Update `codex-guard`, `codex-task`, and `template-metrics-dashboard` to derive operational paths from the loader.
- Add regression tests for the loader and keep the existing workflow suites green.

## Completed Work
- Added `[repo_structure]` defaults to `.codex/config.toml`.
- Added `scripts/_repo_structure.py` to load repo-local roots and derive the concrete workflow paths.
- Updated `codex-task`, `codex-guard`, and `template-metrics-dashboard` to use the shared loader.
- Added `tests/meta_workflow_guard/test_repo_structure_config.py`.
- Updated shared docs in `templates/TOOLS.md` and `templates/engine/core/codex-readiness.md`.
