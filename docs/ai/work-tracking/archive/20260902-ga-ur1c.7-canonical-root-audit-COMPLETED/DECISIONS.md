# Decisions

- 2026-09-02 — Use only existing local Git refs. Continuity auditing must never fetch or mutate a project merely to decide freshness.
- 2026-09-02 — A checkout on its target branch blocks if ahead or behind; an unresolved target also blocks. A deliberate non-base branch and tracked dirt remain visible as bounded warnings, preserving concurrent operator work.
- 2026-09-02 — Reconcile the stale Operations checkout only after the repair merges, preserving its two pre-existing sync-log records as an exact durable Git object rather than replaying them into a now-advanced generated log.
- 2026-09-02 — Archived through the supported archive helper; no evidence was deleted.
