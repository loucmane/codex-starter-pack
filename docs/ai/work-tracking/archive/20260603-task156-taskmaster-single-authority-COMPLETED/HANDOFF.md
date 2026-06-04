# Task 156 Make Taskmaster the single task authority for Aegis surfaces – Handoff Summary

## Current State
- _Pending_

## Next Steps
- _Pending_
# Handoff

Task 156 is implemented and verified.

## Summary
- Aegis no longer picks a Taskmaster task id by parsing `tasks.json`.
- Valid Taskmaster projects now receive guidance to run `task-master next/show` and then call `aegis kickoff` with the explicit external id.
- Invalid Taskmaster projects surface `installed_taskmaster_invalid` with repair guidance and no local fallback.
- Reconcile reports `taskmaster_invalid` without false stale-stub findings when the authority file is malformed.

## Verification
- `tests/meta_workflow_guard/test_aegis_installer.py`: passed
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`: passed
- `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`: passed
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py`: passed
- Ruff on touched files: passed with the existing installer `E402` bootstrap ignored
- Archived on 2026-06-04 11:02 CEST — Folder moved to archive and tracker marked COMPLETED.
