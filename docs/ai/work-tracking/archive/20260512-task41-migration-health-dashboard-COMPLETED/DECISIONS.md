# Decisions

- 2026-05-12 — Implement Task 41 as a portable static migration-health dashboard/report. Do not add React, Vue, WebSockets, Prometheus, Grafana, databases, daemons, or external alert delivery for this task.
- 2026-05-12 — Missing telemetry inputs should be reported as visible warning-level components. The report must not fabricate live scanner, billing, performance, or monitoring data.
- 2026-05-12 — Include migration health as the final `report generate --kind telemetry`/`--kind all` stage so it summarizes the already-generated static pipeline artifacts.
