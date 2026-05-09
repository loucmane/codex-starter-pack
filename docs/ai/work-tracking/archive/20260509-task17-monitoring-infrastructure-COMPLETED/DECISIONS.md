# Decisions

- 2026-05-09 — Implement Task 17 as static, file-based monitoring over existing metrics artifacts instead of deploying live monitoring services.
- 2026-05-09 — Add a repo-local monitoring policy under `templates/metadata/` so alert thresholds can be customized per project without changing helper code.
- 2026-05-09 — Generate monitoring output under `reports/template-monitoring/` and upload it as CI artifact alongside drift and metrics reports.
- 2026-05-09 — Keep strict mode error-based only: warning-level checks should produce visible monitoring findings without failing CI.
