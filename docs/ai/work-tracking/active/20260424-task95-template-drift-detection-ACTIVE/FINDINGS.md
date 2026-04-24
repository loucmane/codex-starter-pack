# Findings

- 2026-04-24 — The archived drift-detection design is still only a draft; the live `scripts/codex-guard` command surface has `validate` only and no drift-check implementation yet.
- 2026-04-24 — Taskmaster already defines the repo-level output target as `reports/template-drift/`, so Task 95 should produce reusable reports there and keep task-local evidence inside the Task 95 active folder.
- 2026-04-24 — The safest first implementation is deterministic template/canonical-document drift detection built on existing guard metadata rules, not free-form AST comparison across the repo.
- 2026-04-24 — The current repo baseline reports zero drift, which makes `--strict` suitable for CI enforcement without introducing immediate false positives.
