# Findings

- 2026-05-08 — Existing training/user-guide material is Claude-centered and predates the current portable Codex foundation plus Claude runtime adapter.
- 2026-05-08 — `templates/guides/index.md` references missing guide paths including `quickstart/first-request.md`, `reference/quick-actions.md`, `troubleshooting/errors.md`, `troubleshooting/performance.md`, `workflows/advanced.md`, and advanced handler/system-extension pages.
- 2026-05-08 — Current foundation adoption docs already exist in `templates/engine/validation/foundation-adoption-guide.md`, and runtime enforcement docs exist in `.claude/engine/runtime-contract.md`; Task 33 should connect users to these rather than recreating them.
- 2026-05-08 — The repository lacks a concise hands-on training path that teaches the current session, plan, work-tracking, guard, PR, and archive workflow as a repeatable exercise.
- 2026-05-08 — Focused guide tests can keep Task 33 maintainable by checking only the current training guide and guide hub rather than attempting a broad repository-wide markdown link audit.
