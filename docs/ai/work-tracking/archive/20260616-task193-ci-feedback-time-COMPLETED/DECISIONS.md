# Decisions

- 2026-06-16 — Use **pytest-xdist `-n auto`** as the primary lever (vs sharding/matrix changes).
  It runs the identical test set across cores, so coverage is provably unchanged; the pytest run
  is the dominant cost in the only pytest job (ci.yml). Sharding across the 3.11/3.12 matrix was
  rejected — that would reduce per-version coverage.
- 2026-06-16 — Put `-n auto` in the **ci.yml command, not pyproject `addopts`** — contained to
  CI; doesn't change local default behavior, focused-test runs, or require xdist for every
  invocation.
- 2026-06-16 — `--dist loadgroup` (not `loadfile` or bare `load`). Bare `load` is fastest but
  exposes the guard-rules real-repo race; `loadfile` is robust but makes the biggest file the
  wall-clock floor. `loadgroup` pins ONLY the one unsafe file (`test_guard_rules.py`, via an
  xdist_group `pytestmark`) and keeps everything else granular. Justified: a 5× full-suite run
  under the most aggressive `load` distribution showed guard-rules is the SOLE offender.
- 2026-06-16 — Parallel-safety fix #1: a **`conftest.py`** isolating
  `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` per worker (gpgsign off, identity, defaultBranch=main).
  Root cause: a git test ran `git commit` without `-c commit.gpgsign=false` and only passed
  because another test leaked a global gpgsign=false — order-dependent and unsafe per-worker.
  The conftest gives every test/worker a clean git env matching CI. Validated: 6× `-n auto` runs
  passed with the developer's real `commit.gpgsign=true` still set.
- 2026-06-16 — Parallel-safety fix #2: pin `test_guard_rules.py` to one xdist group instead of
  making its fixture worker-unique. A worker-unique-rename attempt was **rejected** — the
  folder-names tests pass hardcoded `entries` referencing the fixed path, so renaming the
  on-disk folder desyncs them (broke `..._allows_untracked_multi_day_started_folder`). Pinning
  the module (serial among its own tests, like a non-parallel run) is correct and minimal.
- 2026-06-16 — Deliberately did NOT also restructure ci.yml (hoist the version-independent
  shadow-capture steps out of the matrix, cache the npm Taskmaster install). Those are smaller,
  higher-churn wins; xdist alone is the high-ROI, low-risk change. Possible follow-up if more CI
  time reduction is wanted.
