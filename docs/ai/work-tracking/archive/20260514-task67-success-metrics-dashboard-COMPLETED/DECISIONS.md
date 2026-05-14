# Decisions

- 2026-05-14 — Implement Task 67 as `python3 scripts/codex-task success metrics`, a static JSON/Markdown success scorecard over existing evidence. This follows Tasks 41, 55, 60, and 97 and avoids inventing a live dashboard runtime that the repository does not have.
- 2026-05-14 — Treat predictive metrics, live KPI widgets, databases, alerting, and external dashboards as out of scope. Future runtime dashboard work requires a separate Taskmaster task with proven product/runtime need.
- 2026-05-14 — Do not manually edit `.taskmaster/tasks/tasks.json` to correct stale parent wording. Because Taskmaster locks completed tasks and the AI-backed update path failed, preserve the authoritative reconciliation in subtasks, plan, design, tracker, and evidence instead.
