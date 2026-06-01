# Findings

- 2026-06-01 — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:scope|E:aegis_foundation/mcp_registration.py] Existing registration helpers already render, execute, and verify native MCP client commands; smoke tooling should reuse those paths and add isolated subprocess environment handling rather than duplicate command construction.
- 2026-06-01 — [S:20260601|W:task135-isolated-mcp-registration-smoke|H:scope|E:cmd`isolated temp HOME/CODEX_HOME smoke`] Manual tag acceptance showed real Codex registration passes only when `CODEX_HOME` exists before invocation, so the smoke command must pre-create `CODEX_HOME` for Codex.
