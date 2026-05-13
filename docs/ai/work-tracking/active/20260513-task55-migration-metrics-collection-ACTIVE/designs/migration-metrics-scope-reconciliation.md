# Task 55 Migration Metrics Scope Reconciliation

**Captured**: 2026-05-13 13:30 CEST  
**Task**: 55 - Implement Migration Metrics Collection

## Historical Task Wording

Task 55 asks for a comprehensive migration metrics system:

- KPI metrics for migration success;
- metric collection agents;
- aggregation pipeline;
- time-series database storage;
- visualization dashboards;
- metric alerting;
- metric reports;
- export capabilities.

That wording belongs to the older migration-service framing. The current repository is a portable workflow foundation with local scanners, deterministic reports, Taskmaster state, GitHub Actions, session/work-tracking evidence, and no long-running service or production migration runtime.

## Evidence Reviewed

- Task 37 reconciled telemetry to the static `python3 scripts/codex-task report generate --kind telemetry` pipeline.
- Task 17 added static monitoring over `reports/template-metrics/latest.json`.
- Task 41 added `scripts/template-migration-health-dashboard` to aggregate telemetry component health.
- Task 68 added `python3 scripts/codex-task validation final-suite` to orchestrate final sign-off evidence.
- Task 23 added a non-destructive migration rehearsal planner over scanner roadmap and rollback checkpoint inputs.
- `scripts/template-ssot-scanner/baseline_summary.py` already produces scanner-derived raw migration metrics.
- `scripts/template-ssot-scanner/migration_roadmap.py` already produces prioritized roadmap metrics and phase data.
- `scripts/template-ssot-scanner/security_validator.py` already produces scanner-backed security finding counts.

## Scope Decision

Task 55 should not add collection agents, background services, time-series storage, live dashboards, external alerting, or fake runtime telemetry.

The current gap is a dedicated migration KPI packet that combines the existing scanner baseline, optional roadmap, and optional security validation outputs into one file-backed report with explicit success criteria and exportable JSON/Markdown artifacts.

Implementation should:

- read metadata-wrapped `baseline_summary.json` from the scanner output directory;
- optionally read a migration roadmap JSON produced by `migration_roadmap.py`;
- optionally read `security_validation.json`;
- compute migration KPIs for completion, pending migration, references, dependencies, duplicates, fixes, security, and roadmap backlog;
- classify aggregate status as `pass`, `warn`, or `fail` without failing normal report generation;
- support strict mode for callers that want fail-level KPIs to exit nonzero;
- write deterministic JSON plus Markdown reports;
- expose the behavior as `python3 scripts/codex-task migration metrics`;
- state explicitly that the command performs no live collection, database writes, dashboards, notifications, or remediation mutations.

## Out Of Scope

- Time-series databases, retention policies, metrics collectors, agents, daemons, or schedulers.
- Prometheus, Grafana, Elasticsearch, WebSockets, dashboards, or hosted observability services.
- Slack, email, PagerDuty, GitHub Issue, or webhook alert delivery.
- Replacing `template-metrics-dashboard`, `template-monitoring`, `template-migration-health-dashboard`, or `validation final-suite`.
- Regenerating scanner outputs or applying fixes inside the metrics command.

## Proven Gap

The repository can generate individual static reports, but it does not yet provide one migration-focused KPI packet that answers:

- What is the current migration completion percentage?
- How many files remain pending, partially migrated, or not migrated?
- Which integrity blockers still affect migration readiness?
- How many roadmap items exist by priority and category?
- Which source artifacts support those metrics?
- What command should an operator run next to refresh the source evidence?

## Planned Implementation Boundary

Expected code/test surface:

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- Task 55 work-tracking artifacts and task-local evidence

Expected command shape:

```bash
python3 scripts/codex-task migration metrics \
  --baseline-summary scripts/template-ssot-scanner/output/data/baseline_summary.json \
  --roadmap docs/ai/work-tracking/active/<folder>/reports/migration-metrics-collection/migration-roadmap-YYYY-MM-DD.json \
  --security-report scripts/template-ssot-scanner/output/data/security_validation.json \
  --report-file docs/ai/work-tracking/active/<folder>/reports/migration-metrics-collection/migration-metrics-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/migration-metrics-collection/migration-metrics-YYYY-MM-DD.md
```

## Verification Plan

- Add parser, builder, renderer, and handler tests for `migration metrics`.
- Generate a task-local roadmap from current scanner outputs.
- Generate a task-local migration metrics JSON and Markdown report.
- Run focused pytest, plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check before closeout.

## S:W:H:E

- **2026-05-13 13:30 CEST** - [S:20260513|W:task55-migration-metrics-collection|H:docs/scope|E:docs/ai/work-tracking/active/20260513-task55-migration-metrics-collection-ACTIVE/designs/migration-metrics-scope-reconciliation.md] Reconciled Task 55 from live metrics infrastructure wording to a portable scanner-backed migration KPI packet.
