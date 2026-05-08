# Findings

- 2026-05-08 — Task 22's REST, Redis, and GraphQL wording is historical. Current repository evidence shows `scripts/template_registry.py` already owns discovery, caching, compatibility fallback, metadata parsing, and search.
- 2026-05-08 — The useful remaining gap is a stable serializable discovery facade around `TemplateRegistry`, especially pagination, status/version filtering, and normalized dependency output.
- 2026-05-08 — `task-master update-task --id=22` refused to rewrite the completed parent task details because completed tasks are locked. The current scope authority is therefore the Task 22 scope reconciliation artifact and work-tracking record, while the parent task's original detail text remains historical context.
