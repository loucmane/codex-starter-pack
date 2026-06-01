# Findings

- 2026-05-31 — Current Aegis registration already supports package, pinned package, public GitHub, wheel, and source checkout modes. The missing product surface is an explicit private GitHub mode with new-machine commands that do not depend on PyPI/TestPyPI or a local checkout.
- 2026-05-31 — The repository remote uses SSH (`git@github.com:loucmane/codex-starter-pack.git`), so the private happy path should prefer `git+ssh://git@github.com/loucmane/codex-starter-pack.git@<ref>` for `uvx --from`.
- 2026-05-31 — Manual `.mcp.json` and Codex config-file writes are documented as fallback-only; Task 134 should keep native `claude mcp add` and `codex mcp add` as the first-class registration path.
