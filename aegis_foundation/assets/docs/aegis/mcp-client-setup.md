# Aegis MCP Client Setup

This guide documents the native MCP registration path for Aegis Foundation. Use it with the distribution contract in `docs/aegis/distribution.md` and the release verification matrix in `docs/aegis/release-verification-matrix.md`.

## Default Install Model

Native MCP client registration is the primary path. A user should not need to clone this repository, copy JSON snippets, or edit `.mcp.json` by hand.

The model is:

1. Register the packaged Aegis MCP server with the native client.
2. Start a fresh project in Claude, Codex, or another MCP client.
3. Use the discovered `aegis.*` MCP tools to install the project-local runtime.
4. Use `aegis.status`, `aegis.next`, `aegis.kickoff`, `aegis.log`, `aegis.verify`, `aegis.closeout_ready`, and `aegis.closeout` for Aegis workflow state.
5. Use the agent's native tools for normal project implementation work such as reading files, editing source, running tests, and inspecting git status.

The project-local runtime installed by Aegis includes `.aegis/`, `.claude/` hooks, `CLAUDE.md`, sessions, plans, work-tracking scaffolding, readiness gates, pending S:W:H:E tracking, and closeout gates. Taskmaster and Serena are optional integrations; Aegis must work without them.

MCP is the bootstrap and control-plane interface. It installs and operates the workflow, but it is not a replacement for the agent's normal editor, shell, test runner, or git inspection workflow. The installed runtime enforces behavior around all supported mutation surfaces after installation.

## Native Registration Commands

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

The registered server command uses package assets by default. It must not depend on `/home/loucmane/codex` or any local source checkout.

## Generate Commands

Use Aegis to generate deterministic registration payloads:

```bash
aegis mcp generate-registration --client claude --scope user
aegis mcp generate-registration --client claude --scope project
aegis mcp generate-registration --client codex
```

The repo-local development wrapper exposes the same contract:

```bash
python3 scripts/codex-task aegis mcp generate-registration --client claude --scope user
python3 scripts/codex-task aegis mcp generate-registration --client codex
```

Generation is read-only and returns JSON containing the client, scope, server name, source mode, package spec, generated argv, rendered command, target directory, transport, and safety notes.

## Execute Registration

After reviewing the generated command, Aegis can execute the native client command:

```bash
aegis mcp execute-registration --client claude --scope user
aegis mcp execute-registration --client codex
```

Execution calls the native client with an argv list and never uses `shell=True`. If the requested client is missing, Aegis returns structured `missing_client` JSON and does not write MCP config files.

## Verify Registration

Verify the native client registration:

```bash
aegis mcp verify-registration --client claude --scope user
aegis mcp verify-registration --client codex
```

Verification inspects the native client registration and checks that:

- the `aegis` server exists
- the command uses `uvx`
- the command includes `--from <source>`
- the command starts `aegis-mcp-server`
- the command includes `--default-target-dir`
- the command includes `--transport stdio`

## Source Modes

Package mode is the default:

```bash
aegis mcp generate-registration --client claude --scope user --source-mode package
```

Pinned package mode:

```bash
aegis mcp generate-registration --client claude --scope user --source-mode pinned --package-version 0.1.0
```

GitHub URL/ref mode:

```bash
aegis mcp generate-registration --client claude --scope user --source-mode github --github-ref v0.1.0
```

Local wheel mode:

```bash
aegis mcp generate-registration --client claude --scope user --source-mode wheel --artifact "$PWD/dist/aegis_foundation-0.1.0-py3-none-any.whl"
```

Wheel and source modes validate the local path and render an absolute `uvx --from` value so the native MCP client can run from fresh project folders without depending on the shell's original current directory.

Source checkout mode, for development only:

```bash
aegis mcp generate-registration --client claude --scope user --source-mode source --artifact /path/to/codex
```

Source checkout mode is explicit. Public/fresh-project instructions should use package, pinned package, GitHub artifact, or wheel modes.

## Expected MCP Surfaces

Native registration must discover:

- tools: `aegis.inspect`, `aegis.status`, `aegis.next`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.closeout_ready`, `aegis.closeout`, `aegis.kickoff`, `aegis.log`, `aegis.list_profiles`, and `aegis.explain_profile`
- resources: Aegis contract, schema, current work, verification, closeout, and runtime metadata resources
- prompts: advisory prompts for bootstrap, migration, verification, session prep, and handoff

The MCP server is allowed to inspect and plan in read-only mode. Applying installation changes still requires explicit `aegis.install` with apply semantics. Starting work uses `aegis.kickoff`; it creates `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and a full active work-tracking scaffold rendered from packaged `.aegis/templates/workflow/`.

After a task-scoped mutation, installed Claude `PostToolUse` hooks create `.aegis/state/pending-tracking.json`; `aegis.log` with apply semantics can consume that event with `pending_event_id=current` and `plan_step=auto`, then records the required S:W:H:E entry in `sessions/current`, the active `TRACKER.md`, and event-aware canonical surfaces before the next mutation or session stop is allowed. Scope logs default to findings/decisions/handoff; implementation and verification logs default to implementation/changelog/handoff. Plan evidence is updated only when `plan_step` is supplied explicitly or `auto` can infer the step deterministically.

Expected tool split:

- Aegis MCP or the project-local CLI: inspect, status, next, plan_install/plan-install, install, kickoff, log, verify, closeout_ready/closeout --dry-run, closeout, and future reconciliation.
- Native agent tools: source reads and edits, project test commands, and git status/diff inspection.
- Installed hooks: enforcement across supported mutation surfaces regardless of whether a mutation attempt comes from MCP, Bash, Edit, Write, or another supported tool.

## Fallback Config Files

Manual `.mcp.json` or Codex config edits are fallback-only. Use them only when the native client command is unavailable or broken, and record the limitation in release evidence.

Generic stdio MCP config shape:

```json
{
  "name": "aegis",
  "transport": "stdio",
  "command": "uvx",
  "args": [
    "--from",
    "aegis-foundation==0.1.0",
    "aegis-mcp-server",
    "--default-target-dir",
    ".",
    "--transport",
    "stdio"
  ]
}
```

Fallback snippets are not the happy path and must not replace native `claude mcp add` / `codex mcp add` coverage.

## Release Readiness Rule

Do not call the MCP publicly ready until these checks pass from an installed artifact outside the source repository:

- `aegis --version`
- `aegis mcp generate-registration --client claude --scope user`
- `aegis mcp generate-registration --client claude --scope project`
- `aegis mcp generate-registration --client codex`
- `aegis mcp execute-registration --client claude --scope user` or equivalent fake-client test in CI
- `aegis mcp verify-registration --client claude --scope user` or equivalent fixture/parser test in CI
- native client tool/resource/prompt discovery for the registered Aegis MCP server
- `aegis.inspect`, `aegis.status`, `aegis.next`, `aegis.install`, `aegis.kickoff`, `aegis.log`, `aegis.verify`, `aegis.closeout_ready`, and `aegis.closeout` from a fresh target project
- `aegis-mcp-server --default-target-dir . --describe-config` reporting `"asset_origin": "package"`
