# Decisions

- 2026-06-09 — Treat completed observations as terminal current-work, not active observation mode. Readiness should no longer require `in-progress` observation state after completion; it should fall back to normal kickoff/task binding.
- 2026-06-09 — Do not make completed observations READY for arbitrary mutation on `main`. Persistent writes still require a new kickoff or task-bound branch.
- 2026-06-09 — Make `observe stop` idempotent after completion so a repeated stop reports `already_completed` instead of producing a misleading error.
