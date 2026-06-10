# TM #195 scope — replay harness

Task text: additive replay path ingesting recorded decisions/sessions; golden scenarios
for the HP-Coach corpus (13 FP workflow blocks; E01 true positive; E29 must-fire
mechanism); synthetic adversarial cases; FP/FN deltas for any gate/policy change.
Measurement only — zero behavior change. CI on gate-touching PRs.

## Deliverables

1. **aegis_foundation/replay.py** — the engine: a corpus entry is
   {id, label, state, payload, expect, notes}; `state` selects a synthesized repo
   fixture (ready/blocked/observation x strict/advisory); the engine builds the fixture,
   runs the REAL gate (gate_lib pretooluse/stop via subprocess from the active source
   root), and compares verdicts. Labels carry expectations:
   - `fp_workflow_state` — historical false positives: blocked under the HISTORICAL
     state; the report tracks how many still block (the FP baseline that must only
     ever go DOWN);
   - `must_fire` — E29-class completeness checks that must keep firing forever;
   - `adversarial_must_block` — synthetic attacks that must never be allowed
     (known current-policy gaps are encoded expected_gap=true so they REPORT as
     standing FNs instead of silently passing);
   - `must_allow` — legitimate actions that must never regress into blocks.
2. **Corpus** at tests/fixtures/replay/: hpcoach-2026-06.jsonl encoding the gate-layer
   events from the HP-Coach fixture (E04/E05/E08/E10/E13/E17/E18/E21/E22/E24/E25/E26/
   E32-class entries reproduced as state+payload pairs), synthetic-adversarial.jsonl
   (protected-path writes incl. the .git/hooks gap, settings tamper, taskmaster
   mutations while blocked), and must-allow.jsonl (reads, sanctioned aegis commands,
   repair-while-blocked per #190).
3. **E01/E29 goldens as direct tests**: E01 (observe-stop refuses a dirty tree) via the
   installer in a tmp installed target; E29 (Stop gate blocks on trailing pending
   tracking) via gate_lib stop with a pending-tracking fixture — the must-fire set that
   survives every policy change.
4. **Ledger ingestion**: `ingest_ledger()` converts this repo's live ledger
   (mutation/gate_decision events with reconstructable payloads — Bash command text and
   file paths survive in extra/paths) into corpus candidates, so every recorded session
   compounds the corpus. Digest-only decisions are reported as non-replayable (recorder
   gap finding, matches the old fixture's ingestion notes).
5. **`aegis replay --corpus <path>`** CLI (read-only classified) printing per-label
   counts + deltas, exit 1 on regression (lost must-allow, new FP, adversarial allow
   without expected_gap). **pytest suite** (tests/claude_adapter/test_replay_harness.py)
   runs the committed corpora in CI on every PR — gate-touching changes are covered by
   the same suite that already runs everywhere.

## Out of scope
Policy-change simulation UX beyond corpus reruns; HP-Coach JSONL transcript backfill
(the 270MB join belongs to a later ingestion pass); auto-fix of the .git/hooks FN gap
(recorded as expected_gap; closing it is its own policy change to be replayed).
