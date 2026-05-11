# Decisions

- 2026-05-11 — Implement Task 62 as a file-backed compatibility layer: canonical matrix data plus a validating/reporting `codex-task` helper. This satisfies the historical capability/version/feature/fallback/metrics requirements without duplicating Task 13 template path compatibility or building a new runtime service.
- 2026-05-11 — Treat the MCP installer idea as a future consumer, not Task 62's first implementation. The compatibility matrix must exist before a portable installer or MCP server can safely install/adapt the system in other repositories.
