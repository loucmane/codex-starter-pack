# Task 251 Fix Aegis Advisory Pending Delivery Closeout Semantics – Implementation Notes

## Planned Workstreams
- [x] Add one fail-closed raw pending-queue classifier with bounded summaries.
- [x] Route status, verify, closeout, closeout readiness, doctor, next, and repair guidance through the classifier.
- [x] Preserve advisory-only evidence while allowing delivery and closeout; retain strict failure for required or untrusted state.
- [x] Keep source and packaged runtime/docs byte-identical where required.
- [x] Add Blog Task 40 fixture, dry-run immutability, output-budget, replay, parity, and documentation regressions.

## Runtime Changes

- `scripts/_aegis_installer.py` now classifies the raw pending queue as `absent`, `empty`, `advisory_only`, `required_only`, `mixed`, `unknown`, or `malformed`. It reports exact counts, five bounded samples, provenance validity, preservation state, and the canonical artifact path.
- Status, enforcement status, next guidance, doctor, strict verification, closeout readiness, closeout population, closeout repair guidance, and text summaries consume the same classification result.
- Advisory-only evidence passes strict delivery verification and closeout without being rewritten, deleted, drained, or converted into repair commands. Explicit strict events and every untrusted queue shape still fail closed.
- `.claude/scripts/gate_lib.py` ignores historical advisory-only residue for mutation/stop gating, records new strict mutations as strict, promotes a deduplicated advisory event when the same mutation recurs under strict mode, and bounds strict queue feedback to five events plus an exact omitted count.
- `aegis_foundation/cli.py` advertises `.aegis/state/pending-tracking.json` as the complete artifact for status, doctor, verify, next, and closeout output.

## Evidence and Regression Changes

- Added the sanitized 97-event Blog Task 40 reproduction at `tests/fixtures/aegis/blog-task40-advisory-pending-closeout.json`; no live Blog repository content was read or changed.
- Added real-gate replay state `ready_advisory_pending` and corpus cases proving edit and stop both allow while all 97 advisory events remain stored.
- Added classifier, strict re-entry, normal/dry-run closeout preservation, output-budget, gate-feedback budget, mirror parity, documentation parity, and malformed/mixed/unknown negative tests.
- Added the source and packaged lifecycle contract at `docs/aegis/advisory-pending-lifecycle.md` and `aegis_foundation/assets/docs/aegis/advisory-pending-lifecycle.md`, including the separately attended Blog retry procedure.

## Progress Log

- **2026-07-14 13:19** — [S:20260714|W:task251-aegis-advisory-pending-closeout|H:pytest:task251-verification|E:docs/ai/work-tracking/archive/20260714-task251-aegis-advisory-pending-closeout-COMPLETED/reports/aegis-advisory-pending-closeout/task-verification.md] Verified advisory pending delivery semantics, strict fail-closed behavior, dry-run immutability, output budgets, replay, and source/package parity
