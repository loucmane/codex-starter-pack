# Task 121 Scope - Aegis Workflow UX and Logging Defaults

## Purpose

Task 121 hardens the Aegis installed workflow before TestPyPI or PyPI publication. Task 120 proved the local-wheel, fresh-project path works with a live Claude client, but it also exposed avoidable friction that would make agents perform extra bookkeeping instead of following the installed workflow naturally.

The target behavior remains:

- Aegis MCP and CLI are the workflow control plane.
- Native agent tools are the normal implementation, reading, testing, and git-inspection path.
- Installed hooks enforce readiness, pending S:W:H:E tracking, protected paths, strict verification, and closeout.

## Evidence Baseline

Primary baseline:

- `docs/ai/work-tracking/archive/20260522-task120-fresh-local-install-proof-COMPLETED/reports/fresh-local-install-proof/claude-live-test-result.md`

Task 120 verified that a fresh Claude client could:

- accept the project-scoped Aegis MCP server;
- install Aegis from a local wheel into an uninstalled target project;
- run kickoff and reach READY;
- edit `src/main.ts` with native tools;
- log S:W:H:E through Aegis;
- run strict verification;
- pass closeout.

## Findings To Fix

Task 120 exposed three UX gaps that are in scope for Task 121:

1. `aegis log` default surfaces forced agents to know closeout-required surfaces and relog entries for `CHANGELOG.md`.
2. Strict verification created a pending event that required exact handler/evidence copying.
3. Closeout missing-evidence failures named missing surfaces but did not provide deterministic repair commands or structured repair guidance.

## Scope

Task 121 will:

- add event-aware default surface selection for `aegis log`;
- preserve explicit `--surface` and MCP `surfaces` override behavior;
- add CLI and MCP pending-event consumption by id, with a deterministic current/latest sentinel only if unambiguous;
- improve pending-event block messages with copyable `aegis log --pending-id ...` guidance;
- add closeout repair guidance without making closeout auto-mutate evidence surfaces;
- keep source runtime and packaged assets in sync;
- prove the Task 120 live-style installed web workflow closes out without extra relogging.

## Non-Scope

- Publishing to TestPyPI or PyPI.
- Making MCP the source editor or implementation path.
- Weakening readiness, pending-tracking, protected-path, verify, or closeout gates.
- Auto-repairing closeout evidence during `aegis closeout`.

## Acceptance Direction

The task is done only when focused tests prove:

- scope, implementation, and verification logs get the right canonical surfaces by default;
- explicit surface overrides remain backward compatible;
- pending events can be consumed by id through CLI and MCP;
- closeout failures include actionable repair guidance;
- the live-style web workflow can install, kickoff, perform a native edit, log once per event, verify, and close out without extra changelog-only relogging.
