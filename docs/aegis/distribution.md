# Aegis Distribution Contract

This document describes release-oriented install and invocation paths for Aegis Foundation. The development checkout and editable package modes in `docs/aegis/invocation-contract.md` remain supported.

Release lifecycle policy lives in `docs/aegis/release-policy.md`; operational upgrade, downgrade, and rollback flow lives in `docs/aegis/update-rollback.md`; reusable CI snippets and release matrix live in `docs/aegis/ci-install-templates.md` and `docs/aegis/release-verification-matrix.md`; MCP client setup for Codex, Claude, and generic stdio clients lives in `docs/aegis/mcp-client-setup.md`.

## Package Identity

- Distribution package: `aegis-foundation`
- CLI command: `aegis`
- MCP command: `aegis-mcp-server`
- Import packages: `aegis_foundation`, `aegis_mcp`

Check the installed version:

```bash
aegis --version
```

Inspect MCP startup configuration without starting a transport:

```bash
aegis-mcp-server --describe-config
```

## Local Wheel Verification

Before public publication, build a local wheel and install it into an isolated environment:

```bash
uv build --wheel --out-dir dist
python3 -m venv .venv-aegis-release
.venv-aegis-release/bin/python -m pip install dist/aegis_foundation-0.1.0-py3-none-any.whl
```

From the target project directory, run the installed command without `AEGIS_SOURCE_ROOT`:

```bash
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
aegis verify --target-dir . --strict
```

The installed command must resolve packaged Aegis assets from the wheel, not from the source checkout.

For release-candidate artifact certification from the source checkout, use:

```bash
aegis certify-release --source-dir . --dist-dir dist/aegis-release-candidate --report-file reports/aegis-release-certification/certification-report.json
```

The generated certification report records artifact checksums, provenance, artifact content inspection, clean installed-wheel smoke results, strict verification evidence, and the GitHub-before-PyPI publication handoff.

## Public Install Snippets

After publishing `aegis-foundation`, install with pip:

```bash
python3 -m pip install aegis-foundation
```

Run with `uvx`:

```bash
uvx --from aegis-foundation aegis inspect --target-dir .
uvx --from aegis-foundation aegis status --target-dir .
uvx --from aegis-foundation aegis plan-install --target-dir . --primary-agent claude --agent claude
uvx --from aegis-foundation aegis verify --target-dir .
```

Run with `pipx`:

```bash
pipx run --spec aegis-foundation aegis inspect --target-dir .
pipx run --spec aegis-foundation aegis status --target-dir .
pipx run --spec aegis-foundation aegis plan-install --target-dir . --primary-agent claude --agent claude
pipx run --spec aegis-foundation aegis verify --target-dir .
```

For local pre-publication smoke tests:

```bash
uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .
pipx run --spec ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis inspect --target-dir .
```

## MCP Startup

Native MCP client registration is the preferred bootstrap path. It registers the packaged `aegis-mcp-server` once, then lets the discovered `aegis.*` tools install and operate the workflow inside each target project.

Claude user/global scope:

```bash
claude mcp add --scope user aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio
```

Claude project scope:

```bash
claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio
```

Codex:

```bash
codex mcp add --env UV_CACHE_DIR=.aegis/uv-cache --env UV_TOOL_DIR=.aegis/uv-tools aegis -- uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio
```

Generate, execute, and verify those commands through Aegis:

```bash
aegis mcp generate-registration --client claude --scope user
aegis mcp generate-registration --client codex
aegis mcp execute-registration --client claude --scope user
aegis mcp verify-registration --client claude --scope user
```

Manual `.mcp.json` and Codex config-file snippets are fallback-only; native `claude mcp add` / `codex mcp add` coverage is required for release readiness.

For local/offline stdio startup from an installed package:

```bash
aegis-mcp-server --default-target-dir . --describe-config
aegis-mcp-server --default-target-dir . --transport stdio
```

Installed-package `--describe-config` output must report packaged assets, not a source checkout:

```json
{
  "asset_origin": "package",
  "distribution_name": "aegis-foundation",
  "source_root": ".../site-packages/aegis_foundation/assets"
}
```

When `--source-root /path/to/codex` or `AEGIS_SOURCE_ROOT` is explicitly supplied, `asset_origin` is `source`; this is the development checkout mode documented in `docs/aegis/invocation-contract.md`.

After publication, MCP clients can use `uvx` or `pipx` to run the same command:

```bash
uvx --from aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio
pipx run --spec aegis-foundation aegis-mcp-server --default-target-dir . --transport stdio
```

For local pre-publication MCP smoke tests:

```bash
uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --describe-config
uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
```

Hosted MCP service deployment is a supported release pattern, but this repository does not publish a hosted service in Task 113. A hosted deployment must document transport, authentication, version pinning, upgrade/rollback, and verification evidence before users treat it as production-ready.

## Safety

- Review `aegis plan-install` output before running `aegis install --apply`.
- Do not write `.aegis/` files directly.
- Preserve generated reports under `.aegis/reports/` as the evidence trail.
- Pin package versions in automation once releases are published.
