# Findings

- 2026-08-31 — The preserved `/home/loucmane/codex` checkout is absent from the project registry and has no descriptor, so `project_context.py` blocks only with a generic onboarding error. The error does not explain that the root is deliberately retired or identify `/home/loucmane/gas-city-ops`.
- 2026-08-31 — Codex user configuration still marks both the historical and canonical roots `trusted`; Claude's top-level Aegis MCP package source still names `/home/loucmane/codex`. Project-local guards are insufficient because untrusted projects skip project hook layers.
- 2026-08-31 — Official Codex hook behavior confirms user-level hooks remain active independently of project trust. `PreToolUse` can cover Bash, file editors, `apply_patch`, and MCP tools and fail closed with exit 2.
- 2026-08-31 — Git common-directory identity is the necessary boundary: every linked worktree owned by the historical checkout resolves to `/home/loucmane/codex/.git`, so a literal cwd comparison alone would be bypassable.
- 2026-08-31 — The repository migration manifest already holds the canonical and historical paths but described retirement as a future separate gate. A distinct v1 root-policy asset avoids breaking the stable project-registry schema while making the transition executable and testable.
