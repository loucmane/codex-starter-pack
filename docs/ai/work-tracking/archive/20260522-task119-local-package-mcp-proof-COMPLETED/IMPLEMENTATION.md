# Task 119 Local-First Aegis Package and MCP Installation Proof – Implementation Notes

## Planned Workstreams
- Local artifact registration hardening: validate wheel/source paths and emit absolute `uvx --from` specs so native clients can run from fresh project folders.
- Local artifact certification: build wheel/sdist, inspect required assets, run clean installed-wheel CLI smoke, and run local-wheel MCP server config smoke.
- Fresh target proof: run the local wheel MCP target smoke through install, kickoff, S:W:H:E logging, strict verification, closeout, and source-checkout leakage checks.

## Progress Log
- 2026-05-22 15:24 CEST — [S:20260522|W:task119-local-package-mcp-proof|H:implementation:local-artifact-registration|E:aegis_foundation/mcp_registration.py] Hardened local `wheel` and `source` MCP source modes with artifact shape validation and absolute package specs.
- 2026-05-22 15:24 CEST — [S:20260522|W:task119-local-package-mcp-proof|H:implementation:release-certification|E:scripts/_aegis_installer.py] Extended release certification with local-wheel MCP server config smoke and kept full MCP stdio workflow proof in the focused pytest target.
- 2026-05-22 15:24 CEST — [S:20260522|W:task119-local-package-mcp-proof|H:documentation:local-proof-gate|E:docs/aegis/release-policy.md] Documented local artifact MCP target smoke as the blocking precondition before TestPyPI/PyPI publication.
