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
- 2026-09-02 — Live acceptance observed the writer lock before invoking the host doctor. The
  doctor blocked for 25.946877379 seconds, then returned `overall=ready` with 20 pass, zero fail,
  zero warn, and zero unknown checks. The first evidence validator expected an obsolete uppercase
  `status=READY` shape and stopped after the successful doctor run; the preserved result was
  validated append-forward against the actual schema (`overall=ready`, lowercase `pass`) without
  repeating the live reconciliation cycle.
