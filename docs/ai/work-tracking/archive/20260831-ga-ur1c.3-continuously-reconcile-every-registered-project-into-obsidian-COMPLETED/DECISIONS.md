# Decisions

- 2026-08-31 — Use the canonical workflow project registry plus validated descriptors as the only onboarding source. Filesystem discovery is forbidden; future projects enter through the existing project-onboarding gate and regenerate the same single user unit.
- 2026-08-31 — Keep per-project projections isolated and use `Home.md` as the stable live-index probe, avoiding a dependency on any particular Bead remaining present.
- 2026-08-31 — Derive the global dashboard from the canonical continuity report, not a second ledger classifier. Publish only normalized report fields (Now, Next, Blocked, Drift) and retain the raw snapshot in private state.
- 2026-08-31 — A byte-identical filesystem cycle still performs a bounded managed-note read. It never reloads Obsidian unless bytes changed, separating app observation from publication mutation.
- 2026-08-31 — Archived through the supported archive helper; no evidence was deleted.
