# Decisions

- 2026-04-24 — Implement Task 97 as a static file generator that writes `reports/template-metrics/latest.md` and `latest.json` instead of introducing a web app or database.
- 2026-04-24 — Reuse `scripts/codex-guard` helpers for template metadata coverage so the dashboard reports the same source of truth as the enforcement layer.
- 2026-04-24 — Normalize the Task 97 kickoff artifacts in-place rather than discarding the wizard kickoff; the defect is part of the implementation history and should stay documented.
- 2026-04-24 — Generate the metrics dashboard in both guard workflows and upload `reports/template-metrics/` as a CI artifact so the dashboard stays refreshed automatically.
