# Task 113 Release Distribution Contract Baseline

## Purpose
Task 113 turns the Task 112 local checkout and editable package invocation contract into a release-ready Aegis distribution contract. The work must extend the existing contract; it must not remove or replace local checkout usage, editable installs, `scripts/codex-task aegis ...`, or the MCP development startup paths that Task 112 verified.

## Scope Boundary
- Public package metadata and naming must become explicit, documented, and testable.
- Wheel and sdist builds must include the assets Aegis needs to install and verify a target project without reaching back into `/home/loucmane/codex`.
- External CLI and MCP invocation must be verified from outside the repository.
- `uvx` and `pipx` paths must be documented and, where the local environment supports them, exercised against a local wheel or local package path before any public package publication exists.
- Update, migration, rollback, signing, hosted/offline MCP guidance, CI install templates, and a release verification matrix must be documented as a production release contract.
- Actual publication to PyPI or a package registry is out of scope unless explicitly added later.

## Subtask Shape
1. `113.1` - Create the design baseline, findings, decisions, handoff state, and workflow evidence.
2. `113.2` - Update public package metadata and single-source version contract.
3. `113.3` - Implement wheel-safe asset resolution and package-data bundling.
4. `113.4` - Verify external installed CLI invocation and install snippets.
5. `113.5` - Harden packaged MCP startup and asset-origin discovery.
6. `113.6` - Define update, rollback, migration, signing, and release policy.
7. `113.7` - Add CI install templates and release verification matrix.
8. `113.8` - Run final regressions and close handoff evidence.

## Initial Decisions
- Keep `aegis` and `aegis-mcp-server` as the command names unless a concrete collision is found.
- Treat `aegis-foundation` as the working public distribution name until package-name checks or release policy identify a better name.
- Keep packaged install support as additive. Development checkout and editable package paths remain first-class.
- Prefer deterministic local wheel/install verification over any task that depends on publishing to an external registry.

## Verification Boundary
Task 113 is not complete until tests and stored evidence prove:
- package metadata and docs agree;
- wheel/sdist artifacts contain required Aegis assets;
- external installed CLI invocation works from a non-repo cwd without `AEGIS_SOURCE_ROOT`;
- packaged MCP startup and `--describe-config` resolve target cwd and asset origin correctly;
- update/rollback/signing guidance is present and tested through documentation checks;
- CI install templates and release matrix remain in sync with the command contract;
- Taskmaster health, plan sync, work-tracking audit, codex guard, and `git diff --check` are clean.
