# Decisions

- 2026-09-01 — Preserve live lock observation for every external continuity snapshot. The dashboard
  capture is a reconciler-owned post-release candidate and may explicitly project only `idle` after
  project filesystem/live-index gates have committed. Releasing the registry lock before dashboard
  generation was rejected because it would admit concurrent cycles; stripping cycle state from the
  report was rejected because it would hide legitimate in-progress and interrupted observations.
- 2026-09-01 — Treat `GasCity/<project>/Aegis` as a generated, manifest-owned projection: a pure
  missing-file condition is self-healable only when no unknown or modified survivor exists and the
  current renderer proves the exact prior digest for every overlapping missing path. Synchronous
  gates remain strict until the atomic repair completes.
- 2026-09-01 — Installer snapshots are valid only after the timer is stopped and the oneshot service
  is inactive. A timer may not be started until the installed reconciliation and strict check pass.
  Rollback restores stable scheduler semantics; transient `running/start` observations are evidence
  of an in-flight cycle, not a state to recreate.
