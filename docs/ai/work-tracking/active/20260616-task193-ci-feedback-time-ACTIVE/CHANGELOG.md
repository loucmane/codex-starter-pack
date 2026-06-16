# Task 193 Reduce CI feedback time without reducing coverage – Changelog

- 2026-06-16 13:14 CEST — Initialized active work-tracking folder.
- 2026-06-16 — Parallelized CI pytest with pytest-xdist (`-n auto --dist loadgroup` in ci.yml;
  xdist added to dev deps). Made the suite parallel-safe: repo-root `conftest.py` isolates git
  config per worker; `test_guard_rules.py` pinned to one xdist group. Measured 323s→~60s
  (32 cores) / 323s→103s (4 workers, 3.1×); 6/6 `-n auto` runs green. Coverage unchanged
  (identical test set).
