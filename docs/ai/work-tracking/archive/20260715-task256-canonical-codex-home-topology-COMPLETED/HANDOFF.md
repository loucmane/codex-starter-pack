# Task 256 Canonical Codex Home Topology Diagnostics and Migration Plan – Handoff Summary

## Current State
- Task 256 implementation is complete in the isolated clone on
  `feat/task-256-canonical-codex-home-topology`.
- The binding architecture, read-only topology diagnostics, strict schemas, deterministic
  no-mutation planner, and exact Task 257 drain-first cutover plan are present and verified.
- Live read-only dogfood reports split brain and blocks Task 257 because process scope and
  SQLite authority are not yet host-proven. This is the intended fail-closed result.
- All runnable regression tests pass; independently reproduced baseline/environment
  constraints are recorded in `FINDINGS.md` and must not be misreported as Task 256 defects.
- Cross-session continuity is recorded in Serena memory
  `.serena/memories/2026-07-15_task256_canonical_codex_home_topology.md`.
- Neither live Codex home, any server, shell configuration, wrapper, Blog, auth, sessions,
  SQLite state, trust store, hook hash, nor Gas Town migration state was modified.

## Next Steps
1. Run plan sync, Taskmaster health, work-tracking audit, readiness, and S:W:H:E guard.
2. Review the final diff and generated-file scope.
3. Mark Task 256 done only after final verification evidence is current and archive its
   tracking folder through the supported closeout workflow.
4. Commit and push the exact reviewed Task 256 branch, open an attended PR, and stop before
   merge.
5. After the owner reviews and merges Task 256, create Task 257 from
   `docs/aegis/task257-canonical-codex-home-cutover-plan.md`; do not execute the cutover as
   part of Task 256.

## Verification Summary

- Focused topology/schema: 50 passed.
- Runnable full suite: 2,130 passed, 4 opt-in smoke skips.
- Baseline-only exceptions: two network-dependent editable installs, one sandbox-stalled
  stdio MCP test, and one `/tmp`-location assumption; each reproduced on untouched main or
  passed in the canonical checkout as applicable.
- Ruff, module typing, byte parity, schema validation, compile, and diff checks passed;
  Black reported both new Python files unchanged, while modified legacy files preserve
  independently confirmed pre-existing formatting rather than introducing unrelated churn.
- Full command/result detail is stored in
  `reports/canonical-codex-home-topology/task-verification.md`.

## Task 257 Authority Boundary

The cutover document is a plan, not mutation authority. Task 257 must independently prove
host-complete process ownership, drain active work, select the authoritative SQLite root,
take immutable backups, preserve sessions/auth/connectors/trust, and obtain its documented
attended boundaries before changing topology.
- Archived on 2026-07-15 22:24 CEST — Folder moved to archive and tracker marked COMPLETED.
