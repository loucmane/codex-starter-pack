# Decisions

- 2026-05-31 — Treat `aegis.inspect` as an actionable workflow guidance surface, not just a read-only status probe. It must carry the not-installed hard stop because normal Claude sessions may call inspect first and then decide whether source edits are allowed.



## Progress Log

- **2026-05-31 09:21** — [S:20260531|W:task131-taskmaster-backed-aegis-acceptance|H:codex:ci-decision|E:tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py] Keep the MCP hard-stop behavior and update broader tests to model the required Claude restart instead of weakening the runtime contract.
- **2026-05-31 10:04** — [S:20260531|W:task131-taskmaster-backed-aegis-acceptance|H:codex:inspect-decision|E:aegis_mcp/server.py] Kept normal-language discovery while strengthening inspect itself: not-installed inspect now tells Claude to init before source edits, project verification, Taskmaster mutation, or start/kickoff.
