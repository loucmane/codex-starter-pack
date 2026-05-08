# Task 20 CI/CD Pipeline

## Status
Task 20 implements the proven current CI gap after scope reconciliation: a dedicated full Python pytest GitHub Actions workflow. Existing guard, drift, meta-workflow, hook parity, and metrics workflows remain unchanged.

## Implementation
- Added `.github/workflows/ci.yml`.
- Workflow runs on pull requests and pushes to `main`.
- Workflow uses Python matrix `3.11` and `3.12` with `fail-fast: false`.
- Workflow installs runtime dependencies and `dependency-groups.dev` dependencies from `pyproject.toml`.
- Workflow runs `python3 scripts/codex-task taskmaster health` and full configured pytest with `PYTHONDONTWRITEBYTECODE=1`.
- Workflow writes pytest output under `reports/ci/` and uploads it through `actions/upload-artifact@v4`.
- Added `tests/meta_workflow_guard/test_ci_workflows.py` to assert the workflow contract.

## Evidence
- Scope reconciliation: `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/designs/ci-cd-scope-reconciliation.md`.
- Targeted workflow tests: `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/reports/ci-cd-pipeline/tests-2026-05-08-ci-workflows.txt`.
- Full local pytest: `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/reports/ci-cd-pipeline/tests-2026-05-08-full-pytest.txt`.
- Taskmaster health: `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/reports/ci-cd-pipeline/taskmaster-health-2026-05-08.txt`.

## Active Context
- Branch: `feat/task-20-ci-cd-pipeline`.
- Session: `sessions/2026/05/2026-05-08-007-task20-ci-cd-pipeline.md`.
- Plan: `plans/2026-05-08-task20-ci-cd-pipeline.md`.
- Work tracking: `docs/ai/work-tracking/active/20260508-task20-ci-cd-pipeline-ACTIVE/`.

## Next
- Finish final verification stack: plan sync, work-tracking audit, guard, diff-check.
- Mark Taskmaster subtask `20.2` and parent Task `20` done after evidence is recorded.
- Push branch, create PR, verify GitHub Actions includes the new CI workflow before merge.