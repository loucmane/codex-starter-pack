# Task 16 Create Performance Testing Harness – Implementation Notes

## Planned Workstreams
- Complete scope reconciliation against the portable foundation and prior completed performance-adjacent tasks.
- Add a repo-local performance policy file for duration and regression thresholds.
- Add a static performance harness that measures selected foundation operations, compares optional baselines, and writes Markdown/JSON reports.
- Wire the harness into `codex-task report generate`, repo-structure configuration, and CI artifacts.
- Add focused regression tests and capture final guard/test/performance evidence.

## Scope Gate
- 2026-05-10 — Completed. Task 16 is scoped to durable performance measurement and regression classification, not deep optimization or live monitoring infrastructure.

## Completed Implementation
- Added `templates/metadata/template-performance-policy.json` with repo-local thresholds for cold registry discovery, warm-cache registry resolution, guard validation runtime, scanner no-checkpoint runtime, and baseline regression percentages.
- Added `scripts/template-performance-harness`, a static report generator that loads policy, runs built-in and command probes, compares optional baselines, classifies `pass`/`warn`/`fail`, writes Markdown/JSON outputs, and supports `--strict`.
- Added `reports/template-performance/README.md` as the repo-level report contract.
- Extended `scripts/_repo_structure.py` with `template_performance_policy_path` and `performance_report_dir`.
- Extended `scripts/codex-task report generate` with `--kind performance|all`, `--performance-report-dir`, `--performance-baseline-file`, and `--strict-performance`.
- Included the performance policy/script/report directory in bootstrap and sync-planning surfaces.
- Wired both guard workflows to generate and upload `reports/template-performance/`.
- Added focused tests for the harness, codex-task wiring, repo-structure portability, bootstrap assets, and workflow report generation.

## Evidence
- Scope: `designs/performance-testing-scope-reconciliation.md`
- Direct performance run: `reports/performance-testing-harness/performance-2026-05-10.txt`
- Direct performance report: `reports/performance-testing-harness/template-performance/latest.md`
- Codex-task performance wrapper: `reports/performance-testing-harness/codex-task-performance-2026-05-10.txt`
- Focused tests: `reports/performance-testing-harness/tests-2026-05-10-focused.txt`
