# Task 17 Setup Monitoring Infrastructure – Implementation Notes

## Planned Workstreams
- Scope reconciliation: complete. Task 17 is bounded to portable static monitoring over existing metrics artifacts.
- Monitoring policy: add `templates/metadata/template-monitoring-policy.json` with policy-defined metric checks.
- Monitoring evaluator: add `scripts/template-monitoring` to read `reports/template-metrics/latest.json`, evaluate checks, and write `reports/template-monitoring/latest.md` / `latest.json`.
- Automation: wire monitoring generation into guard workflows and `codex-task report generate`.
- Tests: add focused tests for policy loading, threshold evaluation, strict mode, output rendering, CI wiring, and portable roots.

## Completed Implementation
- Added `templates/metadata/template-monitoring-policy.json` with six default checks:
  - template metadata coverage is complete;
  - template metadata drift count is zero;
  - latest template drift findings are zero;
  - active work-tracking folder count is at most one;
  - Taskmaster in-progress count is at most one;
  - plan-sync has recorded activity.
- Added `scripts/template-monitoring` as a static evaluator that:
  - loads policy from the configured templates root;
  - reads an existing metrics dashboard JSON payload;
  - evaluates dotted metric sources against policy thresholds;
  - writes Markdown and JSON monitoring reports;
  - returns nonzero in `--strict` mode only for error-level failures.
- Added `reports/template-monitoring/README.md` documenting the static monitoring contract and local invocation.
- Updated `_repo_structure.py` with `monitoring_report_dir` and `template_monitoring_policy_path`.
- Updated `scripts/codex-task report generate` with `--kind monitoring` and `--strict-monitoring`; `--kind all` now runs drift, metrics, then monitoring.
- Updated bootstrap/sync surfaces so new projects inherit `reports/template-monitoring/`, `template-monitoring-policy.json`, and `scripts/template-monitoring`.
- Updated guard workflows to run `python3 scripts/template-monitoring --strict` after metrics generation and upload `reports/template-monitoring/` artifacts.
- Added `tests/meta_workflow_guard/test_template_monitoring.py` and updated repo-structure, codex-task, and workflow tests.

## Evidence
- Task-local metrics sample: `reports/monitoring-infrastructure/sample-template-metrics/latest.json`.
- Task-local monitoring sample: `reports/monitoring-infrastructure/sample-template-monitoring/latest.json` (`status: pass`, `6/6` checks passed).
- Focused regression: `reports/monitoring-infrastructure/tests-2026-05-09-focused.txt` (`66 passed`).
- Full pytest: `reports/monitoring-infrastructure/tests-2026-05-09-full.txt` (`377 passed`).
- Plan sync: `reports/monitoring-infrastructure/plan-sync-2026-05-09-final.txt`.
- Work-tracking audit: `reports/monitoring-infrastructure/work-tracking-audit-2026-05-09-final.txt`.
- Guard: `reports/monitoring-infrastructure/guard-2026-05-09-final.txt`.
- Diff check: `reports/monitoring-infrastructure/diff-check-2026-05-09-final.txt`.
- Taskmaster health: `reports/monitoring-infrastructure/taskmaster-health-2026-05-09-final.txt`.
