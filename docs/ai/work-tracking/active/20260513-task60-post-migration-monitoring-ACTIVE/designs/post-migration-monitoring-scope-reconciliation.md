# Task 60 Post-Migration Monitoring Scope Reconciliation

**Captured**: 2026-05-13 14:28 CEST  
**Task**: 60 - Setup Post-Migration Monitoring

## Historical Task Wording

Task 60 asks for ongoing post-migration monitoring:

- production monitoring dashboards;
- weekly scanner health checks;
- monthly usage reviews;
- quarterly benchmark updates;
- yearly planning reviews;
- automated reports;
- monitoring playbooks;
- monitoring automation.

That wording belongs to the older migration-service framing. The current repository is a portable workflow foundation with static reports, Taskmaster state, GitHub Actions, scanner outputs, and task-local evidence. It does not run a production service, live dashboard backend, alert daemon, scheduler, or hosted observability stack.

## Evidence Reviewed

- Task 17 already implemented `scripts/template-monitoring`, a static monitoring evaluator over `reports/template-metrics/latest.json`.
- Task 37 already implemented `python3 scripts/codex-task report generate --kind telemetry`, the ordered static telemetry pipeline.
- Task 41 already implemented `scripts/template-migration-health-dashboard`, aggregating static telemetry into `reports/migration-health/latest.json` and `.md`.
- Task 55 already implemented `python3 scripts/codex-task migration metrics`, producing scanner-backed migration KPI JSON and Markdown packets.
- `reports/README.md` explicitly states that the foundation does not require Prometheus, Grafana, Elasticsearch, StatsD, a database, or a long-running service.
- `templates/TOOLS.md` documents the static telemetry pipeline and the GitHub auth/signing cache policy.

## Scope Decision

Task 60 should not add live dashboards, background schedulers, webhook alerts, hosted observability integrations, or another monitoring data pipeline.

The current gap is an operator-facing post-migration monitoring packet that composes the existing static reports into a recurring monitoring runbook:

- read an optional migration metrics packet from Task 55;
- read the aggregate migration-health report from Task 41;
- classify aggregate post-migration monitoring status as `pass`, `warn`, or `fail`;
- emit required follow-up actions when source reports are missing, warning, or failing;
- define weekly, monthly, quarterly, and yearly review cadences with exact refresh commands and evidence expectations;
- write deterministic JSON plus Markdown reports;
- expose the behavior as `python3 scripts/codex-task migration monitoring`;
- state explicitly that the command performs no live scheduling, alerting, external calls, telemetry mutation, scanner regeneration, or remediation.

## Out of Scope

- Prometheus, Grafana, StatsD, OpenTelemetry SDK wiring, Elasticsearch, databases, or hosted observability services.
- Cron/systemd/GitHub scheduled workflow creation. Downstream projects can schedule the static command if they want, but this task only defines the portable packet and runbook.
- Slack, email, PagerDuty, ticket, issue, or webhook alert delivery.
- Live production endpoint checks, secret reads, billing API calls, or external service calls.
- Replacing `template-monitoring`, `report generate --kind telemetry`, `template-migration-health-dashboard`, `migration metrics`, or `validation final-suite`.
- Regenerating scanner outputs or applying migration fixes inside the monitoring command.

## Proven Gap

The repository can generate static telemetry and migration metrics, but it cannot yet answer in one portable artifact:

- Which source reports should be reviewed after migration?
- Which source reports are missing, warning, or failing?
- What weekly/monthly/quarterly/yearly checks should an operator run?
- Which exact commands refresh each monitoring input?
- What actions are required before considering post-migration monitoring healthy?
- Can a downstream project inherit the monitoring cadence without adopting a live observability stack?

## Planned Implementation Boundary

Expected code/test/doc surface:

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `reports/post-migration-monitoring/README.md`
- `reports/README.md`
- `templates/TOOLS.md`
- Task 60 work-tracking artifacts and task-local evidence

Expected command shape:

```bash
python3 scripts/codex-task migration monitoring \
  --metrics-report docs/ai/work-tracking/archive/<task55-folder>/reports/migration-metrics-collection/migration-metrics-YYYY-MM-DD.json \
  --migration-health-report reports/migration-health/latest.json \
  --report-file docs/ai/work-tracking/active/<task60-folder>/reports/post-migration-monitoring/post-migration-monitoring-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<task60-folder>/reports/post-migration-monitoring/post-migration-monitoring-YYYY-MM-DD.md
```

## Verification Plan

- Add parser, builder, renderer, handler, missing-input, and strict-mode tests for `migration monitoring`.
- Generate task-local post-migration monitoring JSON and Markdown using the current Task 55 metrics packet plus a fresh migration-health artifact.
- Run focused pytest, plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check before closeout.

## S:W:H:E

- **2026-05-13 14:28 CEST** - [S:20260513|W:task60-post-migration-monitoring|H:docs/scope|E:docs/ai/work-tracking/active/20260513-task60-post-migration-monitoring-ACTIVE/designs/post-migration-monitoring-scope-reconciliation.md] Reconciled Task 60 from live production-monitoring wording to a portable static post-migration monitoring packet over existing telemetry and migration KPI reports.
