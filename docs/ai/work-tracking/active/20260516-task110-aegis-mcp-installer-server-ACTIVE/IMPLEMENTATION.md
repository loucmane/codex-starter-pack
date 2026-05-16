# Task 110 Build Aegis MCP Installer Server – Implementation Notes

## Planned Workstreams
- `110.1` — Scaffold importable MCP package, server factory, and stdio entrypoint. **Done**: added `aegis_mcp/server.py`, `aegis_mcp/__init__.py`, `scripts/aegis-mcp-server`, `mcp>=1.0,<2.0`, and initial scaffold tests.
- `110.2` — Register V1-backed `aegis.*` tools and formal input schemas. **Done**: registered the six V1 tool contracts and validation tests without wiring core handlers yet.
- `110.3` — Wire handlers to the installer core with schema checks and structured MCP errors. **Done**: tool handlers call the core installer module, validate core payloads, and map predictable failures to structured MCP payloads.
- `110.4` — Expose read-only `aegis://` resources and safe workflow prompts.
- `110.5` — Update implementation docs, MCP config guidance, and local smoke coverage.

## 110.1 Scaffold Notes
- The server factory uses `mcp.server.fastmcp.FastMCP` from the official Python MCP SDK.
- `create_server` attaches `aegis_config` and `aegis_installer` to the server instance so later subtasks can register handlers without duplicating installer behavior.
- The entrypoint supports `--describe-config` for smoke testing without starting a long-running transport.
- Production tools are intentionally not registered in 110.1; `110.2` owns tool schema registration.

## 110.2 Tool Schema Notes
- `create_server` now calls `register_v1_tools`, which registers exactly the six V1-backed MCP tools: `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.list_profiles`, and `aegis.explain_profile`.
- Deferred production tools are intentionally absent: `aegis.status`, `aegis.plan_update`, `aegis.update`, and `aegis.rollback`.
- FastMCP/Pydantic schemas mirror the installer constraints: only `profile=generic`, `primary_agent` limited to `claude|codex|gemini|multi|none`, and `agents` as a unique list limited to `claude|codex|gemini`.
- `aegis.plan_install` requires explicit `target_dir`, `primary_agent`, and `agents`.
- `aegis.install` requires explicit `target_dir`, `profile`, `primary_agent`, `agents`, and `apply`; `apply` must be `true` before handler wiring can proceed.
- `aegis.verify` requires explicit `target_dir` and `acknowledge_report_write`; the acknowledgement must be `true` because the core verifier writes reports.
- Valid calls return a `handler_deferred` payload until `110.3` wires the tools to `scripts/_aegis_installer.py`. This keeps `110.2` focused on the public contract and avoids silently performing core behavior before the handler subtask.

## 110.3 Handler Wiring Notes
- The MCP handlers now call the existing installer core functions directly: `inspect_project`, `plan_install`, `install`, `verify`, `list_profiles`, and `explain_profile`.
- `aegis.plan_install` validates the returned plan against `schemas/aegis/install-plan.schema.json`; `aegis.explain_profile` validates the returned profile against `schemas/aegis/profile.schema.json`.
- Successful calls return a consistent wrapper: `{ "ok": true, "tool": "...", "read_only": true|false, "result": ... }`.
- Predictable failures return `{ "ok": false, "tool": "...", "error": { "code": "...", "message": "...", "status": "...", "details": ... } }` instead of leaking Python tracebacks through FastMCP.
- `aegis.install` refuses `apply=false` without calling the core and maps core `status=refused` and `status=failed` reports into structured errors while preserving report and cleanup payloads.
- `aegis.verify` refuses `acknowledge_report_write=false` without calling the core and maps failed verification reports into structured errors while preserving the verifier report details.
