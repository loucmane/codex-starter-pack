# Task 133 Run Codex Live Aegis Acceptance Test – Implementation Notes

## Planned Workstreams
- `aegis_mcp/server.py`: added server-level default primary-agent and agent-list configuration, wired through MCP tools and CLI parser flags so a Codex-registered MCP server can default `aegis.init` guidance to `primary_agent=codex`, `agents=["codex"]`.
- `scripts/_aegis_installer.py` and `aegis_foundation/assets/scripts/_aegis_installer.py`: added MCP-first bootstrap guidance, existing `AGENTS.md` merge/preservation, installed-agent-aware log guidance, duplicate external-task slug normalization, and exact verification-report path guidance.
- `tests/meta_workflow_guard/test_aegis_mcp_server.py`: added Codex default guidance coverage and strengthened MCP tool description expectations around MCP-first init.
- `tests/meta_workflow_guard/test_aegis_installer.py`: added coverage for preserving existing `AGENTS.md` content and Codex-primary explicit log guidance without pending queue assumptions.
- Live acceptance evidence:
  - Failed/recovery runs: `/tmp/aegis-task133-codex-live-1780220128`, `/tmp/aegis-task133-codex-live-full-1780221000`, `/tmp/aegis-task133-codex-live-full2-1780222000`, `/tmp/aegis-task133-codex-live-full3-1780222312`
  - Final clean pass: `/tmp/aegis-task133-codex-live-full4-R8DoDU`
  - Final nested Codex report: `/tmp/aegis-task133-codex-live-full4-R8DoDU/codex-last-message.txt`
