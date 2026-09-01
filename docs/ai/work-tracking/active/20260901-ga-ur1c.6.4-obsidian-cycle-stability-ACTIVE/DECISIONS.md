# Decisions

- 2026-09-01 — Preserve live lock observation for every external continuity snapshot. The dashboard
  capture is a reconciler-owned post-release candidate and may explicitly project only `idle` after
  project filesystem/live-index gates have committed. Releasing the registry lock before dashboard
  generation was rejected because it would admit concurrent cycles; stripping cycle state from the
  report was rejected because it would hide legitimate in-progress and interrupted observations.
