# Decisions

- 2026-06-09 — Allow only safe Aegis repair apply through BLOCKED readiness. The gate should not generalize this to arbitrary Aegis mutations: closeout, kickoff, Taskmaster writes, file writes, and compounded shell commands remain blocked when readiness is BLOCKED.
- 2026-06-09 — Keep target-dir confinement and pending-tracking enforcement ahead of the repair allowance. A repair apply targeting outside the governed root still fails before readiness, and pending S:W:H:E entries still require `aegis log`.
