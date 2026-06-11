# 2026-06-11 Task 211 replay-cold-start A/B falsifier

aegis_foundation/replay_coldstart.py: authentic capsule falsifier replaying real cold-start
SHAs, capsule-on vs AEGIS_CAPSULE=off worktrees, fresh claude -p, measuring
tool-calls-to-first-meaningful-action (spec s7) + correctness. CI-tested core (parser,
worktree, paired CI, decide, fresh-null guard); operator-only run_live_ab behind
AEGIS_RUN_COLDSTART_AB=1. Pre-registered: KEEP-ELIGIBLE iff recon delta>=1.0 & CI low>0 &
fresh-null passes; CI<=0 => KILL; else INCONCLUSIVE. Authorizes a KEEP (cost-measuring),
unlike the synthetic cohort. Next: operator seeds scenarios + runs; live s7 A/B confirms.
