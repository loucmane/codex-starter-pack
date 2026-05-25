# Findings

- 2026-05-25 — [S:20260525|W:task123-aegis-release-candidate-global-mcp-proof|H:codex:design|E:docs/ai/work-tracking/active/20260525-task123-aegis-release-candidate-global-mcp-proof-ACTIVE/designs/existing-project-copy-proof.md] Task 123 should treat the copied existing project as the primary release-candidate proof. Fresh fixtures are supporting tests; the real acceptance target is a `/tmp` copy of a user-supplied project.
- 2026-05-25 — [S:20260525|W:task123-aegis-release-candidate-global-mcp-proof|H:codex:verify|E:docs/ai/work-tracking/active/20260525-task123-aegis-release-candidate-global-mcp-proof-ACTIVE/reports/release-candidate-global-mcp-proof/artifact-build.md] The first release-candidate build exposed a packaging-quality issue: generated `__pycache__` files under `aegis_foundation/assets/` were included in wheel/sdist output. Task 123 fixed this before live MCP testing.
- 2026-05-25 — _Pending_ — document new findings here.
