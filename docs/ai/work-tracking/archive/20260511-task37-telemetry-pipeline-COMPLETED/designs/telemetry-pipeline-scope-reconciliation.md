# Task 37 Telemetry Pipeline Scope Reconciliation

**Captured**: 2026-05-11 17:20 CEST  
**Task**: 37 - Build Telemetry Pipeline

## Historical Task Wording

Task 37 asks for a comprehensive telemetry collection and analysis system:

- OpenTelemetry SDK integration
- trace context propagation
- custom template-usage metrics
- Elasticsearch log aggregation
- Grafana dashboards
- anomaly detection
- 90-day retention policies
- GDPR compliance

That wording comes from an earlier migration-service framing. The current repository is a portable foundation/starter pack with local scripts, GitHub Actions, static report artifacts, Taskmaster state, and work-tracking evidence. It does not run a long-lived application service that would justify a live observability stack.

## Current Repository Evidence

- Task 97 implemented `scripts/template-metrics-dashboard`, which writes repo-level metrics to `reports/template-metrics/latest.md` and `latest.json`.
- Task 17 implemented static monitoring with `scripts/template-monitoring`, policy thresholds, and `reports/template-monitoring/`.
- Task 16 implemented static performance telemetry with `scripts/template-performance-harness` and `reports/template-performance/`.
- Task 24 implemented cost governance telemetry with `scripts/template-cost-report` and `reports/cost-tracking/`.
- Task 25 implemented Phase 0 scanner validation over scanner and monitoring artifacts with `scripts/template-phase0-validation`.
- `scripts/codex-task report generate --kind all` already runs the static report chain in this order: drift, metrics, monitoring, Phase 0 validation, performance, cost.

## Scope Decision

Task 37 should not introduce Prometheus, Grafana, Elasticsearch, OpenTelemetry SDK wiring, background daemons, databases, or external services into this portable foundation.

The current gap is naming and contract clarity:

- the telemetry pipeline exists operationally as `--kind all`, but there is no first-class `telemetry` report kind;
- the repo has stage-specific README files, but no central report/telemetry index explaining the full pipeline;
- `templates/TOOLS.md` documents the metrics dashboard, but not the full static telemetry chain now used by the foundation.

Task 37 will make the existing static report chain explicit and discoverable:

- add `python3 scripts/codex-task report generate --kind telemetry` as a semantic alias for the full static telemetry pipeline;
- keep `--kind all` backward-compatible;
- document the pipeline in `reports/README.md`;
- update `templates/TOOLS.md` with the telemetry/reporting stages and command contract;
- add focused regression coverage proving `telemetry` runs the same ordered stage chain as `all`.

## Out of Scope

- Live OpenTelemetry instrumentation for a non-service repository.
- Grafana, Elasticsearch, StatsD, Prometheus, databases, or hosted dashboards.
- Runtime trace propagation for no runtime request path.
- Retention/GDPR machinery beyond honest file-based report contracts and existing cost/report policy behavior.
- Replacing the existing metrics, monitoring, Phase 0, performance, or cost scripts.

## Proven Gap For 37.2

The repo has the stage scripts and an `all` runner, but the user-facing/task-facing terminology still does not say "telemetry pipeline." A future project adopting the foundation needs one obvious command and one central report map for static telemetry:

```bash
python3 scripts/codex-task report generate --kind telemetry \
  --strict-drift \
  --strict-monitoring \
  --strict-phase0 \
  --strict-performance \
  --strict-cost
```

That command should produce the same stage outputs as `--kind all` while making the intent clear.

## Verification Plan

- Run focused `codex-task` tests for parser/report-generation behavior.
- Run the telemetry pipeline in dry-run mode to confirm command order without mutating repo-level report outputs.
- Run plan sync, work-tracking audit, guard validation, Taskmaster health, and diff check before closeout.
