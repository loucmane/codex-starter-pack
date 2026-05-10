# Task 24 - Cost Tracking System

Date: 2026-05-10
Branch: `feat/task-24-cost-tracking-system`

## Scope Decision
Task 24 was reconciled from legacy live billing/API control wording into a portable static cost governance report. The repo has no Anthropic/GitHub billing telemetry source and no runtime boundary for automatic throttling, so the implementation must not claim live cost tracking without supplied usage data.

## Implemented
- Added `templates/metadata/template-cost-policy.json` with cost categories, warning/critical thresholds, review commands, and explicit non-goals.
- Added executable `scripts/template-cost-report` to load policy, optional usage JSON, classify categories as `pass`, `warn`, `fail`, or `not-measured`, and write `latest.md`/`latest.json`.
- Wired `scripts/codex-task report generate --kind cost|all` with `--cost-report-dir`, `--cost-usage-file`, and `--strict-cost`.
- Extended `_repo_structure` with `template_cost_policy_path` and `cost_report_dir`.
- Added bootstrap/sync portability for cost policy/report directory and included cost reports in guard workflows/artifacts.
- Added tests in `tests/meta_workflow_guard/test_template_cost_report.py` plus codex-task/repo-structure test updates.

## Evidence
- Live report: `docs/ai/work-tracking/active/20260510-task24-cost-tracking-system-ACTIVE/reports/cost-tracking-system/latest.md` and `latest.json`.
- Full pytest evidence: `docs/ai/work-tracking/active/20260510-task24-cost-tracking-system-ACTIVE/reports/cost-tracking-system/tests-2026-05-10-full.txt` (`402 passed`).

## Important Non-Goals
No provider billing API calls, GitHub billing queries, external alerts, automatic cache/rate-limit/throttle mutation, or cost claims for categories without supplied usage input.