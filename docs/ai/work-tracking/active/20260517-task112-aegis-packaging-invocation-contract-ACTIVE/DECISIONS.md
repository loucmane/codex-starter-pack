# Decisions

- 2026-05-17 — Select a two-track V1 invocation contract: local-checkout absolute paths for development and package-style invocation for install-like usage. This keeps Task 112 practical without waiting for public package release work.
- 2026-05-17 — Preserve the existing Aegis architecture. `scripts/_aegis_installer.py` remains the installer source of truth, `scripts/codex-task aegis ...` remains the repository-local wrapper, and `aegis_mcp/server.py` remains the MCP control plane. New entrypoints must be thin dispatch, not a second installer engine.
- 2026-05-17 — Defer public distribution hardening. PyPI/registry publication, package signing, `uvx`/`pipx` release snippets, update migrations, rollback, hosted services, and CI install templates belong in a follow-up task after Task 112 proves the external invocation contract.
- 2026-05-17 — Keep `[tool.uv] package = false` for this task while adding editable package metadata. The V1 package-style contract is an editable/local install that proves the command surface (`aegis`, `aegis-mcp-server`) without changing uv project behavior or claiming wheel/public-release readiness.
