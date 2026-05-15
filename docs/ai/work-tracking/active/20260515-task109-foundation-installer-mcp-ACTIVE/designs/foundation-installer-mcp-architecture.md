# Foundation Installer and MCP Architecture

## Summary

Task 109 turns the completed Codex starter-pack foundation into a portable system that can be installed, verified, updated, and audited in other projects.

The chosen architecture is a deterministic CLI/library core with an optional MCP wrapper.

The CLI/library owns the real behavior: project inspection, install planning, file application, verification, update, rollback, reports, and fixtures. The MCP server is an agent-facing control plane over that same core. This keeps the foundation usable by Codex, Claude, humans, CI, and future agents without depending on any single MCP client.

## Goals

- Install the foundation into greenfield and existing repositories without unsafe overwrites.
- Preserve deterministic behavior through a local library and CLI that can run in shell, CI, or tests.
- Expose the same behavior through MCP tools, resources, and prompts for agent-friendly operation.
- Produce install/update reports that explain files created, modified, skipped, conflicted, and verified.
- Support project profiles such as generic, web app, Python tool, docs site, game/tool, and mixed project.
- Make update and rollback realistic by recording a versioned managed-file manifest.
- Prove portability through fixture repositories, idempotence tests, rollback tests, and cross-agent smoke tests.

## Non-Goals

- Do not make MCP the only way to install or update the foundation.
- Do not overwrite existing project files by default.
- Do not treat copied documentation as proof that a target repository is functional.
- Do not require a specific agent to use the installed foundation.
- Do not ship long-running hosted infrastructure for the first implementation slice.

## Architecture Layers

| Layer | Responsibility | Primary Consumers |
| --- | --- | --- |
| Foundation library | Pure project inspection, planning, rendering, install/update/rollback operations, manifest handling, and verification orchestration | CLI, MCP server, tests |
| CLI | Deterministic command surface under `python3 scripts/codex-task foundation ...` | Codex, humans, CI |
| MCP server | Structured agent-facing tools/resources/prompts that call the same library | Claude, Codex MCP clients, future agents |
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

## CLI Command Surface

The first durable command group should live under `scripts/codex-task`:

```text
python3 scripts/codex-task foundation inspect
python3 scripts/codex-task foundation plan-install
python3 scripts/codex-task foundation install
python3 scripts/codex-task foundation verify
python3 scripts/codex-task foundation status
python3 scripts/codex-task foundation plan-update
python3 scripts/codex-task foundation update
python3 scripts/codex-task foundation rollback
python3 scripts/codex-task foundation list-profiles
python3 scripts/codex-task foundation explain-profile
```

Default behavior:

- `inspect`, `plan-install`, `status`, `plan-update`, `list-profiles`, and `explain-profile` are read-only.
- `install`, `update`, and `rollback` are mutating and must create evidence reports.
- `install` and `update` default to dry-run behavior unless an explicit apply flag is provided.
- Unsafe overwrites are refused unless the install plan marks the merge as safe and the caller explicitly approves.

## MCP Tool Contract

The MCP server should wrap the foundation library, not duplicate logic.

Initial tool set:

```text
foundation.inspect
foundation.plan_install
foundation.install
foundation.verify
foundation.status
foundation.plan_update
foundation.update
foundation.rollback
foundation.list_profiles
foundation.explain_profile
```

Read-only tools:

- `foundation.inspect`
- `foundation.plan_install`
- `foundation.verify` when run in report-only mode
- `foundation.status`
- `foundation.plan_update`
- `foundation.list_profiles`
- `foundation.explain_profile`

Mutating tools:

- `foundation.install`
- `foundation.update`
- `foundation.rollback`

Mutating tools require explicit apply semantics and must return a structured report with changed paths, skipped paths, conflicts, verification results, and rollback checkpoint references.

## MCP Resources

The MCP server should expose structured resources so agents do not have to guess filesystem locations:

```text
foundation://contract/current
foundation://profiles
foundation://profiles/{name}
foundation://install-plan/latest
foundation://verification/latest
foundation://limitations
foundation://managed-files
foundation://project/status
```

## MCP Prompts

Prompts guide agent behavior, but they are not enforcement. They should call or instruct use of the CLI/MCP tools:

```text
foundation.bootstrap_new_project
foundation.migrate_existing_project
foundation.verify_runtime
foundation.prepare_agent_session
foundation.close_agent_session
foundation.install_claude_adapter
foundation.install_codex_adapter
```

## Manifest Contract

Every installed project should receive a versioned manifest such as `.codex/foundation-manifest.json`.

Draft fields:

```json
{
  "foundation_version": "0.1.0",
  "installed_at": "2026-05-15T19:06:22+02:00",
  "profile": "generic",
  "features": {
    "codex_runtime": true,
    "claude_runtime": false,
    "taskmaster": true,
    "work_tracking": true,
    "ci": false
  },
  "managed_files": [],
  "customized_files": [],
  "last_verified_at": null,
  "installer_version": "0.1.0"
}
```

The manifest is required for reliable updates. Without it, update logic has to infer which files are managed, customized, or outside the foundation boundary.

## Project Profiles

Profiles adapt the foundation to different repository shapes while preserving the same workflow core.

Initial profiles:

| Profile | Purpose |
| --- | --- |
| generic | Minimal default for unknown repos |
| web-app | Product sites, SaaS apps, e-commerce, dashboards |
| python-tool | Python libraries, CLIs, local automation tools |
| docs-site | Documentation-heavy repos |
| game-tool | Games, interactive tools, asset-heavy projects |
| mixed | Repos with multiple app/tool surfaces |

Each profile should define expected directories, optional templates, CI recommendations, verification checks, ignored/generated paths, and agent-adapter defaults.

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

1. Read the installed foundation manifest.
2. Compare installed version to current source version.
3. Detect local customizations.
4. Produce an update plan with safe changes and manual-review conflicts.
5. Create a rollback checkpoint.
6. Apply only safe and explicitly approved changes.
7. Re-run verification and update the manifest.

## Rollback Lifecycle

Rollback should restore the pre-install or pre-update checkpoint and then run verification that proves the repository returned to its previous state. Rollback reports must include restored paths, skipped paths, conflicts, and any manual cleanup required.

## Test Strategy

The test suite must prove behavior across fixture repositories, not just unit-level rendering.

Required test classes:

- Unit tests for project detection, plan generation, manifest parsing, profile selection, and conflict classification.
- Golden install-plan tests for fixture repos.
- Install-then-verify tests in temporary repositories.
- Install-twice idempotence tests.
- Forced-failure rollback tests.
- Update tests from older manifest versions.
- MCP protocol tests that prove MCP tools call the same core logic and preserve read-only versus mutating boundaries.
- Cross-agent smoke tests for Codex and Claude adapters after install.

Initial fixture repo matrix:

```text
empty-repo
basic-python-tool
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
| 109.2 | Manifest, profile, and install-plan schema |
| 109.3 | CLI installer lifecycle and verification commands |
| 109.4 | Fixture, idempotence, rollback, and cross-agent tests |
| 109.5 | MCP wrapper contract, resources, prompts, evidence, and handoff |

## Open Questions

- Should the first implementation include a minimal MCP server, or should Task 109 only define the MCP contract and implement the CLI core first?
- Should `.codex/foundation-manifest.json` be installed into every target repo, or should projects be able to choose another manifest path?
- Which profiles must be supported in the first release versus documented as planned?
- Should GitHub Actions templates be installed automatically or only suggested during the first version?

## S:W:H:E Entries

- **2026-05-15 19:06 CEST** - [S:20260515|W:task109-foundation-installer-mcp|H:docs/architecture|E:docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md] Documented CLI/library-core plus optional MCP-wrapper architecture, alternatives, tool contract, manifest, profiles, test strategy, and verification gates.
