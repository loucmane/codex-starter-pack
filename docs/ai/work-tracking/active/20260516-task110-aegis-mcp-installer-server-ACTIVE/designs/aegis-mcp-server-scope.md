# Aegis MCP Server Scope

## Purpose
Task 110 turns the Task 109 Aegis installer contract into an actual MCP server. The server must be a thin, testable wrapper over `scripts/_aegis_installer.py`; it must not duplicate installer logic or create a second source of truth.

## Source Of Truth
- Installer core: `scripts/_aegis_installer.py`
- Schemas: `schemas/aegis/foundation-manifest.schema.json`, `schemas/aegis/profile.schema.json`, `schemas/aegis/install-plan.schema.json`
- Prior contract: `docs/ai/work-tracking/archive/20260515-task109-foundation-installer-mcp-COMPLETED/designs/aegis-mcp-wrapper-contract.md`
- Agent compatibility context: `templates/registry/agent-compatibility-matrix.json`

## V1 Tools
- `aegis.inspect`: read-only target inspection.
- `aegis.plan_install`: read-only plan generation; explicit profile, primary agent, and agents required.
- `aegis.install`: mutating only with explicit `apply: true`; missing or false apply returns a structured refusal.
- `aegis.verify`: writes verification report only when the caller explicitly acknowledges the report write.
- `aegis.list_profiles`: read-only profile discovery.
- `aegis.explain_profile`: read-only profile explanation validated against the profile schema.

Do not register `aegis.status`, `aegis.plan_update`, `aegis.update`, or `aegis.rollback` as production tools until deterministic core support exists.

## Resources
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

Resources are read-only. Missing target state returns structured `not_installed` or `not_available` payloads.

## Prompts
- `aegis.bootstrap_new_project`
- `aegis.migrate_existing_project`
- `aegis.verify_runtime`
- `aegis.prepare_agent_session`
- `aegis.close_agent_session`

Prompts guide agents through inspect, plan, user approval, install, and verify. They are not gates, do not count as evidence, and must not claim success without tool output.

## Subtask Sequence
1. `110.1`: scaffold `aegis_mcp` package, server factory, and stdio entrypoint.
2. `110.2`: register V1-backed tools and formal input schemas.
3. `110.3`: wire handlers to the installer core with validation and structured errors.
4. `110.4`: expose read-only resources and workflow prompts.
5. `110.5`: update docs/config guidance and add local smoke coverage.

## Verification Expectations
- Unit tests for registration and schema surfaces.
- Handler tests using isolated temp projects.
- Resource and prompt discovery tests.
- Local stdio MCP smoke test that calls the server without shelling into `scripts/codex-task`.
- Existing Aegis schema, installer, fixture, and contract tests stay green.
