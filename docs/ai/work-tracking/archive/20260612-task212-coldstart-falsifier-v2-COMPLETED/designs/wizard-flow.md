# Task 212 — Falsifier v2: design scope

Date: 2026-06-12. Trigger: owner workflow uses long-lived sessions, so the per-session
live A/B (TM 213) fills its arms too slowly to gate PR-3/PR-4; and v1's metric
(tool-calls-to-first-meaningful-action) inverted on gated done-states.

## Decisions
1. **Metric**: recon-to-CORRECT-DECISION. Each scenario carries ground truth
   (`continue` with target prefixes, or `do_nothing` with conclusion keywords).
   Correctly doing nothing is a success; a fast wrong mutation is a failure.
2. **Scenarios**: forward-captured via `aegis coldstart capture` — SHA + branch +
   dirty diff + plan-derived ground truth, written while work is live (mid-task states
   are squashed out of main history). Default landing: `.aegis/coldstart-scenarios/`
   (untracked); operator promotes durable ones to fixtures.
3. **READY envelope**: replay worktrees get a task-id-bearing replay branch
   (`<branch>-coldstart-replay`), the re-applied dirty diff, the committed workflow
   state from the tree, and advisory enforcement seeded — mutations are recorded,
   never gate-refused, so the metric measures orientation rather than gate posture.
4. **Verdict v2**: pre-registered. KILL on accuracy loss (capsule < baseline);
   fresh-null guard retained from v1; KEEP-ELIGIBLE requires recon delta ≥ 1.0 with
   CI > 0 among correct runs AND no accuracy loss. Testable core / operator-gated
   live split retained (AEGIS_RUN_COLDSTART_AB=1).

## Boundary
aegis_foundation/replay_coldstart.py + cli.py + tests. No mirrors involved (foundation
module, not a managed .claude script). TM 213's per-session hashing stays live as the
organic-cold-start collector; v2 is the primary falsifier for the PR-3/PR-4 gates.
