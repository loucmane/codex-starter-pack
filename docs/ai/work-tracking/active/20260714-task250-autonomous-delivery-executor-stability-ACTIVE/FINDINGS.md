# Findings

- 2026-07-14 — PR #276 reproduced the Task 247 assumption failure twice: the read-only evaluator succeeds, but the running non-required executor keeps GitHub `mergeable_state=unstable`, so a fresh clean-only policy can never authorize itself.
- 2026-07-14 — The exact-head Checks API exposes sufficient provenance to distinguish the current trusted executor: check name, GitHub App slug, repository Actions URL, run ID, job ID, status, conclusion, and head SHA.
- 2026-07-14 — Legacy commit statuses are a separate surface from Checks API runs; both inventories must be evaluated before treating instability as self-generated.
- 2026-07-14 — The first PR #276 CI failure was an unrelated one-off Python 3.11 MCP stdio timeout; the failed-job rerun passed all 1,957 tests, while Python 3.12 and all closeout-specific tests were already green.
- 2026-07-14 — Task 250 initially inherited two ACTIVE folders because PR #276 could not merge before this policy fix. The source guard correctly refused that state. Archiving Task 249 through the supported helper and restoring its exact reviewed terminal files removes the bootstrap cycle without deleting evidence or changing Task 250's current plan/session pointers.
