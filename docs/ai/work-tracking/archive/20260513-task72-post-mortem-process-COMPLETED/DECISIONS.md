# Decisions

- 2026-05-13 — Implement Task 72 as `python3 scripts/codex-task incident post-mortem`, a non-destructive static packet command. It will accept explicit timeline, RCA, action, prevention, and lesson entries, compute simple static metrics, and write requested JSON/Markdown artifacts. It will not create tickets, send notifications, update dashboards, infer blame, install follow-up schedulers, or mutate Taskmaster/session/plan/work-tracking state beyond requested report artifacts.
