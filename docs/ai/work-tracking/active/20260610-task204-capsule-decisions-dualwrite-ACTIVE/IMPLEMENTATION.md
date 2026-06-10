# Task 204 Capsule PR-1c: gate-decisions dual-write – Implementation Notes

## What was built
- `Payload` gained optional `session_id`/`cwd` populated by `parse_payload` from the
  hook stdin JSON (defaults None; `payload_digest` proven unchanged by the new fields,
  preserving parity with historical digests).
- `append_gate_decision()` now mirrors every advisory decision into the ledger via
  `_dual_write_gate_decision()`: event_type `gate_decision`, same ts and
  payload_digest (the parity key), extra carrying verdict/reason/mode/hook/
  source_commit/readiness_state. Strictly best-effort — any failure is swallowed; the
  JSONL write never depends on it. Both gate_lib copies mirrored.
- NOT done on purpose (spec section 2): JSONL freeze (one release later), history
  migration (never), reader changes (aegis enforce status keeps reading JSONL).

## Verification
- 4 new tests: attribution parsing, digest invariance, end-to-end advisory parity
  (every JSONL record has a ledger twin by payload_digest with matching
  verdict/reason/mode/hook + session attribution), JSONL-survives-without-ledger,
  strict-mode unchanged. 151 targeted tests green; full suite in CI.
- Live dogfood: dual-write active immediately (gate hooks run fresh per call) — new
  advisory decisions in this repo twin into the out-of-worktree store alongside the
  PR-1b recorder events.

## Rider fix (found by this PR's full-suite run)
- Latent PR-1a race: `PRAGMA journal_mode=WAL` takes an exclusive lock and raised
  "database is locked" under concurrent SQLiteLedger opens (the busy handler does not
  reliably cover this pragma). Fixed in ledger_lib (both copies): busy_timeout set
  first, WAL pragma wrapped in a bounded retry, degrading to the file's existing
  journal mode if every attempt loses the race. Concurrent-writers test now passes
  6/6 consecutive runs (was intermittent). Surfaced precisely because the live
  recorder + dual-write now create real hook-process concurrency on this machine —
  the dogfood loop working as intended.
