# Migration Health Dashboard

Generated: 2026-05-12T18:03:18.321445+02:00
Status: warn
Executes external actions: False

## Summary
- Total components: 5
- Passed: 2
- Warnings: 3
- Errors: 0
- Missing: 3

## Components
### Template metrics dashboard

- ID: `metrics`
- Status: `pass`
- Severity: `info`
- Source status: `n/a`
- Generated at: `2026-04-24T15:48:29.554660+02:00`
- Evidence: `reports/template-metrics/latest.json`
- Message: Telemetry component loaded successfully.
- Review command: `python3 scripts/template-metrics-dashboard`

### Template monitoring report

- ID: `monitoring`
- Status: `missing`
- Severity: `warning`
- Source status: `n/a`
- Generated at: `n/a`
- Evidence: `reports/template-monitoring/latest.json`
- Message: Telemetry component is missing; run the review command before claiming full migration health.
- Review command: `python3 scripts/template-monitoring --strict`

### Phase 0 scanner validation report

- ID: `phase0`
- Status: `missing`
- Severity: `warning`
- Source status: `n/a`
- Generated at: `n/a`
- Evidence: `reports/phase0-scanner-validation/latest.json`
- Message: Telemetry component is missing; run the review command before claiming full migration health.
- Review command: `python3 scripts/template-phase0-validation --strict`

### Template performance report

- ID: `performance`
- Status: `pass`
- Severity: `info`
- Source status: `pass`
- Generated at: `2026-05-10T12:24:10.229844+02:00`
- Evidence: `reports/template-performance/latest.json`
- Message: Telemetry component reports pass.
- Review command: `python3 scripts/template-performance-harness --strict`

### Cost tracking report

- ID: `cost`
- Status: `missing`
- Severity: `warning`
- Source status: `n/a`
- Generated at: `n/a`
- Evidence: `reports/cost-tracking/latest.json`
- Message: Telemetry component is missing; run the review command before claiming full migration health.
- Review command: `python3 scripts/template-cost-report --strict`

No live dashboard, WebSocket, external alert, billing query, database write, or background service action was executed by this report.
