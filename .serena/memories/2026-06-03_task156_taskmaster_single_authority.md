# Task 156 - Taskmaster Single Authority

Implemented Taskmaster-present authority hardening for Aegis.

Key points:
- Added `TaskmasterState` classification with `absent`, `valid`, and `invalid` outcomes.
- Suppressed Aegis next-task selection whenever `.taskmaster/tasks/tasks.json` exists and is valid.
- Made present-but-invalid Taskmaster data a repair-required state instead of a local fallback trigger.
- Made `start_local_work` refuse valid and invalid Taskmaster-present projects.
- Updated reconcile to report `taskmaster_invalid` and avoid false stale-stub findings when Taskmaster is unreadable or malformed.
- Synced the mirrored packaged installer file.

Verification:
- `tests/meta_workflow_guard/test_aegis_installer.py`: 66 passed, 1 skipped.
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`: 48 passed.
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`: 34 passed.
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py`: 19 passed.
- Ruff passed on touched files with the known installer E402 bootstrap ignored.
