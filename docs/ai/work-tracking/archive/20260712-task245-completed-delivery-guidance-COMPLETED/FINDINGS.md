# Findings

- 2026-07-12 — `_post_closeout_delivery_guidance` returns `delivery_unknown` on a recorded/current branch mismatch before querying merged pull requests. Blog Task 67 therefore remained non-terminal after PR #28 merged into synchronized `main`.
- 2026-07-12 — `_closeout_passed` accepts any global passed closeout report without checking whether that report belongs to the current task. After Blog Task 38 kickoff, the retained Task 67 report could still arm delivery guidance for the newer envelope.
- 2026-07-12 — The installer already has `_closeout_report_matches_current_work`, including task-ID and work-tracking identity parity, in the doctor/repair path. Reusing that predicate keeps readiness, guidance, and repair from inventing competing identity rules.
- 2026-07-12 — A GitHub `MERGED` label alone is insufficient terminal proof. The local branch must be the PR base, the merge commit must be contained by local `HEAD`, and `HEAD` must be synchronized with its configured upstream.
- 2026-07-12 — A read-only replay against the current Blog Task 38 state returns `closeout_required` under `taskmaster:38`, confirming the retained Task 67 closeout report no longer arms post-closeout delivery for a newer task.
