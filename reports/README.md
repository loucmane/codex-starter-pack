# Workflow Telemetry Reports

This directory contains file-based telemetry, monitoring, and governance reports for the portable Codex foundation.

The foundation does not require Prometheus, Grafana, Elasticsearch, StatsD, a database, or a long-running service. Telemetry is generated as local Markdown and JSON artifacts that can be committed as task-local evidence or uploaded by CI.

## Full Telemetry Pipeline

Run the full static telemetry pipeline with:

```bash
python3 scripts/codex-task report generate --kind telemetry \
  --strict-drift \
  --strict-monitoring \
  --strict-phase0 \
  --strict-performance \
  --strict-cost \
  --strict-migration-health
```

`--kind telemetry` is a semantic alias for the full report chain. `--kind all` remains supported for backward compatibility.

The pipeline runs stages in this order:

1. `scripts/codex-guard drift-check` -> `reports/template-drift/`
2. `scripts/template-metrics-dashboard` -> `reports/template-metrics/`
3. `scripts/template-monitoring` -> `reports/template-monitoring/`
4. `scripts/template-phase0-validation` -> `reports/phase0-scanner-validation/`
5. `scripts/template-performance-harness` -> `reports/template-performance/`
6. `scripts/template-cost-report` -> `reports/cost-tracking/`
7. `scripts/template-migration-health-dashboard` -> `reports/migration-health/`

Post-migration monitoring packets can be generated after those source artifacts exist:

```bash
python3 scripts/codex-task migration monitoring \
  --metrics-report <migration-metrics.json> \
  --migration-health-report reports/migration-health/latest.json \
  --report-file <post-migration-monitoring.json> \
  --runbook-file <post-migration-monitoring.md>
```

This command composes existing static reports into weekly/monthly/quarterly/yearly review guidance. It does not install a scheduler, create a live dashboard, send alerts, or contact external observability services.

## Report Directories

- `template-drift/` - drift checks for guard guidance, metadata policy coverage, and command-surface availability.
- `template-metrics/` - repo-level metrics snapshot from Taskmaster, metadata, drift, work tracking, plan sync, and session history.
- `template-monitoring/` - policy evaluation over the latest metrics snapshot.
- `phase0-scanner-validation/` - static validation over scanner outputs and monitoring status.
- `template-performance/` - performance and regression checks for portable foundation operations.
- `cost-tracking/` - cost policy evaluation using optional usage data.
- `migration-health/` - aggregate health report over the latest static telemetry artifacts.
- `post-migration-monitoring/` - optional static monitoring packets that combine migration KPIs, migration health, and recurring review cadences.

## Task Evidence

Task-specific evidence should still live under the active work-tracking folder:

```text
docs/ai/work-tracking/active/<YYYYMMDD-task-slug-ACTIVE>/reports/<task-slug>/
```

Repo-level reports under `reports/` are reusable snapshots and CI artifacts. Task-local reports are the audit trail for a specific Taskmaster task.
