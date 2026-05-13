# Decisions

- 2026-05-13 — Implement Task 51 as a deterministic static usage analytics report, not as runtime tracking infrastructure. The command will scan workflow artifacts and emit JSON/Markdown evidence.
- 2026-05-13 — Use `TemplateRegistry` as the source of template records so usage analytics stays aligned with the portable registry system.
- 2026-05-13 — Keep archive scanning optional. Default analytics should scan sessions, plans, active work-tracking, and Taskmaster task files; `--include-archive` may be used for historical work-tracking review.
- 2026-05-13 — Document the report under `reports/template-usage-analytics/` and `templates/TOOLS.md` without adding it to the full telemetry chain yet. The command is task/operator-invoked until a future telemetry task proves it should be a mandatory pipeline stage.
