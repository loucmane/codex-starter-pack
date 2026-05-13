# Decisions

- 2026-05-13 13:30 CEST — Implement Task 55 as `python3 scripts/codex-task migration metrics`, a deterministic JSON/Markdown KPI packet over existing scanner evidence, rather than live collection agents, time-series storage, dashboards, or alert delivery.
- 2026-05-13 13:30 CEST — Keep the command non-destructive: it may read baseline, roadmap, and security JSON and write requested report files, but it must not regenerate scanner outputs, apply fixes, open tickets, send notifications, mutate Taskmaster, or call external services.
