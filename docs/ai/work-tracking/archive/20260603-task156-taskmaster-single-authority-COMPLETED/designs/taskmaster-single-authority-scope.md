# Task 156 Scope - Taskmaster Single Authority

## Scope
- Treat `.taskmaster/tasks/tasks.json` path existence as the Taskmaster authority boundary.
- Suppress Aegis task-selection heuristics whenever Taskmaster is present and valid.
- Surface Taskmaster-present-invalid as a distinct repair-required state instead of falling back to local Aegis work.
- Preserve local Aegis task allocation only for Taskmaster-absent projects.
- Keep reconcile read-only while avoiding false stale-stub findings when Taskmaster is unreadable or malformed.

## Files
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`

## Non-Goals
- No Taskmaster CLI invocation from Aegis to compute `next`.
- No source/project feature edits.
- No reconcile apply/write behavior changes.
