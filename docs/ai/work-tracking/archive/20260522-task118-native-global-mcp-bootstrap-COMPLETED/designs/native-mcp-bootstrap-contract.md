# Native MCP Bootstrap Contract

## Goal
Task 118 makes Aegis installable from any fresh project through native MCP client registration commands. A user should not need this repository cloned locally to register the Aegis MCP server, install the project runtime, or run the workflow gates.

## Primary Path
Native client registration is the default path:

- Claude user/global scope: `claude mcp add --scope user aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio`
- Claude project scope: `claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio`
- Codex: `codex mcp add --env UV_CACHE_DIR=.aegis/uv-cache --env UV_TOOL_DIR=.aegis/uv-tools aegis -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio`

The implementation should generate argv lists first, then render display commands from those argv lists. Execute mode must call native clients without `shell=True`.

## Source Modes
Supported source modes:

- Package: `aegis-foundation`
- Pinned package: `aegis-foundation==<version>`
- GitHub URL/ref
- Local wheel path
- Source checkout path

Package mode is the default. Source checkout mode is explicit and should not leak `/home/loucmane/codex` into generated fresh-project commands.

## Verification Contract
The generated registration payload should include:

- client (`claude` or `codex`)
- scope where applicable
- server name (`aegis`)
- source mode and package/artifact spec
- generated client argv
- MCP server argv
- rendered command for docs
- default target directory
- transport (`stdio`)
- safety notes

Verify mode should inspect native client state and report structured pass/fail checks for:

- `aegis` server exists
- command uses `uvx`
- command includes `--from <source>`
- command starts `aegis-mcp-server`
- command includes `--default-target-dir`
- command includes `--transport stdio`

Missing clients must return structured `missing_client` output without trying to write config files.

## Fallback Boundary
Manual `.mcp.json` or Codex config writes are fallback only. They must require an explicit fallback flag and must be documented after the native client path, not before it.

## Fresh-Project Acceptance
From a fresh directory with no checkout:

1. Generate the native registration command.
2. Register Aegis through the native client.
3. Confirm the client discovers the Aegis MCP server and `aegis.*` tools.
4. Use the registered tool path to install packaged runtime assets.
5. Run `aegis.kickoff`, `aegis.log`, `aegis.verify`, and `aegis.closeout`.

The target project must end up with Aegis workflow scaffolding and gates equivalent to this repository's portable runtime contract, without depending on Taskmaster or Serena being present.
