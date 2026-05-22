# Local Artifact MCP Proof

## Decision

Task 119 is a local-first release proof. It does not publish to TestPyPI or PyPI.

PyPI work is blocked until a fresh project can install and run Aegis from a local package artifact or package-style local source path without depending on this repository checkout at runtime.

## Required Proof

The proof must build local distribution artifacts, then use a brand-new temporary git project to verify the installed Aegis ecosystem can run the workflow end to end:

1. Build wheel and sdist artifacts.
2. Register or start the Aegis MCP using the local artifact or package-style local source path.
3. Call `aegis.inspect`, `aegis.plan_install`, `aegis.install`, `aegis.kickoff`, `aegis.log`, `aegis.verify`, and `aegis.closeout`.
4. Confirm `sessions/current`, `plans/current`, `.aegis/state/current-work.json`, and the ACTIVE work-tracking folder are created in the target project.
5. Confirm S:W:H:E evidence lands in the active session, tracker, implementation log, changelog, handoff, and plan.
6. Confirm the target runtime state does not contain `/home/loucmane/codex` or require `AEGIS_SOURCE_ROOT`.

## Boundary

Allowed in this task:

- local wheel/sdist build and inspection
- local wheel or local source-path MCP registration support
- fresh-folder local CLI/MCP smoke tests
- documentation that makes local proof a publication prerequisite

Deferred to a later task:

- TestPyPI publishing
- PyPI publishing
- Trusted Publishing workflow creation
- public package name reservation and release tagging

## Acceptance

Task 119 is complete when local tests and captured evidence prove a fresh target project can get the complete Aegis workflow from the local package path and pass install, kickoff, S:W:H:E log, strict verification, and closeout.
