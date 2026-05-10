# Task 24 Implement Cost Tracking System – Implementation Notes

## Planned Workstreams
- [x] Add `templates/metadata/template-cost-policy.json` with portable cost categories, warning/critical thresholds, non-goals, and review commands.
- [x] Add `scripts/template-cost-report` to load policy, optional usage input, classify budget status, and write JSON/Markdown reports.
- [x] Wire cost reports into `scripts/codex-task report generate --kind cost|all`, repo-structure paths, bootstrap assets, sync assets, and focused regression tests.
- [x] Generate Task 24 evidence under the active work-tracking reports folder before closing.

## Implemented Surface

- `scripts/template-cost-report` writes `latest.md` and `latest.json` reports from repo-local policy and optional usage JSON.
- Missing usage data is classified as `not-measured` so the report does not claim Anthropic, GitHub billing, or local runtime telemetry it does not have.
- `--strict` exits nonzero only for `fail` budget outcomes, not for honest `not-measured` warnings.
- `python3 scripts/codex-task report generate --kind cost|all` runs the cost report after performance reporting.
- Bootstrap and cross-repo sync include the cost policy/report directory so the surface remains portable.
- Guard workflows generate and upload `reports/cost-tracking/` artifacts.

## Evidence

- Focused tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_template_cost_report.py tests/meta_workflow_guard/test_codex_task.py tests/meta_workflow_guard/test_repo_structure_config.py` -> 61 passed.
- Live cost report: `docs/ai/work-tracking/active/20260510-task24-cost-tracking-system-ACTIVE/reports/cost-tracking-system/latest.md`.
- codex-task wiring smoke: `python3 scripts/codex-task report generate --kind cost --cost-report-dir docs/ai/work-tracking/active/20260510-task24-cost-tracking-system-ACTIVE/reports/cost-tracking-system/codex-task --strict-cost`.
