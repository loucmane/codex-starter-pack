# Task 110 Build Aegis MCP Installer Server – Implementation Notes

## Planned Workstreams
- `110.1` — Scaffold importable MCP package, server factory, and stdio entrypoint. **Done**: added `aegis_mcp/server.py`, `aegis_mcp/__init__.py`, `scripts/aegis-mcp-server`, `mcp>=1.0,<2.0`, and initial scaffold tests.
- `110.2` — Register V1-backed `aegis.*` tools and formal input schemas.
- `110.3` — Wire handlers to the installer core with schema checks and structured MCP errors.
- `110.4` — Expose read-only `aegis://` resources and safe workflow prompts.
- `110.5` — Update implementation docs, MCP config guidance, and local smoke coverage.

## 110.1 Scaffold Notes
- The server factory uses `mcp.server.fastmcp.FastMCP` from the official Python MCP SDK.
- `create_server` attaches `aegis_config` and `aegis_installer` to the server instance so later subtasks can register handlers without duplicating installer behavior.
- The entrypoint supports `--describe-config` for smoke testing without starting a long-running transport.
- Production tools are intentionally not registered in 110.1; `110.2` owns tool schema registration.
