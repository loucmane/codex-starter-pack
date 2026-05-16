# Aegis MCP Wrapper Contract

## Summary

Task 109 does not ship a production MCP server.

This document defines the contract for a future Aegis MCP wrapper over the deterministic library/CLI core implemented in `scripts/_aegis_installer.py` and exposed by `python3 scripts/codex-task aegis ...`.

The MCP wrapper must not duplicate installer logic. It should import or otherwise call the same core operations used by the CLI:

- `inspect_project`
- `plan_install`
- `install`
- `verify`
- `list_profiles`
- `explain_profile`

Future update and rollback tools must extend that same library first, then expose MCP wrappers around it.

## Design Rules

- MCP is an agent-facing control plane, not the source of truth.
- CLI/library behavior is the source of truth for planning, applying, verifying, reporting, cleanup, and tests.
- Read-only tools may be callable freely by agent sessions.
- Mutating tools require explicit apply semantics.
- No MCP tool may silently select agents; it must pass explicit `primary_agent` and enabled `agents` values into the core.
- MCP tools must return structured reports equivalent to the CLI JSON payloads.
- MCP resources expose current Aegis state so agents do not guess paths.
- MCP prompts guide workflows, but prompts are not gates or evidence.
- Shared foundation state stays under `.aegis/`.
- Adapter-specific files keep their adapter names: `CODEX.md`, `.codex/`, `scripts/codex-*`, `CLAUDE.md`, and `.claude/`.

## V1-Backed Tools

These tools can be implemented directly over the Task 109 V1 core:

| MCP tool | CLI/core mapping | Mutates target | Apply gate | Status |
| --- | --- | --- | --- | --- |
| `aegis.inspect` | `inspect_project` / `python3 scripts/codex-task aegis inspect` | no | none | V1-backed |
| `aegis.plan_install` | `plan_install` / `python3 scripts/codex-task aegis plan-install` | no | none | V1-backed |
| `aegis.install` | `install` / `python3 scripts/codex-task aegis install` | yes when apply=true | `apply=true` required | V1-backed |
| `aegis.verify` | `verify` / `python3 scripts/codex-task aegis verify` | yes, because V1 writes verification reports and manifest verification state | explicit caller acknowledgement | V1-backed |
| `aegis.list_profiles` | `list_profiles` / `python3 scripts/codex-task aegis list-profiles` | no | none | V1-backed |
| `aegis.explain_profile` | `explain_profile` / `python3 scripts/codex-task aegis explain-profile` | no | none | V1-backed |

### `aegis.inspect`

Purpose: report target repository Aegis state and adapter signals.

Input:

```json
{
  "target_dir": ".",
  "profile": "generic"
}
```

Output schema: structured inspect payload from `inspect_project`.

Evidence expectations:

- Does not write `.aegis/`.
- Does not create reports.
- May be used by prompts before install planning.

### `aegis.plan_install`

Purpose: produce a dry-run install plan for a target repository.

Input:

```json
{
  "target_dir": ".",
  "profile": "generic",
  "primary_agent": "claude",
  "agents": ["claude"]
}
```

Output schema: `schemas/aegis/install-plan.schema.json`.

Evidence expectations:

- Does not mutate the target repository.
- Classifies operations as `create`, `modify`, `skip`, `conflict`, or `manual-review`.
- Records explicit agent selection in `agent_selection`.
- Uses `.aegis/foundation-manifest.json` as the expected manifest path.

### `aegis.install`

Purpose: apply the generic-profile install plan when explicitly requested.

Input:

```json
{
  "target_dir": ".",
  "profile": "generic",
  "primary_agent": "claude",
  "agents": ["claude"],
  "apply": true
}
```

Output schema: install report shape returned by `install`.

Apply gate:

- `apply` must be `true`.
- The wrapper must reject or dry-run when `apply` is absent or false.
- The wrapper must surface unsafe operations instead of retrying with overwrite behavior.

Refusal semantics:

- Existing differing files are `manual-review`.
- Directory/file collisions are `conflict`.
- Unsafe operations return `status=refused`.
- Apply-time write failure returns `status=failed` with cleanup details.

Evidence expectations:

- Writes `.aegis/foundation-manifest.json`.
- Writes `.aegis/contract.md`.
- Writes `.aegis/reports/install-plan.json`.
- Writes `.aegis/reports/install-report.json`.
- Writes selected adapter files only for enabled adapters.
- Does not write `.codex/foundation-manifest.json`.

### `aegis.verify`

Purpose: verify an installed Aegis target repository.

Input:

```json
{
  "target_dir": "."
}
```

Output schema: verification report shape returned by `verify`.

Mutation note:

V1 verification writes `.aegis/reports/verification-report.json` and updates the manifest verification section on pass. MCP clients should treat this as a mutating tool even though it is a verification operation.

Evidence expectations:

- Validates `.aegis/foundation-manifest.json` against `schemas/aegis/foundation-manifest.schema.json`.
- Checks required gate files and hook registration.
- Fails when required gates are missing, non-executable, or unconfigured.
- Reports optional policy-only checks as unsupported rather than proof of enforcement.

### `aegis.list_profiles`

Purpose: list built-in Aegis profiles known to the runtime.

Input:

```json
{}
```

Output schema: profile list payload with `generic` as the V1 profile.

### `aegis.explain_profile`

Purpose: return the profile contract for a single profile.

Input:

```json
{
  "profile": "generic"
}
```

Output schema: `schemas/aegis/profile.schema.json`.

## Future/Deferred Tools

These names are reserved, but implementation is deferred until the library has the corresponding deterministic core behavior:

| MCP tool | Required future core behavior | Mutates target | Status |
| --- | --- | --- | --- |
| `aegis.status` | installed-state summary and latest report index | no | future/deferred |
| `aegis.plan_update` | version comparison and safe update planning | no | future/deferred |
| `aegis.update` | update application with conflict handling and checkpointing | yes | future/deferred |
| `aegis.rollback` | checkpoint restoration and post-rollback verification | yes | future/deferred |

Deferred mutating tools must use explicit apply semantics and must not run from prompt text alone.

## MCP Resources

The MCP server should expose resources backed by `.aegis/` state and current library output:

| Resource URI | Backing source | Status |
| --- | --- | --- |
| `aegis://contract/current` | `.aegis/contract.md` | V1-backed after install |
| `aegis://profiles` | `list_profiles` | V1-backed |
| `aegis://profiles/{name}` | `explain_profile` | V1-backed for `generic` |
| `aegis://install-plan/latest` | `.aegis/reports/install-plan.json` or latest planned payload | V1-backed after plan/install |
| `aegis://verification/latest` | `.aegis/reports/verification-report.json` | V1-backed after verify |
| `aegis://limitations` | manifest policy/unsupported gates plus deferred follow-up list | V1-backed after install |
| `aegis://managed-files` | manifest `managed_files` | V1-backed after install |
| `aegis://project/status` | `inspect_project` plus manifest verification state | future/deferred alias for `aegis.status` |

Resource rules:

- Resources are read-only.
- Missing backing files should return structured `not_installed` or `not_available` states, not stack traces.
- Resources must not mutate `.aegis/`.

## MCP Prompts

Prompts are workflow guidance only. They must call tools or instruct the user to call tools; they are not gates.

| Prompt | Purpose | Required tool flow |
| --- | --- | --- |
| `aegis.bootstrap_new_project` | Guide install into a new repository | `aegis.inspect` -> `aegis.plan_install` -> user approval -> `aegis.install` -> `aegis.verify` |
| `aegis.migrate_existing_project` | Guide install into a repo with existing files | `aegis.inspect` -> `aegis.plan_install` -> resolve conflicts -> user approval -> `aegis.install` -> `aegis.verify` |
| `aegis.verify_runtime` | Check an installed Aegis runtime | `aegis.inspect` -> `aegis.verify` -> read `aegis://verification/latest` |
| `aegis.prepare_agent_session` | Prepare an agent to work inside an installed repo | read `aegis://contract/current`, `aegis://project/status`, and `aegis://limitations` |
| `aegis.close_agent_session` | Prepare evidence handoff | `aegis.verify` and read latest reports |
| `aegis.install_claude_adapter` | Add or verify Claude adapter surfaces | future flow over install/update planning |
| `aegis.install_codex_adapter` | Add or verify Codex adapter surfaces | future flow over install/update planning |

Prompt rules:

- Prompts must not claim success without tool evidence.
- Prompts must not instruct direct writes to `.aegis/`.
- Prompts must distinguish policy-only limitations from mechanical gates.

## Schema Alignment

The MCP wrapper must reuse the Task 109 schema contracts:

- `schemas/aegis/foundation-manifest.schema.json`
- `schemas/aegis/profile.schema.json`
- `schemas/aegis/install-plan.schema.json`

Tool output alignment:

- `aegis.plan_install` returns `install-plan.schema.json`.
- `aegis.explain_profile` returns `profile.schema.json`.
- `aegis.install` writes `foundation-manifest.schema.json` conforming state and returns an install report.
- `aegis.verify` reads and validates `foundation-manifest.schema.json` conforming state and returns a verification report.

Future production MCP implementation should add formal JSON schemas for install reports, verification reports, update plans, rollback plans, and status resources once those shapes stabilize.

## Error Semantics

The wrapper should preserve core statuses:

| Core status | MCP result |
| --- | --- |
| `applied` | success |
| `passed` | success |
| `failed` | tool error with structured report |
| `refused` | tool error with unsafe operations report |
| `unsupported` optional checks | success with limitation metadata unless required |

MCP tool errors must include the structured report payload when possible so agents can write accurate findings and decisions without rerunning commands.

## Evidence Outputs

MCP calls should surface the same evidence paths as CLI calls:

- `.aegis/foundation-manifest.json`
- `.aegis/reports/install-plan.json`
- `.aegis/reports/install-report.json`
- `.aegis/reports/verification-report.json`
- `.aegis/contract.md`

Task/session work-tracking evidence remains outside the installed target unless the target project has its own workflow tracking enabled.

## Follow-Up Tasks

Task 109 V1 closes with the MCP contract only. Follow-up tasks should be created or refined for:

1. Production Aegis MCP server wrapper over `scripts/_aegis_installer.py`.
2. Expanded profile implementation beyond `generic`.
3. Update planning and update application.
4. Full rollback checkpoint creation and restoration.
5. Packaging and distribution for installing Aegis into arbitrary projects.
6. Optional CI installation templates.
7. Cross-agent smoke automation for installed Claude and Codex adapters.
8. Hosted or long-running service infrastructure, only if future usage proves it is needed.

## Non-Goals For Task 109

- Do not implement a production MCP server.
- Do not implement update or rollback tools.
- Do not implement package publishing.
- Do not add hosted infrastructure.
- Do not make MCP mandatory for Aegis installation.
- Do not create a second installer path that diverges from the CLI/library core.

## Acceptance

The MCP wrapper contract is sufficient for Task 109 when:

- All documented tool names use `aegis.*`.
- All documented resource URIs use `aegis://...`.
- V1-backed tools are separated from future/deferred tools.
- Mutating tools require explicit apply semantics.
- Schemas reference `schemas/aegis/`.
- The production MCP server remains explicitly deferred.
- Evidence/handoff identify follow-up tasks for the deferred production work.
