# Decisions

- 2026-05-25 — [S:20260525|W:task123-aegis-release-candidate-global-mcp-proof|H:codex:design|E:docs/ai/work-tracking/active/20260525-task123-aegis-release-candidate-global-mcp-proof-ACTIVE/designs/existing-project-copy-proof.md] Use a copied existing project under `/tmp` as the primary Task 123 live acceptance target. Do not mutate the original project. Keep Aegis MCP as the workflow control plane and native tools as the implementation surface.
- 2026-05-25 — [S:20260525|W:task123-aegis-release-candidate-global-mcp-proof|H:codex:implement|E:MANIFEST.in] Treat bytecode caches in packaged assets as release-blocking noise. Exclude `__pycache__`, `.pyc`, and `.pyo` from Aegis release artifacts before using the wheel for global MCP proof.
- 2026-05-25 — _Pending_ — capture decisions with context.
