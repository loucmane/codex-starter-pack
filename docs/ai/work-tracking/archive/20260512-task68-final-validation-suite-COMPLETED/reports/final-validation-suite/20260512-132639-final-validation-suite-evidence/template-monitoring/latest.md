# Template Monitoring Report

Generated: 2026-05-12T13:26:49.948930+02:00
Policy version: 1.0.0
Metrics file: docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-132639-final-validation-suite-evidence/template-metrics/latest.json
Status: warn

## Summary
- Total checks: 6
- Passed: 5
- Warnings: 1
- Errors: 0

## Checks
- template_metadata_coverage: pass
  - Source: `template_metadata.coverage_pct`
  - Actual: `100.0`
  - Expected: `>= 100`
  - Severity: `error`
  - Message: Template metadata coverage must remain complete.
- template_metadata_drift: pass
  - Source: `template_metadata.drifted_file_count`
  - Actual: `0`
  - Expected: `<= 0`
  - Severity: `error`
  - Message: Template metadata drift findings require correction.
- template_drift_findings: pass
  - Source: `drift.finding_count`
  - Actual: `0`
  - Expected: `<= 0`
  - Severity: `error`
  - Message: Template drift reports should stay clean.
- active_work_tracking_folders: pass
  - Source: `work_tracking.active_folder_count`
  - Actual: `1`
  - Expected: `<= 1`
  - Severity: `warning`
  - Message: More than one active work-tracking folder should be reviewed.
- taskmaster_in_progress_count: missing
  - Source: `taskmaster.status_counts.in-progress`
  - Actual: `None`
  - Expected: `<= 1`
  - Severity: `warning`
  - Message: Metric source 'taskmaster.status_counts.in-progress' is missing
- plan_sync_activity: pass
  - Source: `plan_sync.entry_count`
  - Actual: `615`
  - Expected: `> 0`
  - Severity: `warning`
  - Message: Plan sync should have at least one recorded entry.
