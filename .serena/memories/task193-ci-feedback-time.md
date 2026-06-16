# Task 193 — Reduce CI feedback time (pytest parallelism)

**Status:** done (2026-06-16), branch `feat/task-193-ci-feedback-time`.

## What shipped
CI pytest parallelized with pytest-xdist; suite made parallel-safe.
- `.github/workflows/ci.yml`: pytest step → `python3 -m pytest -n auto --dist loadgroup`.
- `pyproject.toml`: `pytest-xdist>=3.5.0,<4.0.0` in dev group.
- `conftest.py` (repo root, NEW): session/autouse fixture isolating
  `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` per worker (gpgsign off, identity, defaultBranch=main).
- `tests/meta_workflow_guard/test_guard_rules.py`: `pytestmark = pytest.mark.xdist_group(...)`.

## Why (latent bugs xdist exposed)
The suite only passed serially by accident of ordering. Running `-n auto` 5× (under a CI-like
git config to separate local-only artifacts from true races) surfaced exactly two:
1. **Cross-test git-config leak:** a `git commit` lacked `-c commit.gpgsign=false`; it passed
   only because another test leaked a global gpgsign=false. Per-worker processes (or a dev with
   gpgsign=true) broke it. Fixed by the conftest git isolation.
2. **Shared real-repo fixture path:** `_create_work_tracking_fixture` creates folders at FIXED
   paths under the real repo's `docs/ai/work-tracking/active/` (guard validators resolve paths
   relative to REPO_ROOT, so can't move to tmp); ~9 tests reuse the same name → worker race.
   Fixed by pinning the module to one xdist group (`--dist loadgroup`). NOTE: a worker-unique
   rename was rejected — the names tests pass hardcoded `entries` referencing the fixed path.

## Measurement
323s serial → ~60s `-n auto` (32 cores, 5.4×) / 103s `-n 4` (3.1×, 4-vCPU proxy). 6/6 parallel
runs green with the dev's real gpgsign=true. Coverage unchanged (identical test set; no `--cov`
in CI pytest step; no benchmark/perf-marked tests).

## Reusable knowledge
- ONLY `ci.yml` runs pytest (meta-workflow-guard uses unittest; codex-guard has none).
- To make this repo's suite parallel-safe: isolate git config (conftest) + keep real-repo
  fixed-path fixtures on one worker. The rest of the suite is parallel-safe under bare `load`.
- `loadgroup` > `loadfile` here (pins only the unsafe file, keeps the rest granular).
Deferred: hoist version-independent ci.yml shadow-capture steps out of the matrix + cache npm
Taskmaster (smaller wins). See [[task225-doctor-repair-states]].
