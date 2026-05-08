# Decisions

- 2026-05-08 — Implement Task 20 as a dedicated Python test-suite CI workflow instead of a broad greenfield migration pipeline.
- 2026-05-08 — Keep `.github/workflows/codex-guard.yml` and `.github/workflows/meta-workflow-guard.yml` intact as the guard/drift/metrics enforcement path.
- 2026-05-08 — Use Python `3.11` and `3.12` in the matrix because `pyproject.toml` declares `requires-python = ">=3.11"` and the local runtime is Python 3.12.
- 2026-05-08 — Treat branch protection, deployment gates, cost monitoring, and extra security scanners as out of scope unless a future task has repository-admin access or baseline evidence for those controls.
- 2026-05-08 — Keep Task 20 evidence in the active work-tracking folder until the PR is merged; archive happens only after merge and branch cleanup.
