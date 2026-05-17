# Task 112 Aegis Packaging and Invocation Contract – Implementation Notes

## Planned Workstreams
- Scope reconciliation:
  - Document the V1 invocation contract in `designs/aegis-invocation-contract.md`.
  - Keep installer semantics in `scripts/_aegis_installer.py` and treat new entrypoints as thin wrappers.
- Local-checkout external invocation:
  - [x] Added focused tests proving `python3 /path/to/codex/scripts/codex-task aegis ...` works from an external project `cwd`.
  - [x] Documented the development checkout commands in `docs/aegis/invocation-contract.md`.
- Package-style invocation:
  - [x] Added `aegis_foundation.cli` as a thin package-style CLI wrapper over `scripts._aegis_installer`.
  - [x] Added local editable console scripts for `aegis` and `aegis-mcp-server` in `pyproject.toml`.
  - [x] Kept `[tool.uv] package = false`; Task 112 validates editable package-style invocation while release hardening owns public wheel/uvx/pipx behavior.
- MCP external startup:
  - [x] Preserved `AegisMCPConfig.from_paths`, `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR`.
  - [x] Added external-cwd `--describe-config` coverage for local-checkout and editable package-style MCP startup.
  - [x] Added a stdio smoke that starts the local-checkout MCP server from an external cwd and lists Aegis tools/resources/prompts.
- Verification and handoff:
  - Capture pytest, plan-sync, Taskmaster health, work-tracking audit, guard, and diff-check evidence under `reports/aegis-packaging-invocation-contract/`.
