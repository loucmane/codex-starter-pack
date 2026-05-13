# Migration Metrics Collection

- Label: task-55-migration-metrics
- Created at: 2026-05-13T13:38:11+02:00
- Mode: static-file-backed-migration-metrics
- Aggregate status: fail
- Executes external actions: False

## Inputs

- baseline_summary: `scripts/template-ssot-scanner/output/data/baseline_summary.json`
- roadmap: `docs/ai/work-tracking/active/20260513-task55-migration-metrics-collection-ACTIVE/reports/migration-metrics-collection/migration-roadmap-2026-05-13.json`
- security_report: `scripts/template-ssot-scanner/output/data/security_validation.json`

## KPI Summary

- Total KPIs: 9
- Passed: 1
- Warnings: 5
- Failures: 3

## KPIs

| KPI | Value | Unit | Target | Status | Severity | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Migration completion | 37.5 | percent | 100 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Pending migration files | 6 | files | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Broken references | 43 | references | 0 | fail | error | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Circular dependencies | 19 | cycles | 0 | fail | error | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Duplicate files | 4 | files | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Recommended fixes | 45 | fixes | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Security findings | 0 | findings | 0 | pass | info | scripts/template-ssot-scanner/output/data/security_validation.json |
| Critical roadmap items | 24 | items | 0 | fail | error | docs/ai/work-tracking/active/20260513-task55-migration-metrics-collection-ACTIVE/reports/migration-metrics-collection/migration-roadmap-2026-05-13.json |
| Total roadmap items | 51 | items | reviewed backlog | warn | warning | docs/ai/work-tracking/active/20260513-task55-migration-metrics-collection-ACTIVE/reports/migration-metrics-collection/migration-roadmap-2026-05-13.json |

## Roadmap Backlog

- Roadmap: `docs/ai/work-tracking/active/20260513-task55-migration-metrics-collection-ACTIVE/reports/migration-metrics-collection/migration-roadmap-2026-05-13.json`
- Total items: 51
- Priority counts: {'critical': 24, 'high': 24, 'medium': 2, 'low': 1}
- Category counts: {'references': 24, 'dependencies': 19, 'migration': 5, 'duplicates': 2, 'orphaned-files': 1}

## Recommended Refresh Commands

- `python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci`
- `python3 scripts/template-ssot-scanner/baseline_summary.py --data-dir scripts/template-ssot-scanner/output/data`
- `python3 scripts/template-ssot-scanner/migration_roadmap.py --data-dir scripts/template-ssot-scanner/output/data --json-out <roadmap.json> --markdown-out <roadmap.md>`
- `python3 scripts/codex-task migration metrics --baseline-summary <baseline_summary.json> --roadmap <roadmap.json> --security-report <security_validation.json> --report-file <metrics.json> --runbook-file <metrics.md>`
- `python3 scripts/codex-task report generate --kind migration-health`
- `python3 scripts/codex-task validation final-suite --dry-run`

## Non-Goals

- No metric collection agent is started.
- No time-series database is read or written.
- No live dashboard, WebSocket, or hosted observability service is created.
- No alert, notification, ticket, or external webhook is sent.
- No scanner output is regenerated and no remediation mutation is applied.

No metric agent, time-series database, live dashboard, alert delivery, external service call, scanner regeneration, or remediation mutation was executed by this report.
