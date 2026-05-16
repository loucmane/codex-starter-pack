# Aegis Foundation Installer and MCP Architecture

## Summary

Task 109 turns the completed Codex starter-pack foundation into **Aegis Foundation**: a portable, agent-neutral system that can be installed, verified, updated, and audited in other projects.

The chosen architecture is a deterministic CLI/library core with an optional MCP wrapper.

The CLI/library owns the real behavior: project inspection, install planning, file application, verification, update, rollback, reports, and fixtures. The MCP server is an agent-facing control plane over that same core. This keeps Aegis usable by Codex, Claude, humans, CI, and future agents without depending on any single MCP client.

## Naming Decision

The shared installed runtime is named **Aegis Foundation**.

Installed projects use an agent-neutral control directory:

```text
.aegis/
  foundation-manifest.json
  reports/
  state/
```

Naming boundaries:

- `Aegis Foundation` is the shared portable runtime.
- `.aegis/` stores shared foundation state, manifests, reports, and future runtime state.
- `CODEX.md`, `.codex/`, and `scripts/codex-*` remain Codex adapter surfaces.
- `CLAUDE.md` and `.claude/` remain Claude adapter surfaces.
- Future Gemini or other agent adapters should be represented in the Aegis manifest as adapters, not as separate foundations.

This replaces the earlier `.codex/foundation-manifest.json` assumption. Codex remains one supported adapter; it does not own the whole foundation.

## Agent Selection Model

Aegis installation must ask which agent setup the project uses instead of assuming Codex-first defaults.

V1 install UX should support:

```text
primary agent: claude | codex | gemini | multi | none
additional agents: claude, codex, gemini, future adapters
```

Default recommendation for a new generic install: **Claude as the primary agent**.

Rationale:

- Aegis is agent-neutral, but real installed projects need a primary adapter so entrypoints and gates are concrete.
- Claude has a proven hook-based gate model, so a Claude-primary install can mechanically block cold-session mutations through PreToolUse hooks.
- Codex remains a first-class adapter and can be installed alongside Claude, but Codex should not be assumed as the default for new Aegis installs.
- Multi-agent installs are supported by enabling multiple adapter sections in the manifest and requiring the gates for each enabled adapter.

Non-interactive installs should require explicit flags instead of silently choosing an agent:

```text
python3 scripts/codex-task aegis install --profile generic --primary-agent claude --agent claude --apply
python3 scripts/codex-task aegis install --profile generic --primary-agent multi --agent claude --agent codex --apply
```

The selected primary agent and enabled adapters must be recorded in `.aegis/foundation-manifest.json`.

## Access and Gate Contract

Aegis must be a system that agents can use mechanically, not a set of notes they need to remember.

Installed projects expose `.aegis/` as the shared foundation contract:

- Agents may read `.aegis/` directly to understand the installed runtime.
- Agents must not write `.aegis/` directly.
- Mutating foundation operations must go through the Aegis CLI or future MCP wrapper.
- The manifest must identify the installed entrypoints, selected agents, enabled adapters, required gates, and allowed interfaces.

V1 write interface:

```text
python3 scripts/codex-task aegis install --apply
python3 scripts/codex-task aegis verify
```

Future MCP write interface:

```text
aegis.install
aegis.update
aegis.rollback
```

Gate records in the manifest must declare their enforcement type:

| Enforcement | Meaning | Example |
| --- | --- | --- |
| mechanical | The action is blocked at runtime if the gate fails | Claude PreToolUse mutation gate |
| verification | The action is detected by verification, guard, CI, or audit | `codex-guard validate`, work-tracking audit |
| policy | The limitation is documented but not mechanically enforceable yet | Unsupported MCP write surface |

Required gates are hard requirements. If a required gate is missing, not executable, not configured, or reports failure, `aegis verify` must fail.

For a Claude-enabled install, Aegis must install and verify the Claude hook runtime:

```text
CLAUDE.md
.claude/settings.json
.claude/scripts/readiness.sh
.claude/scripts/pretooluse-gate.sh
.claude/scripts/bash-command-guard.sh
.claude/scripts/codex-path-guard.sh
```

V1 verification should prove static hook presence and configuration. Live Claude smoke tests are valuable evidence when available, but the installed contract must not depend on a human remembering to ask Claude to behave correctly. The minimum requirement is that the manifest records Claude gates as required and `aegis verify` fails when those files or hook registrations are missing.

## V1 Scope Lock

Task 109 is narrowed to the Aegis installer contract plus CLI prototype.

V1 includes:

- Final architecture decision for CLI/library core plus optional MCP wrapper.
- Aegis foundation manifest schema.
- Aegis project profile schema.
- Aegis install-plan schema.
- Generic-profile CLI prototype for:
  - `inspect`
  - `plan-install`
  - `install`
  - `verify`
- Fixture tests proving install, verify, and idempotence for the generic profile.
- MCP contract documentation covering Aegis tools, resources, prompts, schemas, and read-only versus mutating behavior.

V1 excludes:

- Full production MCP server implementation.
- Full multi-profile support beyond schema and generic-profile implementation.
- Complex update migrations.
- Package publishing.
- Automatic CI installation into target projects.
- Hosted or long-running service infrastructure.

Deferred follow-up tasks:

- Build the production MCP server wrapper after the CLI core is stable.
- Harden update/rollback across multiple installed foundation versions.
- Expand project profiles beyond generic.
- Package and distribute the installer.
- Add optional CI installation templates and release workflow.

This scope keeps Task 109 concrete: prove the installer core with one profile and document the MCP contract before building the full MCP surface.

## Goals

- Install Aegis into greenfield and existing repositories without unsafe overwrites.
- Preserve deterministic behavior through a local library and CLI that can run in shell, CI, or tests.
- Document how the same behavior will be exposed through MCP tools, resources, and prompts for agent-friendly operation.
- Produce install reports that explain files created, modified, skipped, conflicted, and verified.
- Implement the generic profile first and define schema for future profiles.
- Make future update and rollback realistic by recording a versioned Aegis managed-file manifest.
- Prove portability through fixture repositories and idempotence tests for the generic profile.

## Non-Goals

- Do not make MCP the only way to install or update the foundation.
- Do not overwrite existing project files by default.
- Do not treat copied documentation as proof that a target repository is functional.
- Do not require a specific agent to use the installed foundation.
- Do not ship long-running hosted infrastructure for the first implementation slice.
- Do not implement the full MCP server before the CLI core is proven.
- Do not implement complex cross-version update migrations in V1.
- Do not attempt full multi-profile coverage in V1.

## Architecture Layers

| Layer | Responsibility | Primary Consumers |
| --- | --- | --- |
| Foundation library | Pure project inspection, planning, rendering, install/update/rollback operations, manifest handling, and verification orchestration | CLI, MCP server, tests |
| CLI | Deterministic command surface under `python3 scripts/codex-task aegis ...` | Codex, humans, CI |
| MCP server | Structured Aegis tools/resources/prompts that call the same library | Claude, Codex MCP clients, future agents |
| Agent adapters | `CODEX.md`, `CLAUDE.md`, runtime contracts, slash commands, and hooks installed into the target repo | Agent sessions |
| CI/guard layer | Post-install and post-update checks that prove the installed foundation still works | GitHub Actions, local verification |

## Chosen Decision

Use a CLI/library core with an optional MCP wrapper.

Reasons:

- CLI is deterministic, scriptable, testable, and usable without MCP.
- CI can run the CLI directly.
- MCP improves agent ergonomics without owning the core behavior.
- Tests can exercise the library once and verify both CLI and MCP call paths against the same implementation.
- Update and rollback logic can be shared by humans, agents, and automation.

## Alternatives Considered

| Option | Benefits | Problems | Decision |
| --- | --- | --- | --- |
| MCP-only installer | Good agent UX; structured tool calls from day one | Breaks if MCP is unavailable; harder to run in CI; encourages agent-dependent behavior | Rejected |
| Template repo copy | Simple to understand; easy initial bootstrap | Weak update story; poor conflict handling; no install plan or rollback by default | Rejected as standalone |
| Package-only distribution | Good versioning and install mechanics | Does not solve repo-specific merge planning, verification, or agent runtime setup by itself | Rejected as standalone |
| Git submodule/subtree | Clear upstream relationship; useful for vendor-style reuse | Rigid for customized project files; awkward for managed-file updates and workflow scaffolding | Rejected as primary path |
| CLI/library core plus MCP wrapper | Deterministic core, CI-friendly, agent-friendly when MCP exists, testable across project shapes | More implementation work; requires schema discipline between CLI and MCP | Chosen |

## V1 CLI Command Surface

The first durable command group should live under `scripts/codex-task`:

```text
python3 scripts/codex-task aegis inspect
python3 scripts/codex-task aegis plan-install
python3 scripts/codex-task aegis install
python3 scripts/codex-task aegis verify
python3 scripts/codex-task aegis list-profiles
python3 scripts/codex-task aegis explain-profile
```

Deferred command surface:

```text
python3 scripts/codex-task aegis status
python3 scripts/codex-task aegis plan-update
python3 scripts/codex-task aegis update
python3 scripts/codex-task aegis rollback
```

Default behavior:

- `inspect`, `plan-install`, `list-profiles`, and `explain-profile` are read-only.
- `install` is mutating and must create evidence reports.
- `install` defaults to dry-run behavior unless an explicit apply flag is provided.
- Unsafe overwrites are refused unless the install plan marks the merge as safe and the caller explicitly approves.

Current V1 prototype status as of 2026-05-16:

- The CLI is backed by `scripts/_aegis_installer.py` and exposed through `python3 scripts/codex-task aegis ...`.
- `inspect` reports target state without mutating the target repository.
- `plan-install` emits a schema-shaped install plan and refuses to silently choose an agent in non-interactive mode; callers must pass `--primary-agent` and at least one `--agent`.
- `install` defaults to dry-run behavior; `--apply` writes `.aegis/contract.md`, `.aegis/foundation-manifest.json`, `AGENTS.md`, schema files, and selected adapter files only when there are no conflicts.
- `verify` reads `.aegis/foundation-manifest.json`, checks required managed files, executable gates, and Claude hook registration when Claude is enabled, then records verification state in the manifest and `.aegis/reports/`.
- Second-run idempotence is part of the V1 contract: after a successful install and verify, a repeated plan should report skip-only/no-op behavior rather than manifest churn.

## MCP Tool Contract

The MCP server should wrap the Aegis library, not duplicate logic.

Task 109 V1 documents this MCP tool contract but does not need to ship the production MCP server.

The detailed wrapper contract is captured in `designs/aegis-mcp-wrapper-contract.md`. That document is the Task 109 handoff artifact for a future production MCP server task. The summary below is retained as the architecture overview.

Initial documented tool set:

```text
aegis.inspect
aegis.plan_install
aegis.install
aegis.verify
aegis.status
aegis.plan_update
aegis.update
aegis.rollback
aegis.list_profiles
aegis.explain_profile
```

Read-only tools:

- `aegis.inspect`
- `aegis.plan_install`
- `aegis.verify` when run in report-only mode
- `aegis.status`
- `aegis.plan_update`
- `aegis.list_profiles`
- `aegis.explain_profile`

Mutating tools:

- `aegis.install`
- `aegis.update`
- `aegis.rollback`

Mutating tools require explicit apply semantics and must return a structured report with changed paths, skipped paths, conflicts, verification results, and rollback checkpoint references.

## MCP Resources

The MCP server should expose structured resources so agents do not have to guess filesystem locations:

```text
aegis://contract/current
aegis://profiles
aegis://profiles/{name}
aegis://install-plan/latest
aegis://verification/latest
aegis://limitations
aegis://managed-files
aegis://project/status
```

## MCP Prompts

Prompts guide agent behavior, but they are not enforcement. They should call or instruct use of the CLI/MCP tools:

```text
aegis.bootstrap_new_project
aegis.migrate_existing_project
aegis.verify_runtime
aegis.prepare_agent_session
aegis.close_agent_session
aegis.install_claude_adapter
aegis.install_codex_adapter
```

## Manifest Contract

Every installed project should receive a versioned manifest at `.aegis/foundation-manifest.json`.

Draft fields:

```json
{
  "foundation_name": "Aegis Foundation",
  "foundation_version": "0.1.0",
  "installed_at": "2026-05-15T19:06:22+02:00",
  "profile": "generic",
  "primary_agent": "claude",
  "entrypoints": {
    "shared": "AGENTS.md",
    "contract": ".aegis/contract.md",
    "codex": "CODEX.md",
    "claude": "CLAUDE.md"
  },
  "interfaces": {
    "cli": {
      "command": "python3 scripts/codex-task aegis"
    },
    "mcp": {
      "namespace": "aegis",
      "available": false
    }
  },
  "access_policy": {
    "read_interface": "direct_read_or_aegis_cli",
    "write_interface": "aegis_cli_or_mcp",
    "direct_aegis_writes": false
  },
  "agents": {
    "codex": {
      "enabled": false,
      "available": true,
      "entrypoint": "CODEX.md"
    },
    "claude": {
      "enabled": true,
      "available": true,
      "entrypoint": "CLAUDE.md"
    },
    "gemini": {
      "enabled": false,
      "available": false
    }
  },
  "capabilities": {
    "taskmaster": true,
    "work_tracking": true,
    "ci": false,
    "mcp_contract": true
  },
  "gates": [
    {
      "id": "claude.readiness",
      "required": true,
      "enforcement": "mechanical",
      "path": ".claude/scripts/readiness.sh"
    },
    {
      "id": "claude.pretooluse",
      "required": true,
      "enforcement": "mechanical",
      "path": ".claude/scripts/pretooluse-gate.sh"
    },
    {
      "id": "codex.guard",
      "required": false,
      "enforcement": "verification",
      "command": "python3 scripts/codex-guard validate --include-untracked"
    }
  ],
  "managed_files": [],
  "customized_files": [],
  "last_verified_at": null,
  "installer_version": "0.1.0"
}
```

The manifest is required for reliable updates. Without it, update logic has to infer which files are managed, customized, agent-specific, or outside the Aegis boundary.

## Aegis Project Profiles

Profiles adapt Aegis to different repository shapes while preserving the same workflow core.

V1 implementation target: `generic`.

Profiles to define in schema:

| Profile | Purpose |
| --- | --- |
| generic | Minimal default for unknown repos |
| web-app | Product sites, SaaS apps, e-commerce, dashboards |
| python-tool | Python libraries, CLIs, local automation tools |
| docs-site | Documentation-heavy repos |
| game-tool | Games, interactive tools, asset-heavy projects |
| mixed | Repos with multiple app/tool surfaces |

Each profile should define expected directories, optional templates, CI recommendations, verification checks, ignored/generated paths, and agent-adapter defaults.

The generic profile should define Claude as the default recommended primary adapter while still asking the installer user to confirm the agent setup. If Claude is enabled, Claude hook gates are required. If Codex is enabled, Codex adapter files are installed and tracked as adapter-specific surfaces. If multiple agents are enabled, each enabled adapter contributes its required gates.

The profile schema should include fields such as:

```json
{
  "default_primary_agent": "claude",
  "supported_agents": ["claude", "codex"],
  "agent_selection_required": true,
  "conditional_gates": {
    "agents.claude.enabled": [
      "claude.readiness",
      "claude.pretooluse",
      "claude.bash_command",
      "claude.protected_path"
    ],
    "agents.codex.enabled": [
      "codex.guard",
      "codex.work_tracking_audit"
    ]
  }
}
```

## Install Lifecycle

1. Inspect the repository.
2. Detect project shape and existing foundation state.
3. Produce a dry-run install plan.
4. Classify each path as create, modify, skip, conflict, or manual-review.
5. Create a rollback checkpoint before mutating.
6. Apply the plan only when explicitly requested.
7. Run verification.
8. Write JSON and Markdown reports.
9. Update the manifest.

## Update Lifecycle

Update is deferred from the V1 implementation but documented here so the manifest/schema is designed correctly.

1. Read the installed Aegis manifest.
2. Compare installed version to current source version.
3. Detect local customizations.
4. Produce an update plan with safe changes and manual-review conflicts.
5. Create a rollback checkpoint.
6. Apply only safe and explicitly approved changes.
7. Re-run verification and update the manifest.

## Rollback Lifecycle

Rollback is deferred from the V1 implementation except where tests need local cleanup of failed V1 installs. Full cross-version rollback belongs in a follow-up task.

Rollback should restore the pre-install or pre-update checkpoint and then run verification that proves the repository returned to its previous state. Rollback reports must include restored paths, skipped paths, conflicts, and any manual cleanup required.

Current V1 cleanup status as of 2026-05-16:

- `aegis install --apply` refuses unsafe manual-review/conflict operations before writing any files.
- If an apply-time write fails after planning, Aegis removes planned newly-created files and returns a structured `status=failed` report with cleanup status.
- This is cleanup for failed local V1 install attempts, not the full rollback lifecycle.
- Full rollback commands, update rollback, checkpoint restoration, and cross-version migration rollback remain deferred follow-up work.

## Test Strategy

The test suite must prove behavior across fixture repositories, not just unit-level rendering.

Required test classes:

- Unit tests for project detection, plan generation, manifest parsing, profile selection, and conflict classification.
- Golden install-plan tests for fixture repos.
- Install-then-verify tests in temporary repositories.
- Install-twice idempotence tests.
- Forced-failure cleanup/rollback tests for V1 install operations.
- MCP contract tests or schema checks if a minimal wrapper is introduced; full MCP protocol tests are deferred with the production MCP server.
- Cross-agent smoke-test design notes for Codex and Claude adapters after install; full cross-agent automation is deferred unless needed to prove V1 verification.

Initial fixture repo matrix:

```text
empty-repo
basic-python-tool
```

Deferred fixture matrix:

```text
web-app
docs-site
game-tool
existing-claude-project
existing-codex-project
partial-foundation-install
old-foundation-version
```

## Verification Gates

An installed or updated target repo is not considered ready until these checks pass or are explicitly marked unsupported for that profile:

```text
python3 scripts/codex-guard validate --include-untracked
python3 scripts/codex-task work-tracking audit
python3 scripts/codex-task taskmaster health
python3 scripts/codex-task plan sync
git diff --check
```

If the Claude adapter is installed, verification should also include:

```text
bash .claude/scripts/readiness.sh --quick
cold-session mutation blocked
READY evidence write allowed
protected Codex-owned path edit blocked
Bash protected-path bypass blocked
```

## Improvement Loop

Each real install or update should produce:

- install/update report
- compatibility matrix entry
- limitation entry if anything could not be enforced
- profile feedback when the selected profile is insufficient
- follow-up Taskmaster tasks for gaps that cannot be solved inside the current task

## Task 109 Phasing

| Subtask | Deliverable |
| --- | --- |
| 109.1 | Architecture decision and distribution contract |
| 109.2 | Aegis manifest, profile, and install-plan schema |
| 109.3 | Generic-profile CLI installer lifecycle and verification commands |
| 109.4 | Fixture, idempotence, and V1 rollback/cleanup tests |
| 109.5 | MCP wrapper contract, deferred follow-up tasks, evidence, and handoff |

## Open Questions

- Resolved 2026-05-16: Task 109 includes the MCP wrapper contract only, not a tiny MCP proof-of-concept. The production MCP server is deferred until after the deterministic CLI/library core is stable.
- Resolved 2026-05-16: V1 generic-profile mandatory files are the shared `.aegis/` contract/manifest, schema files, `AGENTS.md`, and selected adapter files for explicitly enabled agents.
- Resolved 2026-05-16: generic empty-repo verification requires manifest schema validity and required adapter gate checks for enabled agents; Taskmaster/Codex workflow checks are only required when their adapter/capability is enabled.

## S:W:H:E Entries

- **2026-05-15 19:06 CEST** - [S:20260515|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md] Documented CLI/library-core plus optional MCP-wrapper architecture, alternatives, tool contract, manifest, profiles, test strategy, and verification gates.
- **2026-05-15 19:19 CEST** - [S:20260515|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md] Locked Task 109 to Option B: foundation installer contract plus generic-profile CLI prototype, with full MCP server, multi-profile support, complex migrations, package publishing, and CI installation deferred.
- **2026-05-16 11:05 CEST** - [S:20260516|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md] Named the portable runtime **Aegis Foundation**, selected `.aegis/foundation-manifest.json` as the shared agent-neutral manifest path, and renamed the V1 CLI/MCP namespace from `foundation` to `aegis`.
- **2026-05-16 12:53 CEST** - [S:20260516|W:task109-foundation-installer-mcp|H:scripts/_aegis_installer.py;scripts/codex-task|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/reports/foundation-installer-mcp/tests-2026-05-16-aegis-installer.txt] Recorded the V1 CLI prototype status after implementing the reusable Aegis installer core, command wrapper, install/verify/idempotence behavior, and installer tests.
- **2026-05-16 13:08 CEST** - [S:20260516|W:task109-foundation-installer-mcp|H:tests/meta_workflow_guard/test_aegis_installer_fixtures.py|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/reports/foundation-installer-mcp/tests-2026-05-16-aegis-fixtures.txt] Recorded the V1 fixture and cleanup status after adding empty-repo/basic-python-tool fixture coverage, multi-agent idempotence checks, conflict refusal, and failed-apply cleanup behavior.
- **2026-05-16 13:24 CEST** - [S:20260516|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/aegis-mcp-wrapper-contract.md] Added the detailed Aegis MCP wrapper contract and resolved the open question in favor of contract-only V1 handoff with production MCP server implementation deferred.
