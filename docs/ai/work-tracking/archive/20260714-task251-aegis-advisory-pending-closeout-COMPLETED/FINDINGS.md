# Findings

- 2026-07-14 — The hook runtime records event mode, but `_strict_pending_tracking_check` and `closeout` independently reduce the delivery rule to queue emptiness. This is the Blog Task 40 contradiction.
- 2026-07-14 — `_pending_tracking_events` filters non-dict entries and treats unreadable or structurally invalid payloads as empty, so a delivery-safe classifier must read and validate the raw queue before selecting samples.
- 2026-07-14 — The kickoff wizard emitted a generic wizard-implementation plan for a runtime-semantics task; the source guard correctly prevented implementation until the scope artifact was reconciled.
- 2026-07-14 — The Blog Task 40 contradiction reproduces with 97 explicit advisory events: the new classifier reports `advisory_only`, strict verification and both closeout modes pass, and the queue remains byte-for-byte intact.
- 2026-07-14 — Existing real-gate replay had strict-pending coverage but no advisory-pending state. Task 251 adds `ready_advisory_pending` and preserves all 97 events after both pretool and stop replay.
- 2026-07-14 — Review caught that the replay fixture builder previously detected advisory mode only from an `_advisory` suffix. The new pending state uses explicit mode detection and a regression assertion, avoiding a false test under strict runtime mode.
- 2026-07-14 — The repository-wide suite passed 1,996 tests with four opt-in smoke skips. Its sole failure is a pre-existing location-sensitive reconcile test: a worktree under `/tmp` makes `REPO_ROOT` satisfy the test apparatus's isolated-temp condition. The changed runtime produced the expected `target_not_isolated_temp` refusal against `/home/loucmane/codex` before validation, confirming no Task 251 regression.
