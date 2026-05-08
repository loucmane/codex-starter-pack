# Decisions

- 2026-05-08 — Implement Task 11 as a scanner-suite roadmap exporter, not as a separate planning subsystem. The generator should read existing scanner outputs and write deterministic markdown plus metadata-wrapped JSON.
- 2026-05-08 — Do not add `matplotlib` for the historical Gantt wording. Current acceptance is a deterministic roadmap with phase/dependency data that future visualization tooling can consume.
- 2026-05-08 — Do not let scanner roadmap generation mutate Taskmaster or apply fixes automatically. Taskmaster-compatible export data is an artifact for review/import, not an execution side effect.
