# Task 204 Capsule PR-1c: gate-decisions dual-write – Handoff Summary

## Current State
- PR-1c implemented: advisory gate decisions dual-written to the ledger (parity key
  payload_digest), JSONL untouched as primary. Tests green; live dual-write verified
  in this repo's store.

## Next Steps
- Push feat/task-204-capsule-decisions-dualwrite, open PR, CI, explicit owner approval
  to merge.
- One release after this ships: freeze gate-decisions.jsonl read-only (spec section 2).
- Then PR-1d (task 205): gate registry + verification classification + scope records —
  the command-normalization-heavy slice, isolated on purpose.
- Archived on 2026-06-10 20:15 CEST — Folder moved to archive and tracker marked COMPLETED.
