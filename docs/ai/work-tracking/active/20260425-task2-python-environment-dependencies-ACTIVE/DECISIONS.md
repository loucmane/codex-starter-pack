# Decisions

- 2026-04-25 — Treat Task 2 as Python environment reproducibility/reconciliation, not as a local-machine package installation task. The acceptance bar is repository metadata plus verification, not incidental global imports.
- 2026-04-25 — Archived the completed Task 1 active work-tracking folder through `scripts/codex-task work-tracking archive` before starting Task 2, rather than deleting or recreating work-tracking state manually.
- 2026-04-25 — Use `pyproject.toml` for supported dependency ranges and `uv.lock`/`requirements.lock` for exact resolved versions. This avoids floating major-version upgrades while keeping the dependency policy readable.
- 2026-04-25 — Do not create a synthetic `src/` tree or require a custom virtualenv prompt just to satisfy stale Taskmaster wording. The current repository uses `scripts/`, `tests/`, and template/workflow directories; Task 2 completion is based on reproducible environment evidence.
- 2026-04-25 — End today's session without archiving the Task 2 work-tracking folder. The task is implementation-complete, but the PR remains open; archive should happen after merge or when starting the next completed-task transition.
