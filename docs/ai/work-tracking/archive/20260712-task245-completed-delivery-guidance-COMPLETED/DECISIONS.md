# Decisions

- 2026-07-12 — Evaluate a recorded branch's merged PR before emitting historical branch-mismatch guidance, but only when local base-branch and synchronization proof is complete.
- 2026-07-12 — Treat a passed closeout report as current only when `_closeout_report_matches_current_work` succeeds. Preserve an envelope's own `closeout_passed_at` compatibility independently.
- 2026-07-12 — Add `mergeCommit` to existing GitHub PR projections rather than introducing another GitHub query mechanism.
- 2026-07-12 — Keep missing, malformed, behind, ahead, wrong-base, and non-ancestor evidence in `delivery_unknown`; Task 245 adds no mutation or repair path.
