# Phase 0 Scanner Validation Report

Generated: 2026-05-12T13:26:50.013927+02:00
Scanner data directory: scripts/template-ssot-scanner/output/data
Monitoring file: docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-132639-final-validation-suite-evidence/template-monitoring/latest.json
Status: warn

## Summary
- Total checks: 7
- Passed: 5
- Warnings: 2
- Errors: 0

## Checks
- scanner-output-completeness: pass
  - Severity: `error`
  - Evidence: `scripts/template-ssot-scanner/output/data`
  - Message: All required scanner outputs are present.
- scanner-output-format: pass
  - Severity: `error`
  - Evidence: `scripts/template-ssot-scanner/output/data`
  - Message: All scanner outputs use output format 2.0.0.
- baseline-metrics-completeness: pass
  - Severity: `error`
  - Evidence: `scripts/template-ssot-scanner/output/data/baseline_summary.json`
  - Message: Baseline summary includes required Phase 0 performance metrics.
- security-error-findings: pass
  - Severity: `error`
  - Evidence: `scripts/template-ssot-scanner/output/data/security_validation.json`
  - Message: No error-level security findings are present.
- security-warning-findings: pass
  - Severity: `warning`
  - Evidence: `scripts/template-ssot-scanner/output/data/security_validation.json`
  - Message: No warning-level security findings are present.
- baseline-known-findings: warn
  - Severity: `warning`
  - Evidence: `scripts/template-ssot-scanner/output/data/baseline_summary.json`
  - Message: Baseline summary contains non-blocking findings that remain visible in the Phase 0 report.
- monitoring-status: warn
  - Severity: `warning`
  - Evidence: `docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-132639-final-validation-suite-evidence/template-monitoring/latest.json`
  - Message: Monitoring report has warning-level findings.
