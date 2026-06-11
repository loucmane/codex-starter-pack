# Task 211 replay-cold-start A/B falsifier – Handoff Summary

## Current State
- Authentic falsifier built + CI-tested (11 tests, full suite green). Operator runs
  real cold-start A/B via AEGIS_RUN_COLDSTART_AB=1 + run_live_ab over seeded scenarios.

## Next Steps
- Push, PR, CI, owner merge approval.
- OPERATOR: seed scenarios (today's kickoff SHAs + HP-Coach incidents), run run_live_ab
  k>=3; if KEEP-ELIGIBLE, confirm with the spec section 7 live interleaved A/B, then
  unpause PR-3 (narration) and PR-4 (retirement). If KILL, keep the recorder, drop Loop 3.
