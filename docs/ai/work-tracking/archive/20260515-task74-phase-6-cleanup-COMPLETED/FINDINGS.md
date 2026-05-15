# Findings

- 2026-05-15 — Historical Phase 6 wording is stale. Current evidence shows no root markdown monoliths above the Task 1 threshold and no stale active work-tracking folder beyond Task 74 itself.
- 2026-05-15 — Root `output/` is the proven cleanup gap. `git ls-files output` reports seven tracked generated scanner artifacts, and those artifacts contain stale `PROJECT-BLOG`, `WORKFLOWS.md`, and `PATTERNS.md` evidence from earlier migration runs.
- 2026-05-15 — Root `output/` is not ignored. A scope probe using the old scanner baseline helper created an untracked root `output/data/baseline_summary.json`, confirming the directory can still collect commit-visible generated artifacts unless `.gitignore` covers it.
