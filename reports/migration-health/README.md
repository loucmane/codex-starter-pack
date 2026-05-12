# Migration Health Reports

This directory stores the aggregate static migration-health dashboard/report for the portable foundation.

Generate it directly with:

```bash
python3 scripts/template-migration-health-dashboard
```

Or generate it as part of the full telemetry pipeline:

```bash
python3 scripts/codex-task report generate --kind telemetry \
  --strict-drift \
  --strict-monitoring \
  --strict-phase0 \
  --strict-performance \
  --strict-cost \
  --strict-migration-health
```

The report reads the latest static telemetry artifacts from:

- `reports/template-metrics/latest.json`
- `reports/template-monitoring/latest.json`
- `reports/phase0-scanner-validation/latest.json`
- `reports/template-performance/latest.json`
- `reports/cost-tracking/latest.json`

Missing telemetry inputs are surfaced as warning-level `missing` components. Malformed telemetry or fail-level source reports fail aggregate migration health. The generator does not run live dashboards, WebSockets, external alert delivery, billing queries, database writes, or background services.
