# Aegis MCP Client Setup

This guide documents the native MCP registration path for Aegis Foundation. Use it with the distribution contract in `docs/aegis/distribution.md` and the release verification matrix in `docs/aegis/release-verification-matrix.md`.

## Public Claude Registration

The public Claude path is:

```bash
aegis mcp register claude
```

This delegates to Claude's native MCP registration command and defaults to user scope, package mode, project-local uv cache/tool dirs, and `--default-target-dir .`. Use `aegis mcp generate-registration`, `aegis mcp execute-registration`, and `aegis mcp verify-registration` for advanced debugging, pinned versions, local wheels, or source checkouts.

## Default Install Model

Native MCP client registration is the primary path. A user should not need to clone this repository, copy JSON snippets, or edit `.mcp.json` by hand.

The model is:

1. Register the packaged Aegis MCP server with the native client.
2. Start a fresh project in Claude, Codex, or another MCP client.
3. Use the discovered `aegis.*` MCP tools to install the project-local runtime.
4. Use `aegis.status`, `aegis.next`, `aegis.start`, `aegis.kickoff`, `aegis.log`, `aegis.verify`, `aegis.closeout_ready`, and `aegis.closeout` for Aegis workflow state.
5. Use the agent's native tools for normal project implementation work such as reading files, editing source, running tests, and inspecting git status.

The project-local runtime installed by Aegis includes `.aegis/`, `.claude/` hooks, `CLAUDE.md`, sessions, plans, work-tracking scaffolding, readiness gates, pending S:W:H:E tracking, and closeout gates. Taskmaster and Serena are optional integrations; Aegis must work without them.

MCP is the bootstrap and control-plane interface. It installs and operates the workflow, but it is not a replacement for the agent's normal editor, shell, test runner, or git inspection workflow. The installed runtime enforces behavior around all supported mutation surfaces after installation.

Claude Code reads `.claude/settings.json` when a session starts. If `aegis.init` or `aegis.install` creates or changes Claude hooks, the MCP tool returns `ok=false`, `error.code=client_reload_required`, `error.status=blocked`, and `details.must_stop=true` even though the install itself was applied and preserved under `details.report`. Aegis writes `.aegis/state/client-reload-required.json` and blocks `aegis.start` / `aegis.kickoff` until a restarted Claude session runs the installed `PreToolUse` hook and clears that marker. Treat this as a hard stop: the current Claude session must not edit source, run project verification, mutate Taskmaster, or call start/kickoff. Restart Claude in the project. After restart, run `aegis.next` and continue with start/kickoff, scope logging, native edits, verification, closeout, doctor, and only then Taskmaster completion if Taskmaster is in use.

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

- tools: `aegis.inspect`, `aegis.status`, `aegis.next`, `aegis.plan_install`, `aegis.install`, `aegis.verify`, `aegis.closeout_ready`, `aegis.closeout`, `aegis.start`, `aegis.kickoff`, `aegis.log`, `aegis.list_profiles`, and `aegis.explain_profile`
- resources: Aegis contract, schema, current work, verification, closeout, and runtime metadata resources
- prompts: advisory prompts for bootstrap, migration, verification, session prep, and handoff

The MCP server is allowed to inspect and plan in read-only mode. Applying installation changes still requires explicit `aegis.install` with apply semantics. Starting standalone local work uses `aegis.start`; it allocates a local Aegis task id, creates `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and a full active work-tracking scaffold rendered from packaged `.aegis/templates/workflow/`. When `.taskmaster/tasks/tasks.json` has available numeric work, `aegis.next` should direct the agent to run `task-master next` and `task-master show <id>` or read-only Taskmaster MCP discovery (`help`, `get_tasks`, `next_task`, `get_task`), then call `aegis.kickoff apply=true` with that numeric id. In that state, `aegis.start` refuses to allocate a competing local Aegis task.

For installed Claude projects, `aegis.start` and `aegis.kickoff` are readiness bootstrap operations only after the reload marker is cleared. The hooks allow those two operations before readiness is READY so agents can create the missing task branch and workflow scaffold. Read-only Taskmaster MCP discovery is also allowed before kickoff so agents can find the external numeric task. Other mutating MCP or CLI operations, such as `aegis.verify`, Taskmaster MCP mutations, unknown Taskmaster MCP tools, and source edits, remain blocked until readiness passes.

After a task-scoped mutation, installed Claude `PostToolUse` hooks create `.aegis/state/pending-tracking.json`; `aegis.log` with apply semantics can consume that event with `pending_event_id=current` and `plan_step=auto`, then records the required S:W:H:E entry in `sessions/current`, the active `TRACKER.md`, and event-aware canonical surfaces before the next mutation or session stop is allowed. Scope logs default to findings/decisions/handoff; implementation and verification logs default to implementation/changelog/handoff. Plan evidence is updated only when `plan_step` is supplied explicitly or `auto` can infer the step deterministically.

After final Aegis closeout, the installed hooks keep normal mutations blocked but allow the matching Taskmaster completion bookkeeping path: `task-master set-status --id=<task-id> --status=done` or the Taskmaster MCP equivalent, followed by `task-master generate` when no targeted generated-file helper exists. This is intentionally narrow; source edits, Git mutations, non-bootstrap Aegis mutations, and mismatched Taskmaster ids remain blocked once current work is completed.

Expected tool split:

- Aegis MCP or the project-local CLI: inspect, status, next, plan_install/plan-install, install, start, kickoff for explicit external numeric task ids, log, verify, closeout_ready/closeout --dry-run, closeout, and future reconciliation.
- Taskmaster CLI/MCP when present: read-only next/show discovery before Aegis kickoff, and set-status done only after Aegis closeout plus read-only doctor pass. For Taskmaster MCP, the pre-kickoff discovery allowlist is `help`, `get_tasks`, `next_task`, and `get_task`; mutation and unknown Taskmaster MCP tools remain blocked.
- Taskmaster generated files: refresh after set-status done with the project helper when present; otherwise run broad `task-master generate` deliberately and report that broad refresh was used.
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
- `aegis.inspect`, `aegis.status`, `aegis.next`, `aegis.install`, `aegis.start`, `aegis.kickoff`, `aegis.log`, `aegis.verify`, `aegis.closeout_ready`, and `aegis.closeout` from a fresh target project
- `aegis-mcp-server --default-target-dir . --describe-config` reporting `"asset_origin": "package"`
