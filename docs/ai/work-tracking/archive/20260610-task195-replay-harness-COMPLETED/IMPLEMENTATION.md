# Task 195 Aegis vNext Phase 0 replay harness – Implementation Notes

## What was built
- aegis_foundation/replay.py: the engine — corpus entries (id/label/state/hook/payload/
  expected_gap) run through the REAL gate code (gate_lib via subprocess from the active
  source root) under six synthesized workflow states (blocked/ready/observation x
  strict/advisory, plus the ready+pending fixture). Label semantics encode the program's
  standing rules: must_allow and must_fire regressions fail; adversarial allows fail
  unless expected_gap (standing gaps are REPORTED, never silently passed); historical
  fp_workflow_state / ceremony_interior blocks form the FP baseline that may only ever
  go down (a flip to allow reports as an improvement).
- Committed corpora (tests/fixtures/replay/): hpcoach-2026-06.jsonl — ten gate-layer
  entries reproduced from the HP-Coach fixture (E04/E05/E08/E10/E17/E21/E22/E24/E29 +
  the codex bootstrap class observed live); synthetic-adversarial.jsonl — eight attacks
  with the two KNOWN current-policy gaps explicitly marked (.git/hooks write,
  package.json postinstall); must-allow.jsonl — ten legitimate actions incl. the #190
  repair carve-out and the new read-only surfaces (ledger path, brief, witness).
- E01/E29 must-fire goldens as direct tests: E01 via a real installed target
  (initialize_project -> start_observation -> dirty file -> stop refuses; reload marker
  cleared to simulate the post-install restart); E29 via the stop gate over a pending
  fixture, with the clean-stop control.
- ingest_ledger(): converts live ledger recordings into corpus candidates (Bash command
  text and file paths are reconstructable; digest-only events counted as non-replayable
  — the recorder-gap finding carried forward from the fixture's ingestion notes).
- aegis replay CLI (--corpus repeatable, --json, exit 1 on regression; read-only gate
  classification) + the pytest suite running the committed corpora in CI on every PR.

## Locks established
FP baseline = 9 (locked in test; may only decrease, deliberately). Standing gaps =
exactly {ADV-git-hook-write, ADV-postinstall}. Bare-`aegis` trust finding: bootstrap
sanctioning requires the local shim or python -m form (by design; corpus documents it).

## Verification
10 harness tests; full suite 1296 passed / 4 env-gated skips.
