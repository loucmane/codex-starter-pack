# Agents Catalog

## Codex Deep Work Agent
- **Entry Point**: `CODEX.md`
- **Profile**: `deep-work` (default); `fast-iterate` available for medium reasoning.
- **Sandbox**: `workspace-write` with on-request approvals.
- **Tools**:
  - Built-ins: `shell`, `update_plan`, `view_image`.
  - MCP Servers: `serena`, `taskmaster-ai`, `context7-mcp`, `sequential-thinking`, `firecrawl-mcp`, `elevenlabs-mcp`, `fpl-mcp` (optional install).
- **Protocols**: ULTRATHINK handshake (Codex edition), handler search prechecks, registry-first discovery.
- **Documentation**: see `templates/TOOLS.md` for tool routing and `templates/engine/` for execution protocols.

Use this entry when launching Codex sessions via the wrapper (`codex resume`) to ensure the right profile, sandbox, and toolchain are applied.
