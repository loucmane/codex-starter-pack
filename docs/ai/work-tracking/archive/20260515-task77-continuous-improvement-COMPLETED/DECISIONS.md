# Decisions

- 2026-05-15 — Implement Task 77 as a static continuous-improvement review packet, not a live improvement platform. The current portable foundation favors deterministic file-backed evidence and explicit non-goals over hosted services, schedulers, dashboards, notifications, databases, or external integrations.
- 2026-05-15 — Place the command under the existing `enhancement` command group as `enhancement continuous-improvement`. Continuous improvement is the operating review over feedback, roadmap, metrics, experiment, validation, learning, and cadence evidence; it naturally extends the existing enhancement planning surface without creating a new top-level workflow engine.
- 2026-05-15 — Treat missing source evidence as `needs-evidence` instead of fabricating completeness. The packet is review evidence only; accepted improvements still require explicit Taskmaster tasks, scope reconciliation, tests, and handoff evidence.
