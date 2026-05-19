# Aegis MCP Client Setup

This guide documents release-candidate MCP setup for Codex, Claude, and generic MCP clients. Use it with the distribution contract in `docs/aegis/distribution.md` and the release verification matrix in `docs/aegis/release-verification-matrix.md`.

## Release Candidate Channel

Task 114 validates local wheel and sdist artifacts as the release-candidate baseline. The first public distribution channel should be GitHub release artifacts if the clean-project CLI and MCP evidence remains green. PyPI publication is a later explicit release task.

For local release-candidate testing, build the artifact first:

```bash
uv build --sdist --wheel --out-dir dist
```

Then use the wheel path:

```text
./dist/aegis_foundation-0.1.0-py3-none-any.whl
```

After publication, replace the wheel path with a pinned package requirement such as `aegis-foundation==0.1.0`.

## MCP Server Command

The installed MCP server command is:

```bash
uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
```

Check startup without launching stdio transport:

```bash
uvx --from ./dist/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --describe-config
```

Release-candidate output must report package assets:

```json
{
  "asset_origin": "package",
  "distribution_name": "aegis-foundation"
}
```

## Codex MCP Config

Use a project-local Codex config entry when testing a release candidate:

```toml
[mcp_servers.aegis]
command = "uvx"
args = [
  "--from",
  "./dist/aegis_foundation-0.1.0-py3-none-any.whl",
  "aegis-mcp-server",
  "--default-target-dir",
  ".",
  "--transport",
  "stdio",
]
```

For a published release, pin the package:

```toml
[mcp_servers.aegis]
command = "uvx"
args = [
  "--from",
  "aegis-foundation==0.1.0",
  "aegis-mcp-server",
  "--default-target-dir",
  ".",
  "--transport",
  "stdio",
]
```

## Claude MCP Config

Use `.mcp.json` in a target project:

```json
{
  "mcpServers": {
    "aegis": {
      "command": "uvx",
      "args": [
        "--from",
        "./dist/aegis_foundation-0.1.0-py3-none-any.whl",
        "aegis-mcp-server",
        "--default-target-dir",
        ".",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

For a published release, replace the wheel path with `aegis-foundation==0.1.0`.

## Generic MCP Client Config

Any stdio MCP client can use the same command shape:

```json
{
  "name": "aegis",
  "transport": "stdio",
  "command": "uvx",
  "args": [
    "--from",
    "./dist/aegis_foundation-0.1.0-py3-none-any.whl",
    "aegis-mcp-server",
    "--default-target-dir",
    ".",
    "--transport",
    "stdio"
  ]
}
```

## Expected MCP Surfaces

Release-candidate validation must discover:

- tools: `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.kickoff`, `aegis.log`, `aegis.status`, and related V1 tools
- resources: Aegis contract, schema, current work, and runtime metadata resources
- prompts: advisory prompts for planning and workflow handoff

The MCP server is allowed to inspect and plan in read-only mode. Applying installation changes still requires the explicit install/apply path exposed by the Aegis tools. Starting work uses `aegis.kickoff` with `apply=true`; it creates `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and a full active work-tracking scaffold rendered from `.aegis/templates/workflow/`. After a task-scoped mutation, installed Claude `PostToolUse` hooks create `.aegis/state/pending-tracking.json`; `aegis.log` with `apply=true` records the required S:W:H:E entry in `sessions/current`, the active `TRACKER.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `HANDOFF.md`, and current plan evidence before the next mutation or session stop is allowed.

## Release Readiness Rule

Do not call the MCP publicly ready until these checks pass from an installed artifact outside the source repository:

- `aegis --version`
- `aegis inspect --target-dir .`
- `aegis plan-install --target-dir . --primary-agent claude --agent claude`
- `aegis install --target-dir . --primary-agent claude --agent claude --apply`
- `aegis status --target-dir .`
- `aegis verify --target-dir .`
- `aegis kickoff --target-dir . --task 1 --slug first-task --title "First Task"`
- `aegis log --target-dir . --handler claude-live-write --evidence docs/ai/work-tracking/active/<folder>/reports/<slug>/result.txt --note "Recorded task result evidence"`
- `./.aegis/bin/aegis log --target-dir . --handler claude-live-write --evidence docs/ai/work-tracking/active/<folder>/reports/<slug>/result.txt --note "Recorded task result evidence"` when the global `aegis` command is unavailable.
- `aegis-mcp-server --default-target-dir . --describe-config`
- stdio tool/resource/prompt discovery
