# Migration Metrics Collection

- Label: migration-metrics
- Created at: 2026-05-15T15:24:52+02:00
- Mode: static-file-backed-migration-metrics
- Aggregate status: warn
- Executes external actions: False

## Inputs

- baseline_summary: `scripts/template-ssot-scanner/output/data/baseline_summary.json`
- roadmap: `docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json`
- security_report: `scripts/template-ssot-scanner/output/data/security_validation.json`

## KPI Summary

- Total KPIs: 9
- Passed: 4
- Warnings: 5
- Failures: 0

## KPIs

| KPI | Value | Unit | Target | Status | Severity | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Migration completion | 37.5 | percent | 100 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Pending migration files | 6 | files | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Broken references | 0 | references | 0 | pass | info | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Circular dependencies | 0 | cycles | 0 | pass | info | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Duplicate files | 4 | files | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Recommended fixes | 2 | fixes | 0 | warn | warning | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Security findings | 0 | findings | 0 | pass | info | scripts/template-ssot-scanner/output/data/security_validation.json |
| Critical roadmap items | 0 | items | 0 | pass | info | docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json |
| Total roadmap items | 8 | items | reviewed backlog | warn | warning | docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json |

## Roadmap Backlog

- Roadmap: `docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json`
- Total items: 8
- Priority counts: {'high': 5, 'medium': 2, 'low': 1}
- Category counts: {'migration': 5, 'duplicates': 2, 'orphaned-files': 1}

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
