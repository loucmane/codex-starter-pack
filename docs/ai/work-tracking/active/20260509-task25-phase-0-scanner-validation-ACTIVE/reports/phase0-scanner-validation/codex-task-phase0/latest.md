# Phase 0 Scanner Validation Report

Generated: 2026-05-09T12:17:10.802821+02:00
Scanner data directory: scripts/template-ssot-scanner/output/data
Monitoring file: docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/sample-template-monitoring/latest.json
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
- security-warning-findings: warn
  - Severity: `warning`
  - Evidence: `scripts/template-ssot-scanner/output/data/security_validation.json`
  - Message: Security validation reports 1 warning-level finding(s).
- baseline-known-findings: warn
  - Severity: `warning`
  - Evidence: `scripts/template-ssot-scanner/output/data/baseline_summary.json`
  - Message: Baseline summary contains non-blocking findings that remain visible in the Phase 0 report.
- monitoring-status: pass
  - Severity: `error`
  - Evidence: `docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/sample-template-monitoring/latest.json`
  - Message: Monitoring report passes.
