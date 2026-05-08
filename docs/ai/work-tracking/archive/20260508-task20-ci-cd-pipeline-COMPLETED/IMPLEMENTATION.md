# Task 20 Setup CI/CD Pipeline – Implementation Notes

## Planned Workstreams
- Scope reconciliation: completed in `designs/ci-cd-scope-reconciliation.md`.
- CI workflow: add `.github/workflows/ci.yml` for full Python pytest coverage.
- Workflow contract tests: add `tests/meta_workflow_guard/test_ci_workflows.py`.
- Evidence: capture targeted workflow tests, full pytest, Taskmaster health, plan sync, audit, guard, and diff-check output.

## Implemented CI Contract
- Runs on pull requests and pushes to `main`.
- Uses a Python matrix for `3.11` and `3.12`.
- Installs runtime dependencies plus `dependency-groups.dev` dependencies from `pyproject.toml`.
- Runs `python3 scripts/codex-task taskmaster health`.
- Runs the full configured pytest suite via `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`.
- Writes per-version pytest logs under `reports/ci/` and uploads them as artifacts.

## Regression Coverage
- `tests/meta_workflow_guard/test_ci_workflows.py` asserts the workflow Python matrix is `3.11` and `3.12`, with `fail-fast: false`.
- The tests assert Taskmaster health and full pytest commands are present.
- The tests assert the workflow installs runtime and dev dependencies from `pyproject.toml`.
- The tests assert CI report artifacts are written under `reports/ci/` and uploaded.

## Evidence
- Targeted workflow tests: `reports/ci-cd-pipeline/tests-2026-05-08-ci-workflows.txt` (`4 passed`).
- Full local pytest: `reports/ci-cd-pipeline/tests-2026-05-08-full-pytest.txt` (`324 passed`).
- Taskmaster health: `reports/ci-cd-pipeline/taskmaster-health-2026-05-08.txt` (OK).
- Plan sync: `reports/ci-cd-pipeline/plan-sync-2026-05-08.txt` (recorded).
- Work-tracking audit: `reports/ci-cd-pipeline/work-tracking-audit-2026-05-08.txt` (passed).
- Guard: `reports/ci-cd-pipeline/guard-2026-05-08.txt` (passed).
- Diff check: `reports/ci-cd-pipeline/diff-check-2026-05-08.txt` (clean).
- Serena memory: `.serena/memories/2026-05-08_task20_ci_cd_pipeline.md`.
