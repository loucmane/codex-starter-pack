# Findings

- 2026-04-24 — The archived `template-metrics-dashboard-draft.md` already captured the right Task 97 scope: repo-local visibility into template usage, drift, plan sync, and workflow health.
- 2026-04-24 — Starting Task 97 exposed a real Task 96 wizard defect: the session `S` token used the full kickoff id suffix and the tracker was not seeded with mirrored kickoff entries, which caused the guard to fail on the generated artifacts.
- 2026-04-24 — Existing repo data is already enough to build a first useful dashboard without adding a service or datastore: Taskmaster JSON, drift reports, plan-sync log, work-tracking folders, and session text provide the needed inputs.
- 2026-04-24 — The initial `scripts/template-metrics-dashboard` implementation failed to import `scripts/codex-guard` because the dynamically loaded module was not registered in `sys.modules`, which breaks dataclass initialization; the loader needs to insert the module before execution.
