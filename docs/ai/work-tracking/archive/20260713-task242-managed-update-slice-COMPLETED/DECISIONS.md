# Decisions

- 2026-07-13 — Make `aegis_foundation.managed_update` the single authoritative managed-update core and keep it stdlib-only; do not introduce an installer import cycle or mutable singleton.
- 2026-07-13 — Keep concrete renderers, policy constants, JSON/schema I/O, apply orchestration, and reports in the installer. This is an incremental extraction, not a framework rewrite.
- 2026-07-13 — Preserve existing installer private names as thin compatibility adapters, including installer-level baseline/source resolvers used by regressions and downstream callers.
- 2026-07-13 — Treat operation summaries plus canonical operation digests as golden consumer contracts. Generated-byte parity remains a separate required invariant.
- 2026-07-13 — Keep unknown or locally divergent managed bytes fail-closed as `manual-review`; never convert extraction uncertainty into a safe overwrite.
- 2026-07-13 — Do not alter the installed manifest schema, target layout, ledger, enforcement mode, or runtime pointer. A reviewed revert must fully roll back the task without target migration.
- 2026-07-13 — Preserve the unchanged `/tmp`-location and client-reload tests and disclose their baseline behavior; require hosted exact-head proof instead of weakening unrelated safety assertions.
- 2026-07-14 — Treat current main's Tasks 247–251 behavior as authoritative during reconciliation. Move its shared-runtime deduplication and Codex hook ownership rules into the extracted core instead of restoring the stale pre-adapter planner.
- 2026-07-14 — Refresh the Codex golden contract to the current first-class adapter surface (38 creates, two safe structural modifications) while retaining the existing HP-Fetcher and Blog digests. This is a compatibility update to the fixture, not a target migration.
- 2026-07-14 — Require the final signed Task 242 tree to pass the complete suite from a real checkout outside `/tmp`; do not globally redefine Python's temp root because that invalidates other isolation tests.
