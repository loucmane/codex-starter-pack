# Task 120 Fresh Local Install Proof

Task 120 validates Aegis local-first publishing readiness before PyPI/TestPyPI.

Key outcomes:

- Built a local wheel and sdist under Task 120 work-tracking evidence.
- Registered a project-scoped Claude MCP server in `/tmp/aegis-task120-claude-live-shop-dry91w` using `claude mcp add --scope project` and `uvx --from <local wheel>`.
- Found and fixed a project-local shim portability bug: wheel installs generated `.aegis/bin/aegis` with a packaged `assets/` path that was not an importable Python root.
- Found and fixed a hidden-directory protection bug: `normalize_path(...).lstrip("./")` stripped leading dots from `.aegis/` and `.claude/`, preventing protected-prefix matches.
- Expanded installed protected runtime paths to include `.aegis/**`, `.claude/**`, `CLAUDE.md`, and `AGENTS.md`.
- Final proof target `/tmp/aegis-task120-proof-shop-final-cNydTu` passed install, local shim status, cold readiness block, kickoff READY, pending S:W:H:E tracking, stop-gate block, implementation logging, protected path blocking, strict verify, and closeout.

Publishing remains blocked until the live Claude test from `/tmp/aegis-task120-claude-live-shop-dry91w` passes.
