# Agent Foundation Portability Options

**Captured**: 2026-05-07 14:59 CEST
**Context**: Forward-looking architecture discussion captured during Task 10 after the reference-fix implementation was already complete. This is not Task 10 implementation scope; it is a decision record for future foundation portability work.

## Problem

The Codex/Claude workflow foundation should be reusable across different project types: web apps, games, packages, MCP servers, documentation sites, and other repositories. The system needs to be enforceable, not memory-based or documentation-only.

The portability target is:

- install the workflow into a new project without hand-copying files;
- keep installed projects upgradeable without overwriting project-specific context;
- let Codex and Claude use the same foundation through agent-specific adapters;
- enforce local behavior through hooks, guards, tests, and CI;
- preserve direct Git/GitHub execution as the default when auth is cached;
- avoid requiring `gac` unless the user explicitly asks or local auth/cache is unavailable.

## Options Considered

### Option A - MCP-only workflow runtime

Build an MCP server that owns the workflow directly and agents call MCP tools for everything.

**Pros**
- Structured agent interface.
- Easy for agents to discover high-level workflow actions.
- Could centralize project inspection and task scaffolding.

**Cons**
- Enforcement disappears when MCP is unavailable or not configured.
- CI and plain Git/Bash do not naturally run through MCP.
- Agents could still mutate files through standard tools unless local hooks exist.
- Recreates the "agent must choose the right path" failure mode.

**Decision**
- Rejected as the foundation.
- MCP can be useful, but not as the only runtime or enforcement layer.

### Option B - Template/starter-pack only

Keep this repository as a starter template. New projects copy the files and adapt them manually.

**Pros**
- Simple and close to the current repo shape.
- Low initial build cost.
- Works for early experiments.

**Cons**
- Manual copy causes drift.
- Upgrades across projects are hard.
- No manifest or lockfile to know which runtime version is installed.
- Agents may skip or partially copy required files.

**Decision**
- Rejected as the long-term portability model.
- Templates remain useful as inputs to an installer.

### Option C - Local CLI/package only

Create an `agent-foundation` CLI/package that installs, verifies, upgrades, and operates the workflow.

**Pros**
- Deterministic local implementation.
- Works without MCP.
- Can be run by humans, Codex, Claude, CI, or scripts.
- Easier to test than an MCP-only implementation.

**Cons**
- Less ergonomic for agents than structured MCP tools.
- Agents can still call commands incorrectly unless the CLI exposes safe high-level operations.
- Requires careful idempotency and conflict handling.

**Decision**
- Accepted as a required core layer, but not sufficient alone for best agent ergonomics.

### Option D - Repo-installed runtime with local CLI plus MCP installer/control plane

Build a versioned local runtime and CLI, install enforcement files into each project, and expose high-level install/upgrade/doctor/kickoff/archive operations through an MCP server that wraps the same core implementation.

**Pros**
- Local repo protects itself through installed files, hooks, guard scripts, tests, and CI.
- MCP becomes an agent-friendly control plane without becoming a single point of enforcement.
- CLI and MCP can share one implementation, reducing drift.
- Works when MCP is unavailable because local CLI/guards/CI still exist.
- Supports idempotent install, versioned upgrade, smoke tests, and project profiles.

**Cons**
- More work than template-only or MCP-only.
- Requires a manifest/lockfile and managed-file strategy.
- Requires migration logic to preserve project-specific custom sections.
- Requires clear bootstrap rules before the workflow exists.

**Decision**
- Chosen as the target architecture.

### Option E - External hosted service/control plane

Run the foundation as an external service that tracks project state, versions, and agent coordination.

**Pros**
- Centralized version visibility across many projects.
- Could coordinate fleet-wide upgrades.
- Useful later for organizations or dashboards.

**Cons**
- Adds hosting, credentials, availability, and privacy concerns.
- Too heavy for the current local-first workflow.
- Still needs local repo enforcement, so it does not remove the hard part.

**Decision**
- Deferred. Potential future layer, not the base architecture.

## Chosen Architecture

Use Option D:

```text
Agent Foundation MCP
  Agent-facing installer/control plane

Agent Foundation CLI/package
  Deterministic local implementation

Project-installed runtime
  Files, hooks, guards, tests, CI, templates, Taskmaster integration

Manifest/lockfile
  Versioned record of installed runtime, managed files, enabled adapters, and enforcement rules
```

The MCP should expose high-level operations:

- `inspect_project`
- `plan_install`
- `apply_install`
- `doctor`
- `smoke_test`
- `plan_upgrade`
- `apply_upgrade`
- `kickoff_task`
- `archive_task`
- `explain_state`

The MCP should not expose arbitrary `write_file`, `run_shell`, or `patch_anything` style tools as its core interface.

## Why This Choice

The workflow has to survive agent forgetfulness, missing MCP servers, future cold sessions, and CI. That means enforcement must live inside each project checkout, not only in the agent interface.

The local runtime gives durable enforcement:

- Codex guard and work-tracking audit;
- Claude readiness and PreToolUse gates;
- cold-session zero-mutation tests;
- protected-path tests;
- Taskmaster generated-file drift control;
- GitHub Actions guard checks;
- direct Git/GitHub protocol with `gac_required=false`.

The MCP layer improves usability:

- agents get structured install/upgrade/scaffold tools;
- install plans can be reviewed before mutation;
- project state can be explained consistently;
- upgrades can be planned and applied without manual copying.

The manifest/lockfile makes the system portable:

- records installed version;
- records enabled agents and integrations;
- records managed files and project-owned files;
- supports safe upgrades and conflict reporting.

## Required Design Pieces

Future portability work should define:

- `.agent-foundation/manifest.json`
- `.agent-foundation/lock.json`
- `.agent-foundation/managed-files.json`
- install planner
- apply installer
- doctor command
- smoke-test command
- upgrade planner
- migration engine
- Codex adapter
- Claude adapter
- Taskmaster adapter
- GitHub adapter
- optional Serena adapter
- optional MCP wrapper around the CLI/package

## Managed File Policy

Installed projects need file ownership categories:

- **Managed files**: fully owned by the foundation runtime and replaceable on upgrade.
- **Managed files with custom regions**: foundation owns marked generated sections; project owns marked custom sections.
- **Project-owned files**: installer may inspect and recommend changes, but must not overwrite without explicit approval.

This avoids turning portability into destructive template copying.

## Bootstrap Rule

Installing into a project before workflow state exists requires a bounded bootstrap mode:

- clean Git tree required;
- inspect first;
- plan before write;
- explicit approval before apply;
- no unrelated source edits;
- run doctor immediately after install;
- run smoke tests immediately after install;
- record install evidence in the project once the workflow exists.

Bootstrap mode is the sanctioned exception to "no workflow scaffolding, no mutation" because its purpose is to create the workflow scaffolding.

## Reversal Criteria

Revisit this decision if any of these become true:

- MCP hookability becomes reliable enough to enforce all relevant mutation surfaces without local hooks.
- Maintaining local CLI and MCP wrapper produces unacceptable drift despite shared core implementation.
- Managed-file migrations prove too fragile across real projects.
- Project profiles require so much customization that a single foundation package becomes counterproductive.
- CI or local hook behavior diverges across platforms in ways the runtime cannot abstract cleanly.

If this happens, compare again against the rejected options and consider splitting the system into a smaller template registry plus optional project-specific installers.

## Follow-Up Task Candidate

Create a future Taskmaster task:

**Build Agent Foundation Installer and Portability Manifest**

Scope:
- introduce `.agent-foundation/manifest.json` and lockfile;
- build a local installer/doctor/smoke-test CLI;
- prove install into a temp project;
- define managed-file sections;
- add an MCP wrapper only after the CLI core is stable.
