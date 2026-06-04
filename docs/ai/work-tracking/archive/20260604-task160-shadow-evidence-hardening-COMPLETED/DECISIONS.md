# Decisions

- 2026-06-04 — Reuse `_taskmaster_state` for shadow authority checks instead of maintaining a separate local JSON parser. This keeps shadow evidence aligned with the same Taskmaster validity model used by Aegis surfaces.
- 2026-06-04 — Treat `.taskmaster/state.json` as an optional path delta but not an unchecked content delta. Managed timestamp/migration bookkeeping may appear or refresh; active tag changes, branch mapping rewrites, malformed values, unknown keys, and invalid JSON refuse as measurement drift.
- 2026-06-04 — Move CI shadow accumulation output to runner temp and assert zero governed-repo deltas. This is stronger than allowing a declared in-repo report path and matches the artifact-only evidence model.
