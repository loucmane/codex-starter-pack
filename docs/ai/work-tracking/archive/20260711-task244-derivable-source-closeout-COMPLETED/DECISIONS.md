# Decisions

- 2026-07-11 — Source-only derivation is fail-closed and read-only; installed targets retain
  manifest/current-work authority.



## Progress Log

- **2026-07-11 23:10** — [S:20260711|W:task244-derivable-source-closeout|H:docs/decisions|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/designs/source-closeout-derivation-contract.md] Use one stdlib-only source resolver shared by source readiness and guard; require branch, done Taskmaster task, one in-root completed archive, and completed tracker identity; never activate the fallback when an installed manifest or current-work state exists.
- **2026-07-11 23:31** — [S:20260711|W:task244-derivable-source-closeout|H:docs/decisions|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/reports/derivable-source-closeout/task-verification.md] Make evidence-reference relocation and plan-sync refresh part of the supported archive transition so a truthful folder move cannot invalidate the terminal guard.
- **2026-07-12 02:11** — [S:20260712|W:task244-derivable-source-closeout|H:docs/decisions|E:docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED/designs/source-closeout-derivation-contract.md] Reuse the fail-closed source resolver for next-day terminal sessions, while deferring the unrelated stdio smoke reader race to its own task.
