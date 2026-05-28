# Findings

- 2026-05-28 — `closeout_ready` must remain read-only, so handoff repair needs its own explicit repair surface rather than hidden mutation during preflight.
- 2026-05-28 — Existing final `closeout --update-handoff` was useful but too late for the live agent loop; agents need to repair placeholder sections before final closeout.
- 2026-05-28 — MCP handoff repair needs conditional mutation classification: preview is read-only, `apply=true` is persistent and must be tracked.
- 2026-05-28 — Fresh live testing caught branch object rendering from local `aegis start`; automated tests now cover this.
- 2026-05-28 — Fresh live testing caught stale `report_written/state_updated` booleans in the closeout report file; final report writes now happen after those fields are set.
