# Task 193 Reduce CI feedback time without reducing coverage – Handoff Summary

## Current State
- CI pytest now runs `python3 -m pytest -n auto --dist loadgroup` (parallel across runner
  cores) — same tests, same coverage. `pytest-xdist` added to dev deps.
- Suite made parallel-safe: a repo-root `conftest.py` isolates git config per worker (fixes a
  latent cross-test gpgsign leak); `test_guard_rules.py` pinned to one xdist group (its tests
  mutate fixed real-repo paths).
- Measured: 323s serial → ~60s under `-n auto` (32 cores), 6/6 parallel runs green with the
  developer's real gpgsign=true. On a 4-vCPU runner expect ~3–4× on the pytest portion.

## Next Steps
- Push branch `feat/task-193-ci-feedback-time`, open PR, merge on owner approval. The PR's own
  CI run is the real-world proof of the feedback-time reduction (compare its Python-tests
  duration to recent PRs' ~10–12min).
- After merge + branch cleanup: archive this folder (rides the next kickoff).

## Deferred (DECISIONS)
- Hoisting the version-independent shadow-capture steps out of the matrix + caching the npm
  Taskmaster install — smaller, higher-churn CI wins; possible follow-up if more reduction is
  wanted.
- Archived on 2026-06-16 14:32 CEST — Folder moved to archive and tracker marked COMPLETED.
