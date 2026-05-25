# Focused Regression Evidence - Task 121

Date: 2026-05-23

## Implementation Summary

Task 121 implemented the first hardening slice for Aegis workflow UX:

- `aegis log` now infers an event class (`scope`, `implementation`, `verification`, or `note`) and applies event-aware default surfaces when explicit surfaces are omitted.
- CLI and MCP `aegis.log` can consume pending S:W:H:E events by id through `--pending-id` / `pending_event_id`.
- Pending-event hook messages now include a copyable pending-id repair command.
- `aegis closeout` reports structured `repair_guidance` for missing evidence references and pending tracking.
- Installed contract docs now describe MCP/CLI as the control plane, native tools as the implementation path, and pending-id logging as the normal repair path.

## Focused Tests

Command:

```bash
uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_aegis_mcp_server.py \
  tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py \
  tests/meta_workflow_guard/test_aegis_release_distribution.py \
  tests/meta_workflow_guard/test_aegis_native_mcp_registration.py \
  tests/meta_workflow_guard/test_aegis_invocation_contract.py \
  tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py
```

Result:

```text
113 passed, 4 skipped in 29.14s
```

Skipped tests are opt-in release/wheel smoke tests:

- `AEGIS_RUN_CERTIFICATION_SMOKE=1`
- `AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1`
- `AEGIS_RUN_WHEEL_SMOKE=1`
- `AEGIS_RUN_WHEEL_MCP_SMOKE=1`

## Opt-In Fresh Target Smoke

Command:

```bash
AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py::test_local_wheel_mcp_real_target_project_smoke_when_enabled
```

Result:

```text
1 passed in 5.03s
```

## Focused Behaviors Covered

- Event-aware default surface selection for scope, implementation, and verification logs.
- Explicit `--surface` override remains backward compatible.
- Pending-event consumption by id in core `log_work`.
- Pending-event consumption by id through MCP `aegis.log`.
- Closeout repair guidance for missing evidence references.
- Live-style installed web target path using project-local `./.aegis/bin/aegis log --pending-id ...`.
- Invocation and MCP setup docs remain aligned with the control-plane/native-tool split.
- Local wheel/MCP smoke still installs into a real target project successfully.
