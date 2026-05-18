# Aegis Invocation Contract

This document defines the supported V1 ways to run Aegis from a project that is not the Aegis source checkout.

Task 112 deliberately separates two modes:

- **Development checkout mode**: use a local checkout of this repository by absolute path.
- **Package-style mode**: use the future install-like command surface. This mode is selected in Task 112 but finalized after the package entrypoint is implemented.

## Release Package Identity

Task 113 uses `aegis-foundation` as the working public distribution name. The import packages remain `aegis_foundation` and `aegis_mcp`, and the console commands remain:

```bash
aegis --version
aegis-mcp-server --describe-config
```

`aegis --version` reports the Aegis package version. `aegis-mcp-server --describe-config` reports the package distribution name plus foundation, installer, and schema versions alongside the resolved source and target directories.

The release package identity is additive. It does not remove the development checkout or editable package-style commands below.

See `docs/aegis/distribution.md` for local wheel, `pip`, `uvx`, `pipx`, MCP startup, and hosted-service release snippets.

## Development Checkout Mode

From the target project directory, replace `/path/to/codex` with the absolute path to the Aegis source checkout.

Inspect without mutating the project:

```bash
python3 /path/to/codex/scripts/codex-task aegis inspect --target-dir .
```

Plan an install without mutating the project:

```bash
python3 /path/to/codex/scripts/codex-task aegis plan-install --target-dir . --primary-agent claude --agent claude
```

Check release/update status without mutating the project:

```bash
python3 /path/to/codex/scripts/codex-task aegis status --target-dir .
```

Apply the install after reviewing the plan:

```bash
python3 /path/to/codex/scripts/codex-task aegis install --target-dir . --primary-agent claude --agent claude --apply
```

Verify the installed runtime:

```bash
python3 /path/to/codex/scripts/codex-task aegis verify --target-dir .
```

Use `--target-dir .` when running from the target project. Use an explicit target path when running from somewhere else.

## MCP Development Startup

Run the MCP server from the same local checkout, but point the default target directory at the project being managed.

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir /path/to/project
```

To inspect the resolved configuration without starting the transport:

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir /path/to/project \
  --describe-config
```

The MCP tools keep the same safety boundary as the CLI:

- `aegis.inspect` and `aegis.plan_install` are read-only.
- `aegis.status` is read-only and reports release/update state without writing target files.
- `aegis.install` requires explicit `apply=true`.
- `aegis.verify` writes a verification report and requires `acknowledge_report_write=true`.
- Agents must cite `.aegis/reports/*` or MCP tool/resource results as evidence, not prompt text.

## Editable Package-Style Mode

Task 112 supports local editable package-style invocation. This gives agents and developers the final command shape without requiring a public package release yet.

Create a local environment and install the checkout in editable mode:

```bash
python3 -m venv .venv-aegis
.venv-aegis/bin/python -m pip install -e /path/to/codex
```

Then run Aegis from the target project directory:

```bash
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
```

Start the editable package-style MCP server from the target project directory:

```bash
aegis-mcp-server --default-target-dir .
```

Inspect package-style MCP configuration without starting the transport:

```bash
aegis-mcp-server --default-target-dir . --describe-config
```

The editable install resolves Aegis assets from the source checkout. Public wheel assets, `uvx`, `pipx`, package signing, update migrations, rollback, hosted services, and CI install templates are out of scope for this contract task and belong to release hardening.

## Installed Target Commands

After Aegis is installed into a target project, the generated target still contains project-local helper files. Those are the runtime files used inside that target. The external invocation commands in this document are for adoption and management from outside the Aegis source repository.

## Safety Notes

- Do not run `install --apply` until the plan output has been reviewed.
- Do not write `.aegis/` directly. Use Aegis CLI or MCP operations.
- Treat `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, and `.aegis/reports/verification-report.json` as the evidence trail.
- Development checkout snippets may contain the source checkout path in local shell or MCP client configuration. Installed target `.aegis/` state should not depend on an absolute source checkout path.
