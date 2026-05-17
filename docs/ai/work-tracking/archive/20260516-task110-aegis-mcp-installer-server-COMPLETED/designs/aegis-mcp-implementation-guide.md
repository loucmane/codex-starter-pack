# Aegis MCP Implementation Guide

## Summary

Task 110 ships the first production Aegis MCP server for this repository.

The server is a thin MCP wrapper over the deterministic installer core in `scripts/_aegis_installer.py`. It must not duplicate installer logic, does not create a second installer path, and does not ask agents to write `.aegis/` directly.

## Entrypoint

- Package: `aegis_mcp`
- Server module: `aegis_mcp/server.py`
- Local stdio entrypoint: `scripts/aegis-mcp-server`
- Default transport: `stdio`
- Config smoke command: `python3 scripts/aegis-mcp-server --describe-config`
- Direct stdio smoke path: launch `scripts/aegis-mcp-server` through the Python MCP SDK `stdio_client`, initialize a `ClientSession`, then list tools, resources, and prompts.

## MCP Config

Project-local `.mcp.json` includes the Aegis server alongside the existing Taskmaster and Serena entries:

```json
{
  "mcpServers": {
    "aegis": {
      "type": "stdio",
      "command": "python3",
      "args": ["scripts/aegis-mcp-server"]
    }
  }
}
```

The entrypoint accepts optional path overrides:

```bash
python3 scripts/aegis-mcp-server \
  --source-root /path/to/aegis/source \
  --default-target-dir /path/to/target
```

`--source-root` selects the repository containing Aegis source assets and schemas. `--default-target-dir` is used by read-only resources such as `aegis://manifest/current`; mutating tools still require explicit `target_dir` arguments.

## Supported Tools

The server registers exactly the V1-backed tools implemented by `scripts/_aegis_installer.py`:

| Tool | Core mapping | Mutates target | Required safety input |
| --- | --- | --- | --- |
| `aegis.inspect` | `inspect_project` | no | `target_dir` |
| `aegis.plan_install` | `plan_install` | no | `target_dir`, `primary_agent`, `agents` |
| `aegis.install` | `install` | yes when `apply=true` | `target_dir`, `profile`, `primary_agent`, `agents`, `apply=true` |
| `aegis.verify` | `verify` | yes, writes verification reports and may update manifest verification state | `target_dir`, `acknowledge_report_write=true` |
| `aegis.list_profiles` | `list_profiles` | no | none |
| `aegis.explain_profile` | `explain_profile` | no | `profile`, default `generic` |

Deferred tools are intentionally not registered as production tools until deterministic core support exists:

- `aegis.status`
- `aegis.plan_update`
- `aegis.update`
- `aegis.rollback`

## Tool Response Format

Successful calls use a stable envelope:

```json
{
  "ok": true,
  "schema_version": "1.0.0",
  "tool": "aegis.plan_install",
  "read_only": true,
  "result": {}
}
```

Predictable refusals and failures use structured errors:

```json
{
  "ok": false,
  "schema_version": "1.0.0",
  "tool": "aegis.install",
  "error": {
    "code": "install_refused",
    "message": "Unsafe overwrite or manual-review operation present.",
    "status": "refused",
    "details": {
      "report": {}
    }
  }
}
```

Mapped predictable errors include invalid Aegis inputs, core `AegisError`, schema validation failures, `apply=false`, `acknowledge_report_write=false`, refused installs, failed applies, and failed verifies.

## Resources

The server exposes read-only JSON-envelope resources:

- `aegis://manifest/current`
- `aegis://contract/current`
- `aegis://schemas/foundation-manifest`
- `aegis://schemas/profile`
- `aegis://schemas/install-plan`
- `aegis://profiles`
- `aegis://profiles/{name}`
- `aegis://install-plan/latest`
- `aegis://verification/latest`
- `aegis://limitations`
- `aegis://managed-files`

Missing target state returns structured `not_installed` or `not_available` payloads. Resource reads must never create or update `.aegis/`.

`aegis://install-plan/latest` first returns the in-process plan cache populated by `aegis.plan_install`, then falls back to `.aegis/reports/install-plan.json` when a report exists.

## Schema Alignment

The MCP server reuses the Aegis schema contracts from Task 109:

- `schemas/aegis/foundation-manifest.schema.json`
- `schemas/aegis/profile.schema.json`
- `schemas/aegis/install-plan.schema.json`

`aegis.plan_install` validates install plans against `schemas/aegis/install-plan.schema.json`. `aegis.explain_profile` validates profile payloads against `schemas/aegis/profile.schema.json`. Installed manifests are still produced and verified by the shared core against `schemas/aegis/foundation-manifest.schema.json`.

## Prompts

Prompts are advisory workflow helpers. They are never gates and never evidence.

- `aegis.bootstrap_new_project`
- `aegis.migrate_existing_project`
- `aegis.verify_runtime`
- `aegis.prepare_agent_session`
- `aegis.close_agent_session`

Prompt invariants:

- Preserve the flow `aegis.inspect` -> `aegis.plan_install` -> user approval -> `aegis.install` -> `aegis.verify`.
- Cite resources such as `aegis://contract/current`, `aegis://limitations`, and `aegis://verification/latest`.
- Distinguish mechanical gates from policy-only limitations.
- Never instruct direct writes to `.aegis/`.
- Never claim success without tool/report evidence.

## Safety Contract

- `.aegis/` is shared foundation state.
- Agents may read `.aegis/` through resources.
- Agents must not write `.aegis/` directly.
- Mutating operations go through `aegis.install` or `aegis.verify` with explicit acknowledgement fields.
- `aegis.install apply=false` returns a structured refusal and does not call the core installer.
- `aegis.verify acknowledge_report_write=false` returns a structured refusal and does not call the core verifier.
- Prompts and memories are continuity aids, not evidence.

## Test Coverage

Task 110 validates the server with focused pytest coverage:

- Tool discovery and formal input schema checks.
- Core handler wiring over temporary targets.
- Structured refusal and failure mapping.
- Read-only resources for installed and not-installed targets.
- Prompt invariant checks.
- Direct stdio MCP smoke test that launches `scripts/aegis-mcp-server` without shelling through `scripts/codex-task`.

Evidence is stored under `docs/ai/work-tracking/active/20260516-task110-aegis-mcp-installer-server-ACTIVE/reports/aegis-mcp-installer-server/`.
