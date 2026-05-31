# Task 134 Private GitHub Distribution and Cross-Machine Install Flow – Implementation Notes

## Planned Workstreams
- Add first-class `private-github` registration source mode in `aegis_foundation/mcp_registration.py`.
- Keep package, pinned package, public GitHub, wheel, and source checkout modes backward compatible.
- Update package CLI and repo-local `scripts/codex-task aegis mcp ...` wrapper source-mode choices.
- Document private GitHub new-machine registration commands for Claude and Codex.
- Cover command generation, fake registration verification, and invocation-contract docs with focused tests.

## Progress Log
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:aegis_foundation/mcp_registration.py] Added `private-github` source mode, SSH URL normalization, and private GitHub safety-note output while preserving existing source modes.
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:aegis_foundation/cli.py] Added `private-github` to package CLI MCP registration choices and help text.
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:scripts/codex-task] Added `private-github` to the repo-local Aegis MCP registration wrapper choices.
- **2026-05-31 14:32** — [S:20260531|W:task134-private-github-distribution|H:apply_patch|E:docs/aegis/mcp-client-setup.md] Documented private GitHub registration commands for Claude and Codex.
