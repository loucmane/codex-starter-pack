# Task 127 Add Aegis handoff auto-repair flow – Implementation Notes

## Planned Workstreams
- Inspected `closeout`, `_closeout_handoff_checks`, and `_update_handoff_for_closeout` in `scripts/_aegis_installer.py`.
- Added deterministic handoff rendering that rebuilds semantic sections before `## Progress Log` while preserving the existing progress log.
- Added core `repair_handoff(...)` with dry-run preview and apply modes.
- Added package CLI support through `aegis handoff repair`.
- Added repo wrapper support through `python3 scripts/codex-task aegis handoff repair`.
- Added MCP support through `aegis.handoff_repair`, read-only by default and mutating only with `apply=true`.
- Added hook classifier handling so MCP handoff repair preview stays read-only while `apply=true` remains a tracked mutation.
- Added branch metadata normalization so local `aegis start` branch objects render as branch names in repaired handoffs.
- Fixed closeout report write ordering so the report file records `report_written=true` and `state_updated=true` when final closeout succeeds.
- Mirrored runtime changes into packaged assets under `aegis_foundation/assets/`.
- Added installer and MCP tests covering placeholder handoff repair, dry-run non-mutation, apply behavior, and closeout readiness after repair.
- Ran a fresh live workflow in `/tmp/aegis-task127-live-test-OC1Nir66/shop-webapp` and repaired the implementation based on the issues that surfaced.

## Changed Files
- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `scripts/codex-task`
- `aegis_foundation/assets/scripts/codex-task`
- `aegis_mcp/server.py`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`
