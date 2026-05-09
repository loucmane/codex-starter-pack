# Task 17 Monitoring Infrastructure Scope Reconciliation

**Captured**: 2026-05-09 11:20 CEST  
**Task**: 17 - Setup Monitoring Infrastructure

## Historical Task Wording

Task 17 asks for monitoring infrastructure:

- Prometheus exporters
- Grafana dashboards
- StatsD client for application metrics
- Elasticsearch log aggregation
- alerts for discovery latency, guard failures, and budget thresholds
- migration progress tracker
- telemetry decorators for template loads

That wording came from an earlier migration-service framing. The current repository is a portable foundation/starter-pack with local scripts, GitHub Actions, static reports, Taskmaster state, and work-tracking evidence. It does not run a long-lived application service or ship a production observability stack.

## Current Repository Evidence

- Task 97 already implemented a static `scripts/template-metrics-dashboard` generator that writes `reports/template-metrics/latest.md` and `latest.json`.
- The metrics dashboard is already wired into both guard workflows and uploaded as CI artifacts.
- The metrics snapshot includes Taskmaster status counts, template metadata coverage, drift report data, work-tracking counts, plan-sync data, and wizard adoption.
- Task 98 made `scripts/template-metrics-dashboard` portable through `_repo_structure.load_repo_structure()`.
- Task 45 added scanner performance profiling, but the monitoring dashboard does not yet evaluate report metrics against thresholds.
- There is no repo-local monitoring policy, alert evaluator, or alert-style report that says whether the metrics snapshot is healthy.

## Scope Decision

Task 17 should implement portable, file-based monitoring over existing metrics artifacts. It should not introduce live Prometheus, Grafana, StatsD, Elasticsearch, databases, background daemons, or web services into this starter-pack repository.

Implementation should:

- add a repo-local monitoring policy under `templates/metadata/`
- add a static monitoring evaluator script that reads `reports/template-metrics/latest.json`
- produce `reports/template-monitoring/latest.md` and `latest.json`
- classify checks as pass, warning, or fail based on policy thresholds
- support strict mode so CI can fail only on policy-level errors
- wire monitoring generation after metrics dashboard generation in guard workflows
- expose monitoring through `python3 scripts/codex-task report generate --kind monitoring|all`
- keep all paths portable through `_repo_structure.load_repo_structure()`
- add focused tests for policy loading, threshold evaluation, strict behavior, report rendering, CI wiring, and cross-project roots

## Out of Scope

- Deploying Prometheus, Grafana, StatsD, Elasticsearch, or any service.
- Creating dashboards that require a server, database, or remote account.
- Runtime telemetry decorators for nonexistent application services.
- Live latency monitoring for template discovery beyond static artifact evaluation.
- Cost-budget enforcement until the repo has a real cost telemetry source.
- Replacing the Task 97 metrics dashboard.

## Proven Gap

The repo can generate metrics, but it cannot yet answer:

- Does the current metrics snapshot pass policy thresholds?
- Are drift findings, metadata coverage, active-folder count, or plan-sync activity alert-worthy?
- Can CI surface monitoring output separately from raw metrics?
- Can a new project using the portable foundation inherit monitoring policy and report directories?

## Implementation Boundary For 17.2

Expected code/data/test surface:

- `templates/metadata/template-monitoring-policy.json`
- `scripts/template-monitoring`
- `reports/template-monitoring/README.md`
- `tests/meta_workflow_guard/test_template_monitoring.py`
- targeted updates to `_repo_structure.py`, `scripts/codex-task`, and guard workflow files

Expected behavior:

- monitoring policy loads from the configured templates root
- evaluator reads a metrics JSON payload without mutating the source metrics
- monitoring report includes status summary and per-check findings
- strict mode exits nonzero only when an error-level check fails
- `codex-task report generate --kind all` runs drift, metrics, then monitoring in order
- guard workflows generate and upload `reports/template-monitoring/`

## Verification Plan

- Run focused monitoring tests and existing metrics/codex-task/CI workflow tests.
- Run full pytest before closeout.
- Capture sample monitoring report output under Task 17 reports.
- Capture plan sync, work-tracking audit, guard, diff-check, and Taskmaster health evidence.
