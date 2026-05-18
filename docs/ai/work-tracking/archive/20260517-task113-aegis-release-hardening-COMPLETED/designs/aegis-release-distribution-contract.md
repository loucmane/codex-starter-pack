# Aegis Release Distribution Contract

## Context
Task 112 established that Aegis can be invoked from a development checkout and from an editable package install. Task 113 extends that into a release-ready contract for users who install Aegis as a package and run the CLI or MCP server from outside this repository.

## Current Baseline
- `pyproject.toml` still uses provisional metadata from the starter-pack repository.
- `aegis_foundation/cli.py` delegates to `scripts._aegis_installer` and supports checkout/editable operation.
- `aegis_mcp/server.py` exposes the MCP server and development startup paths.
- `docs/aegis/invocation-contract.md` explicitly defers public wheel assets, `uvx`/`pipx`, signing, update migration, rollback, hosted MCP service guidance, and CI install templates.
- Task 112 evidence proves the development contract; Task 113 must not break it.

## Release Contract Targets
1. Public package identity is explicit and consistent between `pyproject.toml`, docs, CLI output, MCP diagnostics, and tests.
2. Version reporting is single-source enough to keep `pyproject.toml`, `aegis_foundation`, installer constants, and command output aligned.
3. Wheel and sdist artifacts include all Aegis assets needed to inspect, plan, install, and verify a target project without source-checkout access.
4. External installs can run `aegis` and `aegis-mcp-server` from a non-repository cwd.
5. `uvx` and `pipx` snippets are documented with local-wheel verification paths before public publishing is required.
6. Update, migration, rollback, signing, provenance, checksum, hosted/offline MCP, and CI install flows are documented honestly and tested where deterministic.

## Non-Goals
- Publishing to PyPI or another package registry.
- Removing `scripts/codex-task aegis ...`.
- Removing checkout or editable install support.
- Renaming the `aegis` or `aegis-mcp-server` console commands without a concrete collision.
- Adding mutating update/rollback behavior unless it can reuse the existing installer safety model and has deterministic tests.

## Verification Requirements
- Metadata and version tests assert package identity and command stability.
- Build tests inspect wheel and sdist contents.
- External install tests run from a temp cwd outside the repository without `AEGIS_SOURCE_ROOT`.
- MCP startup tests prove `--describe-config` and stdio discovery from an external cwd.
- Documentation tests assert update, rollback, signing, `uvx`/`pipx`, hosted/offline MCP, and CI template coverage.
- Final workflow checks store plan sync, Taskmaster health, work-tracking audit, codex guard, and diff-check evidence.
