# Task 20 CI/CD Scope Reconciliation

## Context

Task 20 asks for a CI/CD pipeline with scanner validation, guard enforcement, performance tests, security scans, Python matrix testing, artifact storage, branch protection, deployment gates, and cost monitoring. That wording predates several completed systems:

- Task 9 added tracked local hook parity verification for the guard and drift hooks.
- Task 15 made Serena status and evidence enforcement explicit.
- Task 84 added timestamp guard enforcement.
- Task 97 added template metrics generation and wired guard workflows to upload metrics artifacts.

The repo now already has:

- `.github/workflows/codex-guard.yml` for guard, drift, metrics, and artifacts.
- `.github/workflows/meta-workflow-guard.yml` for path-scoped workflow guard checks on PRs and pushes to `main`.
- `.pre-commit-config.yaml` for local guard and drift parity.
- `python3 scripts/codex-task taskmaster health` for full-graph Taskmaster dependency health.
- A full pytest suite configured through `pyproject.toml`.

## Current-State Gap

GitHub Actions currently validates guard/drift/metrics, but it does not run the full Python test suite. A PR can therefore pass guard workflows while breaking:

- Claude adapter runtime gate tests;
- codex-task helper tests;
- template registry and metrics tests;
- session continuation tests;
- timestamp guard tests;
- template SSOT scanner tests.

Local proof: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest` collected 320 tests and passed locally on Python 3.12.

## Decision

Add a dedicated `.github/workflows/ci.yml` workflow for the Python test suite rather than duplicating the existing guard workflows.

The workflow should:

1. Run on pull requests and pushes to `main`.
2. Use a Python matrix for `3.11` and `3.12`, matching `pyproject.toml` support.
3. Install both runtime dependencies and the `dependency-groups.dev` entries from `pyproject.toml`.
4. Run `python3 scripts/codex-task taskmaster health`.
5. Run the full configured pytest suite with `PYTHONDONTWRITEBYTECODE=1`.
6. Store per-version pytest output under `reports/ci/` and upload it as a GitHub Actions artifact.
7. Keep guard, drift, and metrics automation in the existing workflows.

## Out of Scope

- Branch protection settings: GitHub repository configuration, not a repo file change.
- Deployment gates: no deployable product exists in this starter-pack repository yet.
- Cost monitoring: GitHub billing configuration is external; the workflow keeps the matrix small and focused.
- Secret scanning and broader security scans: Task 9 explicitly deferred these pending separate baseline evidence.

## Verification Plan

- Add a regression test that parses `.github/workflows/ci.yml` and asserts the matrix, dependency install, taskmaster health, full pytest command, and artifact upload contract.
- Run `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_ci_workflows.py`.
- Run the full local pytest suite.
- Capture plan sync, audit, guard, and diff-check evidence before closing Task 20.
