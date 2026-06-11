# Task 211 replay-cold-start A/B falsifier – Implementation Notes

- aegis_foundation/replay_coldstart.py: extract_first_action_cost (transcript parser →
  tool-calls-to-first-meaningful-action), is_meaningful_action (first mutation outside
  governance/scratch surfaces, spec section 7), build/remove worktree (historical state
  reconstruction), aggregate (paired baseline-capsule recon delta + normal-approx 95%
  CI, correctness tally), decide (pre-registered KEEP-ELIGIBLE/KILL/INCONCLUSIVE with
  fresh-null guard), render_report.
- OPERATOR-ONLY run_live_ab behind AEGIS_RUN_COLDSTART_AB=1: builds worktrees, fires
  fresh claude -p per arm (capsule on / AEGIS_CAPSULE=off), parses the newest transcript,
  aggregates + decides; refuses without the gate so CI never runs real sessions.
- Fixtures: 4 cold-start transcripts (low/high recon, governance-only-then-action,
  never-acts). 11 CI tests cover the whole core + the operator gate. Full suite green.
- This authorizes a KEEP (it measures real cost), unlike the synthetic cohort; the
  owner's live interleaved A/B remains gold-standard confirmation.
