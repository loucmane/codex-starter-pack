# Template Usage Analytics Scope Reconciliation

**Task**: 51 - Build Template Usage Analytics  
**Date**: 2026-05-13  
**Branch**: `feat/task-51-template-usage-analytics`

## Current-State Evidence

- Task 51's historical wording asks for usage tracking decorators, a data model, aggregation pipeline, dashboards, trend analysis, anomaly detection, reports, and predictive capacity planning.
- The current portable foundation deliberately uses static, file-backed telemetry. `reports/README.md` says telemetry is generated as local Markdown and JSON artifacts, not Prometheus, Grafana, Elasticsearch, StatsD, a database, or a long-running service.
- Task 97 already created `scripts/template-metrics-dashboard`, which reports Taskmaster status, template metadata compliance, drift, work-tracking turnover, plan sync activity, and wizard adoption.
- Task 37 already added `python3 scripts/codex-task report generate --kind telemetry` as the full static telemetry chain.
- Task 8 already created `scripts/template_registry.py` with `TemplateRegistry` and `TemplateDiscoveryAPI`; registry records expose IDs, paths, categories, statuses, aliases, and metadata suitable for static analytics.
- Task 21 is complete, so template frontmatter/schema dependency is satisfied.

## Stale Requirements

The following pieces are historical and out of scope for this portable foundation unless a future task explicitly reopens them:

- Runtime decorators or instrumentation inside template files.
- A database, warehouse, event stream, long-running aggregation daemon, or external telemetry service.
- A live dashboard, WebSocket server, web UI, Grafana board, or hosted analytics surface.
- Automated anomaly detection services or alert delivery.
- Predictive capacity planning based on runtime traffic.
- Mutation of templates to add usage counters or tracking code.

## Proven Gap

The repo can report high-level workflow metrics, but it does not currently answer these static usage questions:

- Which registered templates are referenced by workflow artifacts?
- Are references using registry IDs, direct template paths, or aliases?
- Which categories and templates appear most in session, plan, Taskmaster, and work-tracking evidence?
- Which registered templates have no observed workflow references?
- Which references suggest adoption gaps, such as path-only usage where an ID-based reference would be more portable?

## Implementation Boundary

Implement a deterministic, non-destructive static usage analytics command:

```bash
python3 scripts/codex-task template usage-analytics \
  --report-file <usage-analytics.json> \
  --runbook-file <usage-analytics.md>
```

The command should:

- Load registered templates through `TemplateRegistry`.
- Scan static workflow sources: `sessions/`, `plans/`, active work-tracking, and `.taskmaster/tasks/`.
- Optionally include archived work-tracking with `--include-archive`.
- Count registry ID, path, and alias references per template.
- Produce source summaries, category summaries, top-template summaries, zero-observed-reference summaries, and static review guidance.
- Emit JSON and Markdown artifacts without mutating templates or external systems.
- Document explicit non-goals in the generated report.

## Acceptance Evidence

- Parser coverage for `template usage-analytics`.
- Unit tests for report construction, path/ID counting, optional archive inclusion, and file outputs.
- Live Task 51 evidence under `docs/ai/work-tracking/active/20260513-task51-template-usage-analytics-ACTIVE/reports/template-usage-analytics/`.
- Plan sync, work-tracking audit, Taskmaster health, guard, and diff-check evidence before closeout.
