# Template Monitoring Report

Generated: 2026-05-09T11:26:00.325382+02:00
Policy version: 1.0.0
Metrics file: docs/ai/work-tracking/active/20260509-task17-monitoring-infrastructure-ACTIVE/reports/monitoring-infrastructure/sample-template-metrics/latest.json
Status: pass

## Summary
- Total checks: 6
- Passed: 6
- Warnings: 0
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
- taskmaster_in_progress_count: pass
  - Source: `taskmaster.status_counts.in-progress`
  - Actual: `1`
  - Expected: `<= 1`
  - Severity: `warning`
  - Message: More than one in-progress Taskmaster task should be reviewed.
- plan_sync_activity: pass
  - Source: `plan_sync.entry_count`
  - Actual: `528`
  - Expected: `> 0`
  - Severity: `warning`
  - Message: Plan sync should have at least one recorded entry.
