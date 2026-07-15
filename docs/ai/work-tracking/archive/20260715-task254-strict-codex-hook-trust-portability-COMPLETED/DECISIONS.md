# Decisions

- 2026-07-15 — The tracked `codex.hook_trust` manifest gate is the durable authority for the safe
  review procedure; generated installation reports are supplemental diagnostics only.
- 2026-07-15 — Guidance and actual trust remain separate. The repository never claims a hook hash
  is trusted; changed hook definitions require renewed client-local `/hooks` review.
- 2026-07-15 — Validation is exact and fail-closed: no aliases or weaker hash scopes are accepted,
  and bypass must remain explicitly false.
- 2026-07-15 — Blog acceptance uses temporary in-process tracked-state substitution with guaranteed
  restoration and byte-level inventory comparison; no Blog runtime rollout or Task 42 mutation is
  part of Task 254.
