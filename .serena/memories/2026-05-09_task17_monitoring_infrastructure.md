# Task 17 - Monitoring Infrastructure (2026-05-09)

## Status
- Branch: `feat/task-17-monitoring-infrastructure`
- Taskmaster: parent Task 17 done; subtasks 17.1 and 17.2 done.
- Session: `sessions/2026/05/2026-05-09-001-task17-monitoring-infrastructure.md`
- Plan: `plans/2026-05-09-task17-monitoring-infrastructure.md`
- Active work tracking: `docs/ai/work-tracking/active/20260509-task17-monitoring-infrastructure-ACTIVE/`

## Scope Decision
Task 17 was reconciled against current Task 97 metrics dashboard and portable foundation work. The correct current scope is static, file-based monitoring over existing metrics artifacts, not live Prometheus/Grafana/StatsD/Elasticsearch infrastructure.

## Implementation
- Added `templates/metadata/template-monitoring-policy.json` with policy-defined checks for metadata coverage, drift findings, active work-tracking count, Taskmaster in-progress count, and plan-sync activity.
- Added `scripts/template-monitoring`, which reads `reports/template-metrics/latest.json`, evaluates policy thresholds, writes `reports/template-monitoring/latest.md` and `latest.json`, and supports `--strict` for error-level failures only.
- Added `reports/template-monitoring/README.md`.
- Updated `scripts/_repo_structure.py` with `monitoring_report_dir` and `template_monitoring_policy_path`.
- Updated `scripts/codex-task report generate` with `--kind monitoring`, `--strict-monitoring`, and `all` ordering of drift -> metrics -> monitoring.
- Updated bootstrap/sync surfaces so new projects inherit the monitoring report directory, monitoring policy, and monitoring script.
- Updated guard workflows to run `python3 scripts/template-monitoring --strict` after metrics generation and upload `reports/template-monitoring/` artifacts.
- Added `tests/meta_workflow_guard/test_template_monitoring.py` and updated codex-task/repo-structure tests.

## Evidence
- Task-local sample monitoring report: `docs/ai/work-tracking/active/20260509-task17-monitoring-infrastructure-ACTIVE/reports/monitoring-infrastructure/sample-template-monitoring/latest.json` with `status: pass` and six checks passed.
- Focused regression: `docs/ai/work-tracking/active/20260509-task17-monitoring-infrastructure-ACTIVE/reports/monitoring-infrastructure/tests-2026-05-09-focused.txt` (`66 passed`).
- Full pytest: `docs/ai/work-tracking/active/20260509-task17-monitoring-infrastructure-ACTIVE/reports/monitoring-infrastructure/tests-2026-05-09-full.txt` (`377 passed`).
- Final verification rerun after status correction: plan sync, work-tracking audit, guard, diff-check, and Taskmaster health all passed with evidence under `reports/monitoring-infrastructure/`.

## Next Steps
1. Commit and push Task 17 on `feat/task-17-monitoring-infrastructure`.
2. Open PR, wait for green checks, merge.
3. On `main`, archive `20260509-task17-monitoring-infrastructure-ACTIVE`, clear current session/plan pointers, record post-archive audit/guard/diff-check/health evidence, commit and push archive closeout.