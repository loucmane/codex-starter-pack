# Task 256 Canonical Codex Home Topology Diagnostics and Migration Plan Tracker

**Started**: 2026-07-15
**Status**: COMPLETED
**Last Updated**: 2026-07-15

## Goals
- [x] Record the binding single-canonical-home architecture and explicitly reject the dual-home wrapper topology as steady state
- [x] Inventory Codex homes, SQLite ownership, binaries, versions, sockets, lifecycle metadata, trust, sessions, and routing with secret-safe provenance
- [x] Detect split brain and diagnose stale pre-trust threads only from reliable evidence without inferring hook approval
- [x] Produce deterministic no-mutation migration planning that fails closed when active work or ownership is unknown
- [x] Specify the exact drain-first Task 257 host cutover, rollback, preservation, and attended checkpoints
- [x] Add deterministic focused and regression tests proving read-only behavior, redaction, and source-package parity
- [x] Preserve both live Codex homes, active servers, shell configuration, wrapper, Blog, sessions, credentials, and trust stores
- [x] Complete source verification and closeout preparation for attended exact-head PR delivery; automatic merge remains prohibited

## Progress Log
- **2026-07-15 20:55** — [S:20260715|W:task256-canonical-codex-home-topology|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-07-15 20:55 CEST`
- **2026-07-15 20:55** — [S:20260715|W:task256-canonical-codex-home-topology|H:scripts/codex-task|E:docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/TRACKER.md] Scaffolded the Task 256 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-07-15 20:55** — [S:20260715|W:task256-canonical-codex-home-topology|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 256 in progress and updated only its generated task file
- **2026-07-15 20:55** — [S:20260715|W:task256-canonical-codex-home-topology|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 256 kickoff
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:aegis_foundation/codex_topology.py|E:schemas/aegis/codex-topology-status.schema.json] Implemented a bounded, read-only, secret-safe topology collector that distinguishes home, SQLite, session, server, executable, wrapper, trust-guidance, process-scope, and thread-freshness evidence without asserting client hook approval
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:aegis_foundation/cli.py|E:tests/meta_workflow_guard/test_codex_topology.py] Added `aegis codex topology status|plan`, fail-closed unknown-state handling, strict status/plan schemas, packaged mirrors, and 50 focused schema/topology tests
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:docs/aegis/canonical-codex-home-architecture.md|E:docs/aegis/task257-canonical-codex-home-cutover-plan.md] Published the binding single-home ADR and exact ten-phase drain-first Task 257 plan with preservation, rollback, canary, `/hooks`, and attended boundaries
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:pytest|E:tests/meta_workflow_guard/test_codex_topology.py] Passed 2,130 runnable regression tests with 4 opt-in smoke skips; separately proved the three full-run failures and one timeout are unchanged baseline/environment constraints, not Task 256 regressions
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:aegis:codex-topology-status|E:docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/FINDINGS.md] Read-only dogfood detected two session stores, two control sockets, multiple executable identities, and ambiguous SQLite authority while correctly refusing to infer host-wide process safety from the sandbox namespace
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:serena/memory|E:.serena/memories/2026-07-15_task256_canonical_codex_home_topology.md] Activated the isolated Task 256 clone in Serena and recorded the architecture, implementation, verification, preservation boundary, and Task 257 continuation state through Serena MCP
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:validation:evidence|E:docs/ai/work-tracking/archive/20260715-task256-canonical-codex-home-topology-COMPLETED/reports/canonical-codex-home-topology/task-verification.md] Recorded acceptance coverage, exact verification results, independently reproduced baseline constraints, live read-only dogfood, preservation proof, and the attended delivery boundary
- **2026-07-15 22:12** — [S:20260715|W:task256-canonical-codex-home-topology|H:task-master:set-status|E:.taskmaster/tasks/task_256.md] Marked Taskmaster Task 256 done and regenerated only its targeted task projection after implementation and verification passed

## Plan Compliance Checklist
- [x] plan-step-scope — Canonical-home ADR and official-fact boundary recorded
- [x] plan-step-contract — Diagnostic and planner contracts frozen before implementation
- [x] plan-step-implement — Read-only topology and no-mutation planner implemented
- [x] plan-step-test — Focused, regression, no-write, and package-parity evidence passed
- [x] plan-step-cutover — Exact drain-first Task 257 plan published
- [x] plan-step-verify — Workflow evidence synchronized, Task 256 completed, and attended exact-head PR delivery prepared
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
