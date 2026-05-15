# Post-Migration Monitoring

- Label: post-migration-monitoring
- Created at: 2026-05-15T15:24:58+02:00
- Mode: static-file-backed-post-migration-monitoring
- Aggregate status: warn
- Executes external actions: False

## Inputs

| Input | Path | Exists | Status | Severity | Generated at |
| --- | --- | --- | --- | --- | --- |
| migration_metrics | docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-metrics-2026-05-15-ssot-clean.json | True | warn | warning | 2026-05-15T15:24:52+02:00 |
| migration_health | reports/migration-health/latest.json | False | missing | warning |  |

## Required Actions

- **warning** - Review warning-level or incomplete migration KPI inputs. `Refresh scanner, roadmap, and security inputs before the next monitoring review.`
- **warning** - Generate the aggregate migration-health report. `python3 scripts/codex-task report generate --kind migration-health`

## Source Highlights

### Migration Metrics

| Item | Status | Severity | Value | Target | Evidence |
| --- | --- | --- | --- | --- | --- |
| Migration completion | warn | warning | 37.5 | 100 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Pending migration files | warn | warning | 6 | 0 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Broken references | pass | info | 0 | 0 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Circular dependencies | pass | info | 0 | 0 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Duplicate files | warn | warning | 4 | 0 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Recommended fixes | warn | warning | 2 | 0 | scripts/template-ssot-scanner/output/data/baseline_summary.json |
| Security findings | pass | info | 0 | 0 | scripts/template-ssot-scanner/output/data/security_validation.json |
| Critical roadmap items | pass | info | 0 | 0 | docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json |
| Total roadmap items | warn | warning | 8 | reviewed backlog | docs/ai/work-tracking/active/20260515-task80-production-deployment-ACTIVE/reports/production-deployment/migration-roadmap-2026-05-15-ssot-clean.json |

## Cadence Plan

| Cadence | Check | Purpose | Commands | Evidence |
| --- | --- | --- | --- | --- |
| weekly | Weekly scanner and migration-health refresh | Keep scanner-derived migration KPIs and aggregate static telemetry current. | `python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci`<br>`python3 scripts/template-ssot-scanner/baseline_summary.py --data-dir scripts/template-ssot-scanner/output/data`<br>`python3 scripts/codex-task report generate --kind telemetry`<br>`python3 scripts/codex-task migration metrics --baseline-summary <baseline_summary.json> --roadmap <roadmap.json> --security-report <security_validation.json> --report-file <metrics.json> --runbook-file <metrics.md>`<br>`python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json --report-file <monitoring.json> --runbook-file <monitoring.md>` | scanner baseline summary<br>migration metrics packet<br>migration health report<br>post-migration monitoring packet |
| monthly | Monthly usage and cost review | Review static cost telemetry and open migration actions before scope drift accumulates. | `python3 scripts/codex-task report generate --kind cost`<br>`python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json --report-file <monitoring.json> --runbook-file <monitoring.md>` | cost tracking report<br>post-migration monitoring packet |
| quarterly | Quarterly benchmark and regression review | Refresh performance baselines and review migration-health trend inputs. | `python3 scripts/template-performance-harness --report-dir reports/template-performance`<br>`python3 scripts/codex-task report generate --kind migration-health`<br>`python3 scripts/codex-task migration monitoring --metrics-report <metrics.json> --migration-health-report reports/migration-health/latest.json --report-file <monitoring.json> --runbook-file <monitoring.md>` | template performance report<br>migration health report<br>post-migration monitoring packet |
| yearly | Yearly roadmap and planning review | Regenerate the migration roadmap and compare remaining work against Taskmaster health. | `python3 scripts/template-ssot-scanner/migration_roadmap.py --data-dir scripts/template-ssot-scanner/output/data --json-out <roadmap.json> --markdown-out <roadmap.md>`<br>`python3 scripts/codex-task taskmaster health --report-file <taskmaster-health.txt>`<br>`python3 scripts/codex-task validation final-suite --dry-run` | migration roadmap<br>Taskmaster health report<br>final validation dry-run |

## Automation Guidance

- report_refresh: Run static report commands manually, in CI, or in a reviewed scheduler owned by the downstream project.
- default_review_packet: Store the generated JSON and Markdown packet as task-local evidence before acting on findings.
- strict_gate: Use --strict only when fail-level post-migration status should fail the caller.

## Non-Goals

- No scheduler, daemon, cron job, or background worker is installed.
- No Prometheus, Grafana, OpenTelemetry, Elasticsearch, StatsD, or database service is configured.
- No Slack, email, PagerDuty, ticket, issue, or webhook alert is sent.
- No scanner output, telemetry artifact, Taskmaster state, or remediation file is mutated by this report.
- No live production endpoint, secret, billing account, or hosted observability backend is contacted.

This packet is a static review artifact. It coordinates existing reports and review cadences, but it does not install or execute a production monitoring system.
