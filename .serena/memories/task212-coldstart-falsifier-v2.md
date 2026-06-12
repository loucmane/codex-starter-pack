# Task 212 — Cold-start falsifier v2 (2026-06-12)

Replaces v1's degenerate metric. Built because the owner's workflow is long-lived
sessions (cold starts rare), so the per-session live A/B (TM 213) fills arms too
slowly; v2 generates authentic arms on demand.

## Mechanism (all in aegis_foundation/replay_coldstart.py, v2 section)
- `capture_scenario(repo, ...)` / `aegis coldstart capture` — forward-captures the
  CURRENT in-progress state: SHA, branch, dirty diff (200KB cap), ground truth derived
  from plans/current (first pending plan step → decision_class "continue" + keywords +
  Scope prefixes; no open step → "do_nothing"). Default output
  `.aegis/coldstart-scenarios/<id>.json` (untracked; operator promotes good ones to
  fixtures). Run it at natural mid-task pauses to build the corpus history squashed away.
- `build_envelope_worktree` — detached worktree at scenario SHA, replay branch
  `<branch>-coldstart-replay` (carries the task id → READY envelope), dirty patch
  re-applied, enforcement seeded advisory. `remove_envelope_worktree` deletes worktree
  + replay branch.
- `score_decision(transcript, expected)` — recon-to-CORRECT-DECISION: "continue"
  correct iff first meaningful mutation hits target_prefixes; "do_nothing" correct iff
  NO meaningful mutation AND final assistant text matches keywords (correctly doing
  nothing is a SUCCESS — the v1 inversion fix).
- `aggregate_v2` — accuracy per arm over ALL runs; recon deltas among CORRECT runs
  only (fast wrong answers don't help).
- `decide_v2` — pre-registered: KILL if capsule accuracy < baseline; fresh-null guard
  kept; KEEP-ELIGIBLE iff recon delta >= 1.0 with CI > 0 AND accuracy >= baseline.
- `run_live_ab_v2` — operator-only behind AEGIS_RUN_COLDSTART_AB=1; drops
  ANTHROPIC_API_KEY; pins AEGIS_CAPSULE per arm.

## Relationship to TM 213 per-session A/B
Both stay live: per-session hashing costs nothing and catches organic cold starts
(HP-Coach, other agents); v2 is the primary falsifier for the PR-3/PR-4 gates because
it doesn't depend on owner session habits. Compact-boundary stamps (source=compact)
are a free secondary read.

Tests: tests/claude_adapter/test_coldstart_falsifier_v2.py (14).
