# Findings

- 2026-09-02 — The false reboot-readiness failure is a reader/writer coordination defect, not a
  freshness or Obsidian failure. `reconcile_registry()` correctly owns
  `registry-cycle.lock` as the sole writer, but `check_registry()` used the same nonblocking
  acquisition as a second writer and immediately returned `ok=false,status=already-running`.
- 2026-09-02 — The repair belongs at the reconciler API, not in the reboot doctor. Health checks
  now wait at most 60 seconds for the active writer and then inspect one coherent post-cycle
  snapshot. An expired bound returns `lock-timeout` without exporting Beads, reading ledgers, or
  inspecting partial vault state.
- 2026-09-02 — Reconciliation concurrency remains unchanged: a second writer still returns the
  successful non-mutating `already-running` no-op immediately. The new wait applies only to the
  read-only check boundary.
