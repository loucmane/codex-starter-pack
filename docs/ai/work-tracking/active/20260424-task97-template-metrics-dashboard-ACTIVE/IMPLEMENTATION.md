# Task 97 Template Metrics Dashboard – Implementation Notes

## Planned Workstreams
- Define the dashboard schema and source inventory from Taskmaster, drift reports, plan sync, work-tracking folders, and session history.
- Harden the Task 96 wizard baseline so Task 97 starts from valid session/tracker artifacts.
- Implement the `scripts/template-metrics-dashboard` generator plus repo-level report directory documentation.
- Add focused regression tests for the generator output and keep CI automation aligned with the report contract.

## Completed Work
- Added a standalone `scripts/template-metrics-dashboard` CLI with `--report-dir`, markdown/json output generation, and `codex-guard` metadata reuse.
- Added `reports/template-metrics/README.md` to document the repo-level dashboard contract.
- Added `tests/meta_workflow_guard/test_template_metrics_dashboard.py` and kept the existing Task 96/guard suites green.
- Wired both guard workflows to run the dashboard generator and upload `reports/template-metrics/` artifacts.
