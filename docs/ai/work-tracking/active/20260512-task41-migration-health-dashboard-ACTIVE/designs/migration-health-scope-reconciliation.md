# Task 41 Migration Health Dashboard Scope Reconciliation

**Captured**: 2026-05-12 17:51 CEST  
**Task**: 41 - Build Migration Health Dashboard

## Historical Task Wording

Task 41 asks for a real-time migration dashboard with:

- React or Vue UI
- WebSocket live updates
- migration progress bar and phase indicators
- scanner and guard status
- performance graphs
- cost usage gauge
- alert panel
- error-rate trending
- team blockers section
- mobile responsive UI tests

That wording comes from the older migration-service framing. The current repository is a portable Codex workflow foundation with local scripts, Taskmaster state, static Markdown/JSON reports, GitHub Actions, session/work-tracking evidence, and no long-running application service.

## Evidence Reviewed

- `templates/TOOLS.md` defines the current telemetry model as file-based, not Prometheus/Grafana/WebSocket/service-backed.
- `reports/README.md` documents the static telemetry pipeline: drift, metrics, monitoring, Phase 0 validation, performance, and cost.
- `scripts/codex-task report generate --kind telemetry` already runs the ordered static pipeline through existing helper scripts.
- Task 97 implemented `scripts/template-metrics-dashboard` for repo-level metrics.
- Task 17 implemented `scripts/template-monitoring` for policy evaluation over metrics.
- Task 25 implemented `scripts/template-phase0-validation` for scanner/monitoring gate state.
- Task 16 implemented `scripts/template-performance-harness`.
- Task 24 implemented `scripts/template-cost-report`.
- The current `reports/` root has reusable static report directories for metrics and performance; monitoring, Phase 0, and cost directories are present but may not have current `latest.json` artifacts until the telemetry pipeline is rerun.

## Scope Decision

Task 41 should not add a React/Vue dashboard, WebSocket server, live database, background daemon, or external observability stack.

The correct current-state implementation is a portable, file-backed migration health dashboard/report that aggregates the existing static telemetry artifacts into one operator-facing Markdown/JSON health view.

Implementation should:

- read existing telemetry outputs from `reports/template-metrics/`, `reports/template-monitoring/`, `reports/phase0-scanner-validation/`, `reports/template-performance/`, and `reports/cost-tracking/`;
- tolerate missing optional report files by surfacing them as visible warning-level health components rather than inventing live data;
- classify each component as `pass`, `warn`, `fail`, or `missing`;
- compute an aggregate migration-health status where fail-level components fail the report and missing/warn components warn the report;
- write `reports/migration-health/latest.md` and `latest.json`;
- expose generation through `python3 scripts/codex-task report generate --kind migration-health`;
- optionally include migration-health as the final stage of `--kind telemetry` / `--kind all` after cost;
- keep path discovery portable through `_repo_structure.load_repo_structure()`;
- add focused tests for status aggregation, missing-artifact handling, report writing, codex-task wiring, documentation, and cross-project report roots.

## Out of Scope

- React, Vue, WebSocket, mobile UI, or browser dashboard implementation.
- Prometheus, Grafana, Elasticsearch, StatsD, OpenTelemetry SDK wiring, databases, or daemons.
- Team blocker input forms or project-management UI.
- Runtime alert delivery to Slack, email, PagerDuty, GitHub Issues, or webhooks.
- Creating fake scanner, billing, performance, or monitoring data when source reports are absent.
- Replacing the existing metrics, monitoring, Phase 0, performance, or cost reports.

## Proven Gap

The repository can generate individual static telemetry artifacts, but it cannot yet answer in one file:

- Is the current migration/foundation state healthy overall?
- Which telemetry components are passing, warning, failing, or missing?
- Which report files support the current status?
- What should an operator run next when a component is missing or stale?
- Can downstream projects inherit a single portable migration-health report contract?

## Implementation Boundary For 41.2

Expected code/data/test surface:

- `scripts/template-migration-health-dashboard`
- `scripts/_repo_structure.py`
- `scripts/codex-task`
- `reports/migration-health/README.md`
- `tests/meta_workflow_guard/test_migration_health_dashboard.py`
- targeted updates to `reports/README.md`, `templates/TOOLS.md`, and codex-task/report tests

Expected behavior:

- missing input files are visible as `missing` warning components;
- malformed input files are fail-level components;
- source report statuses map predictably into migration-health status;
- Markdown output lists every component with evidence path and recommended review command;
- JSON output is deterministic enough for tests and CI artifacts;
- `--strict-migration-health` exits nonzero only when aggregate status is `fail`;
- `report generate --kind telemetry` runs migration health after cost so it summarizes the full static pipeline.

## Verification Plan

- Run focused migration-health tests.
- Run codex-task report-generation tests touched by the new kind.
- Generate sample task-local migration-health output under this active work-tracking folder.
- Capture plan sync, work-tracking audit, guard, diff-check, Taskmaster health, and focused pytest evidence before closeout.

## S:W:H:E

- **2026-05-12 17:51 CEST** - [S:20260512|W:task41-migration-health-dashboard|H:docs/scope|E:docs/ai/work-tracking/active/20260512-task41-migration-health-dashboard-ACTIVE/designs/migration-health-scope-reconciliation.md] Reconciled Task 41 from live UI/dashboard wording to a portable static migration-health report grounded in the current telemetry foundation.
