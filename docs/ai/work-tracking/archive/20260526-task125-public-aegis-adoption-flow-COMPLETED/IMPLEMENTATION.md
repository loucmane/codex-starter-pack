# Task 125 Build Public Aegis Real-Project Adoption Flow – Implementation Notes

## Planned Workstreams
- Public CLI flow:
  - Added `aegis init` for first-time project setup with Claude as the public default primary agent.
  - Added `aegis start "<task title>"` for local tracked work without Taskmaster or Serena.
  - Added `aegis mcp register claude` wrapper for native Claude MCP registration.
- Installed runtime guidance:
  - Updated generated `CLAUDE.md`, `.aegis/contract.md`, and next-action guidance so normal-language requests can trigger `aegis start` when readiness is blocked on `main`.
  - Preserved existing project `CLAUDE.md` content below the Aegis runtime block.
- MCP/automation flow:
  - Added `aegis.init` and `aegis.start` MCP tools.
  - Kept implementation work on native agent tools; Aegis remains the workflow/evidence layer.
- Acceptance:
  - Captured initial fresh/existing smoke evidence in `reports/public-flow/initial-public-flow-smoke.md`.
  - Captured fresh Claude normal-language live acceptance in `reports/public-flow/normal-language-claude-live-acceptance.md`.



## Progress Log

- **2026-05-26 12:51** — [S:20260526|W:task125-public-aegis-adoption-flow|H:codex:implementation|E:docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/reports/public-flow/initial-public-flow-smoke.md] Implemented initial public Aegis init/start/MCP wrapper slice and captured smoke evidence
- **2026-05-27 13:25** — [S:20260527|W:task125-public-aegis-adoption-flow|H:codex:implementation|E:docs/ai/work-tracking/active/20260526-task125-public-aegis-adoption-flow-ACTIVE/reports/public-flow/normal-language-claude-live-acceptance.md] Verified the installed public flow with a normal-language fresh Claude task

