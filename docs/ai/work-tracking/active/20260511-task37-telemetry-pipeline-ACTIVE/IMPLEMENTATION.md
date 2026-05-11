# Task 37 Build Telemetry Pipeline – Implementation Notes

## Planned Workstreams
- Scope reconciliation against the current portable foundation and existing report generators.
- First-class telemetry report kind in `scripts/codex-task`.
- Central report/telemetry documentation.
- Focused regression coverage and dry-run evidence for report ordering.

## Scope Gate
- 2026-05-11 — Complete. Task 37 is scoped to the existing portable static telemetry chain, not live observability services.

## Implemented Surface
- Added `telemetry` to `python3 scripts/codex-task report generate --kind ...`.
- `--kind telemetry` runs the same ordered report pipeline as `--kind all`: drift, metrics, monitoring, Phase 0 validation, performance, cost.
- Preserved `--kind all` for backward compatibility.
- Added `reports/README.md` as the central static telemetry/reporting index.
- Updated `templates/TOOLS.md` with the telemetry pipeline command and stage contracts.
- Added focused `codex-task` regression coverage for the parser and report pipeline dispatch order.

## Evidence
- Focused tests: `reports/telemetry-pipeline/tests-2026-05-11-codex-task.txt` (`54 passed`).
- Telemetry dry-run: `reports/telemetry-pipeline/telemetry-dry-run-2026-05-11.txt`.
- Task-local telemetry execution: `reports/telemetry-pipeline/telemetry-run-2026-05-11.txt`.
- Final task-local telemetry execution after plan sync: `reports/telemetry-pipeline/telemetry-run-final-2026-05-11.txt`.
- Task-local pipeline outputs:
  - `reports/telemetry-pipeline/template-drift/`
  - `reports/telemetry-pipeline/template-metrics/`
  - `reports/telemetry-pipeline/template-monitoring/`
  - `reports/telemetry-pipeline/phase0-scanner-validation/`
  - `reports/telemetry-pipeline/template-performance/`
  - `reports/telemetry-pipeline/cost-tracking/`
- Final task-local pipeline outputs:
  - `reports/telemetry-pipeline/final-template-drift/`
  - `reports/telemetry-pipeline/final-template-metrics/`
  - `reports/telemetry-pipeline/final-template-monitoring/`
  - `reports/telemetry-pipeline/final-phase0-scanner-validation/`
  - `reports/telemetry-pipeline/final-template-performance/`
  - `reports/telemetry-pipeline/final-cost-tracking/`
- Final plan sync: `reports/telemetry-pipeline/plan-sync-2026-05-11-final.txt`.
- Final work-tracking audit: `reports/telemetry-pipeline/work-tracking-audit-2026-05-11-final.txt`.
- Final guard: `reports/telemetry-pipeline/guard-2026-05-11-final.txt`.
- Final Taskmaster health: `reports/telemetry-pipeline/taskmaster-health-2026-05-11-final.txt`.
- Final diff check: `reports/telemetry-pipeline/diff-check-2026-05-11-final.txt`.
