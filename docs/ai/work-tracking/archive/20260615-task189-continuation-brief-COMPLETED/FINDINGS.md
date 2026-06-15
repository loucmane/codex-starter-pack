# Findings

- 2026-06-15 — Scope reconciliation confirmed the TM 189 spec's three residuals against
  source: (1) named brief schema fields (continue_means / artifact_policy / stop_conditions /
  per-state confirmation_boundary) were absent from `next_action` output; (3) `handle_next`
  dumped full JSON with no concise agent rendering. Both built here. (2) the safe-repair vs
  manual-review split is produced by `doctor`/`repair` but not surfaced as `next_action`
  states — larger, deferred to TM 225.
- 2026-06-15 — `next_action` returns `not_installed` against the codex repo itself: this is the
  Aegis *foundation source*, not a self-install (no `.aegis/foundation-manifest.json`), so the
  brief was verified end-to-end via an installed temp target (install→kickoff→scope) instead.
- 2026-06-15 — The kickoff (run via the Codex wizard) re-introduced the `task-master generate`
  churn signature in `tasks.json`: every task `id` rewritten int→string (223 lines) on top of
  the 2 real status flips. Recurring; restore-and-resurgically-flip is the clean fix.
