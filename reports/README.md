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

Operational runbook packets can be generated when an operator needs one consolidated procedure index over the existing static helpers:

```bash
python3 scripts/codex-task operations runbook \
  --label <label> \
  --report-file <operational-runbook.json> \
  --runbook-file <operational-runbook.md>
```

This command composes daily work, recurring maintenance, incident response, escalation, troubleshooting, and validation guidance from existing helpers. It does not install schedulers, send notifications, create tickets, update dashboards, deploy code, execute rollback, or mutate external operations systems.

Incident post-mortem packets can be generated after a workflow incident or emergency response when an operator needs a static RCA, timeline, follow-up, and prevention artifact:

```bash
python3 scripts/codex-task incident post-mortem \
  --summary <summary> \
  --severity <P0-P3> \
  --timeline "<timestamp>|<phase>|<description>|<evidence>" \
  --root-cause "<category>|<description>" \
  --action-item "<owner>|<description>|<status>|<due>" \
  --prevention "<measure>|<verification command>|<status>" \
  --report-file <post-mortem.json> \
  --runbook-file <post-mortem.md>
```

This command records supplied incident facts, timeline entries, root causes, action items, prevention measures, lessons learned, and static metrics. It does not create tickets, send notifications, update dashboards, scrape timelines, infer blame, mutate Taskmaster/session/work-tracking state beyond requested artifacts, install schedulers, or contact external incident systems.

Template usage analytics packets can be generated when an operator needs a registry-backed view of how templates are referenced by workflow artifacts:

```bash
python3 scripts/codex-task template usage-analytics \
  --report-file reports/template-usage-analytics/latest.json \
  --runbook-file reports/template-usage-analytics/latest.md
```

This command scans static workflow evidence and reports registry ID, path, and alias references. It does not add runtime decorators, create a database, run a live dashboard, send alerts, train predictive models, mutate templates, or contact external analytics services.

Phase 3 automation integration review packets can be generated when an operator needs one gate-review artifact over the automation layer:

```bash
python3 scripts/codex-task automation phase3-review \
  --report-file reports/phase3-automation-integration/latest.json \
  --runbook-file reports/phase3-automation-integration/latest.md
```

This command composes CI/CD gates, guard auto-fix, cost tracking, canary rollout, usage analytics, migration health, operational runbook, and final validation readiness into a static review packet. It does not deploy code, wait five days, run production auto-fix, split traffic, start monitoring services, create dashboards, send notifications, install schedulers, or contact external systems.

Phase 4 documentation delivery review packets can be generated when an operator needs one gate-review artifact over repository-native documentation, training, communication, operations, Phase 3, and final validation evidence:

```bash
python3 scripts/codex-task documentation phase4-review \
  --report-file reports/phase4-documentation-delivery/latest.json \
  --runbook-file reports/phase4-documentation-delivery/latest.md
```

This command classifies each delivery domain as ready, needs-evidence, or needs-implementation and lists refresh commands for evidence gaps. It does not publish hosted documentation, deploy training, schedule office hours, send communications, collect surveys, update dashboards, mutate existing evidence sources, or contact external systems.

Knowledge transfer review packets can be generated when an operator needs one static readiness artifact over repository-native documentation, onboarding, troubleshooting, communication, continuity, handoff, and validation evidence:

```bash
python3 scripts/codex-task knowledge transfer-review \
  --report-file reports/knowledge-transfer-process/latest.json \
  --runbook-file reports/knowledge-transfer-process/latest.md
```

This command classifies each knowledge-transfer domain as ready, needs-evidence, or needs-implementation and lists refresh commands for evidence gaps. It does not create hosted knowledge-base software, produce videos, run Q&A systems, create analytics dashboards, maintain contact databases, send notifications, mutate existing evidence sources, or contact external systems.

Deprecation management review packets can be generated when an operator needs one static gate-review artifact over lifecycle policy, lifecycle audit metrics, versioning policy, communication guidance, operational runbook guidance, emergency/recovery guidance, and final validation evidence:

```bash
python3 scripts/codex-task deprecation review \
  --today <YYYY-MM-DD> \
  --report-file reports/deprecation-management/latest.json \
  --runbook-file reports/deprecation-management/latest.md
```

This command summarizes lifecycle status counts, deprecation warnings, grace-period expirations, archive recommendations, missing migration guidance, supporting evidence domains, and operator-reviewed deprecation actions. It does not instrument runtime logs, move files automatically, send notifications, install schedulers, update dashboards, automate emergency overrides, mutate existing evidence sources, or contact external systems.

## Report Directories

- `template-drift/` - drift checks for guard guidance, metadata policy coverage, and command-surface availability.
- `template-metrics/` - repo-level metrics snapshot from Taskmaster, metadata, drift, work tracking, plan sync, and session history.
- `template-monitoring/` - policy evaluation over the latest metrics snapshot.
- `phase0-scanner-validation/` - static validation over scanner outputs and monitoring status.
- `template-performance/` - performance and regression checks for portable foundation operations.
- `cost-tracking/` - cost policy evaluation using optional usage data.
- `migration-health/` - aggregate health report over the latest static telemetry artifacts.
- `post-migration-monitoring/` - optional static monitoring packets that combine migration KPIs, migration health, and recurring review cadences.
- `operational-runbook/` - optional static operator runbook packets that compose daily, recurring, incident, escalation, and validation procedures.
- `post-mortem-process/` - optional static incident post-mortem packets with timeline, RCA, action, prevention, lesson, and metric sections.
- `template-usage-analytics/` - optional static registry-backed usage analytics over sessions, plans, work tracking, and Taskmaster task files.
- `phase3-automation-integration/` - optional static Phase 3 gate-review packets over existing automation evidence and refresh commands.
- `phase4-documentation-delivery/` - optional static Phase 4 gate-review packets over documentation, training, communication, operations, Phase 3, and final validation evidence.
- `knowledge-transfer-process/` - optional static knowledge-transfer review packets over documentation, onboarding, troubleshooting, communication, continuity, handoff, and validation evidence.
- `deprecation-management/` - optional static deprecation-management review packets over lifecycle audit metrics, versioning, communication, operations, emergency/recovery, and validation evidence.

## Task Evidence

Task-specific evidence should still live under the active work-tracking folder:

```text
docs/ai/work-tracking/active/<YYYYMMDD-task-slug-ACTIVE>/reports/<task-slug>/
```

Repo-level reports under `reports/` are reusable snapshots and CI artifacts. Task-local reports are the audit trail for a specific Taskmaster task.
