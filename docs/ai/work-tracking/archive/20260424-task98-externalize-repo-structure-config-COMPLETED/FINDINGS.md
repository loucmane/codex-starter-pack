# Findings

- 2026-04-24 — `scripts/codex-guard`, `scripts/codex-task`, and `scripts/template-metrics-dashboard` all derive critical behavior from hardcoded repo roots such as `sessions/`, `plans/`, `.taskmaster/`, `docs/ai/work-tracking/`, and `reports/`.
- 2026-04-24 — The repo already has a versioned `.codex/config.toml`, so extending that file is a cleaner portability path than inventing a second repo-local config file.
- 2026-04-24 — Testability improves when path derivation is loaded through a single helper; otherwise import-time constants break as soon as the repo root is swapped under tests or fixtures.
- 2026-04-24 — Guard verification also exposed a stale Task 96 plan file whose steps were still `pending` after the task had already been completed and merged; same-day plan conflicts only stay trustworthy if completed plans are normalized.
