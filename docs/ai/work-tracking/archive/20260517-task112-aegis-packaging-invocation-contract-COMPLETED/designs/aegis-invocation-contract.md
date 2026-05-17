# Aegis Invocation Contract - Task 112

## Purpose

Task 111 proved that Aegis can install and verify isolated target projects, but the smoke coverage still launched the repository CLI with `cwd` set to this source checkout. Task 112 defines the first stable external invocation contract so a fresh project can adopt Aegis without starting commands from `/home/loucmane/codex`.

The contract has two jobs:

- Give developers a local-checkout path while Aegis is still developed from this repository.
- Give package consumers a package-style path that can later become a public release path without changing installer semantics.

## Current Architecture

- `scripts/_aegis_installer.py` is the deterministic installer source of truth. It owns inspect, plan, install, verify, profile listing, profile explanation, managed asset copying, report writes, and safety checks.
- `scripts/codex-task aegis ...` is the current repository-local CLI wrapper. It derives `REPO_ROOT` from the script path, so it can already be launched by absolute path from another directory, but Task 111 did not prove that behavior.
- `aegis_mcp/server.py` is the MCP control plane. `AegisMCPConfig.from_paths` already supports `--source-root`, `--default-target-dir`, `AEGIS_SOURCE_ROOT`, and `AEGIS_DEFAULT_TARGET_DIR`.
- `scripts/aegis-mcp-server` is the local-checkout MCP entrypoint and inserts the source checkout into `sys.path`.
- `pyproject.toml` currently sets `[tool.uv] package = false` and has no console-script entrypoints.

## Option Matrix

| Option | Shape | Pros | Risks | V1 Decision |
| --- | --- | --- | --- | --- |
| Local checkout absolute path | `python3 /path/to/codex/scripts/codex-task aegis inspect --target-dir .` | Uses existing tested wrapper, no packaging churn, works before publication | User must know the source checkout path | Supported as the V1 development contract |
| Local checkout MCP path | `python3 /path/to/codex/scripts/aegis-mcp-server --source-root /path/to/codex --default-target-dir /path/to/project` | Uses existing MCP config contract and explicit paths | Config snippets must not leak into installed target state | Supported as the V1 development MCP contract |
| Local editable console scripts | `aegis inspect --target-dir .`; `aegis-mcp-server --default-target-dir .` | Closest to eventual public package UX, easiest for agents to call | Wheel asset bundling remains a release-hardening concern | Supported as the V1 package-style contract |
| `python -m` module entrypoint | `python -m aegis_foundation.cli inspect --target-dir .` | Simple fallback if console scripts become too broad | Less polished UX and still needs package importability | Fallback only if console scripts become impractical |
| `uvx --from` or `pipx run --spec` | `uvx --from /path/to/wheel aegis inspect` | Mirrors package execution without permanent install | Adds tool-specific complexity to tests and docs | Deferred until release hardening unless trivial through console scripts |
| MCP-only installer | Use only `aegis.*` MCP tools | Useful for agents, but not enough for shell-first adoption | Makes CLI adoption dependent on MCP clients | Rejected as the only contract |
| Public PyPI/registry publish | `uvx aegis-foundation` or `pipx run aegis-foundation` | Final distribution target | Naming, signing, versioning, and release governance are not ready | Out of scope for Task 112 |

## Selected V1 Contract

### Development Local Checkout

From a fresh external project directory:

```bash
python3 /path/to/codex/scripts/codex-task aegis inspect --target-dir .
python3 /path/to/codex/scripts/codex-task aegis plan-install --target-dir . --primary-agent claude --agent claude
python3 /path/to/codex/scripts/codex-task aegis install --target-dir . --primary-agent claude --agent claude --apply
python3 /path/to/codex/scripts/codex-task aegis verify --target-dir .
```

MCP development startup:

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir /path/to/project
```

Diagnostic startup must also work from an external `cwd`:

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir . \
  --describe-config
```

### Package-Style Local Install

Task 112 supports local editable console scripts without duplicating installer behavior:

```bash
python3 -m venv .venv-aegis
.venv-aegis/bin/python -m pip install -e /path/to/codex
```

Then, from the target project directory:

```bash
aegis inspect --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
aegis-mcp-server --default-target-dir .
```

The editable console script resolves Aegis assets from the local checkout. Public wheel asset bundling, `uvx`, and `pipx` are deferred to release hardening.

## Implementation Boundaries

- Do not move installer semantics out of `scripts/_aegis_installer.py`.
- Keep `scripts/codex-task aegis ...` as the repository-local wrapper.
- Keep `aegis_mcp/server.py` as the MCP control plane.
- New package-style CLI code must be thin dispatch over the installer source of truth.
- Default target directory for external commands is the caller's current directory, not the Aegis source checkout.
- Source assets resolve from explicit `--source-root`/`AEGIS_SOURCE_ROOT` in development mode or from bundled package assets in package mode.
- Do not write source-checkout absolute paths into installed target `.aegis/` state except explicitly documented development MCP snippets outside target reports/state.
- Do not publish Aegis publicly in Task 112.
- Do not implement update migrations, rollback, package signing, hosted services, CI install templates, or a second installer engine.

## Required Test Shape

- Add `tests/meta_workflow_guard/test_aegis_invocation_contract.py`.
- Prove local-checkout CLI commands from an external `cwd` with absolute paths and `--target-dir .`.
- Prove the selected package-style command from an external `cwd`.
- Prove inspect and plan do not mutate the target.
- Prove install and verify write the expected `.aegis/reports/*` evidence and preserve seeded user files.
- Prove path-leak protection by scanning target `.aegis/` reports and generated project-facing docs for unintended source-checkout absolute paths.
- Prove external MCP startup with `--describe-config` for development and package-style forms.
- Extend documentation assertions so `docs/aegis/invocation-contract.md` contains the selected local-checkout and package-style commands, explicit target/source-root guidance, and no stale `foundation.*` or `foundation://` naming.

## Follow-Up Recommendation

After Task 112, create a release hardening task for public package naming, published package metadata, `uvx`/`pipx` install snippets, package signing, CI install templates, update migrations, and rollback design. Those are distribution hardening concerns, not prerequisites for the first external invocation contract.
