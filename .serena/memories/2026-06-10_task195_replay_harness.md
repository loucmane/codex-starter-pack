# 2026-06-10 Task 195 replay harness kickoff

Capsule 1a-3.5 merged; gated remainder paused. TM 195 build: aegis_foundation/replay.py
engine running the REAL gate over corpus entries (state fixtures ready/blocked/
observation x strict/advisory); corpora at tests/fixtures/replay/ (hpcoach historical
FPs, synthetic adversarial with expected_gap for known FNs like .git/hooks writes,
must-allow); E01/E29 as direct must-fire tests; ingest_ledger() compounds the corpus
from live recordings; aegis replay CLI + pytest CI suite. Branch protection finding:
private+free plan = no server-side required checks; PR-4 gate needs Pro/public/HP-Coach.
