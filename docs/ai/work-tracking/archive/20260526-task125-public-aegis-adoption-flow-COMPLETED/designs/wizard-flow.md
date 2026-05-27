# Task 125 Scope - Public Aegis Adoption Flow

Date: 2026-05-26
Branch: `feat/task-125-public-aegis-adoption-flow`

## Problem

Task 124 proved the current Aegis runtime can install into an existing project and guide Claude through readiness, S:W:H:E tracking, verification, and closeout. The remaining product gap is usability: the successful flow still exposes too many low-level mechanics (`plan_install`, `install apply`, explicit numeric task kickoff, long prompts).

The public flow should let a user install and use Aegis in the same mental model as established project tools:

```bash
aegis mcp register claude
cd project
aegis init
aegis start "Improve BrandMark accessibility"
```

After that, a fresh Claude session should handle a normal request through the installed contract and hooks, without requiring the user to paste a workflow checklist.

## Boundaries

- Aegis remains the workflow control plane.
- Native agent tools remain the implementation path.
- Existing low-level commands stay backward compatible.
- Taskmaster and Serena are optional integrations, not hard dependencies for target projects.
- Public wrappers must delegate to the proven installer, kickoff, log, verify, closeout, and MCP-registration internals.
- Packaged assets must stay in parity with source assets.
- Existing project instructions must be preserved; no `.bak`, `.orig`, or backup sidecar files.

## Required Public Commands

- `aegis init`: run the inspect, plan-install, install/apply, and verify path with conservative defaults from inside a target project.
- `aegis mcp register claude`: register the Aegis MCP through Claude's native MCP command path, defaulting to user scope and package assets.
- `aegis start "<normal task title>"`: allocate a local task id, derive a slug, create branch/session/plan/work-tracking state, and make readiness READY without Taskmaster.

## Acceptance Shape

- Automated tests cover fresh projects, existing projects, local-task mode, hook behavior, MCP registration, MCP tools where exposed, docs, packaged assets, and release distribution.
- Live proof covers a fresh target and an existing target using the public flow.
- A no-huge-prompt Claude proof shows the installed files guide the behavior from a normal request.
