# Task 193 — Reduce CI feedback time (design)

> Filename is the generic kickoff-scaffold name; this is the Task 193 design artifact
> (`plan-step-scope`).

## Scope reconciliation (what's actually slow)
Four workflows: `aegis-witness` (~15s), `guard` (~30s), `meta-workflow-guard` (unittest +
scripts, fast), and **`ci.yml`** — a 2-leg matrix (Python 3.11/3.12) where each leg runs
install → Taskmaster provision → 4 version-independent shadow-capture steps → **the full pytest
suite (1688 tests)** → artifact upload. Feedback time = the slowest leg, and the pytest run is
the dominant cost (~5min locally, ~10–12min on the runner). Only `ci.yml` runs pytest.

## Change (coverage-preserving)
**Parallelize pytest with pytest-xdist `-n auto`.** Same tests, same coverage — just spread
across the runner's cores. Local measurement: full suite 315s serial → ~70s under `-n auto`
(32 cores). On a 4-core runner expect ~3–4× on the pytest portion.

- `pyproject.toml`: add `pytest-xdist` to the dev group.
- `ci.yml`: `python3 -m pytest -n auto --dist loadgroup`.
- Not added to `addopts` (kept out of local default / other invocations) — contained to CI.

## Parallel-safety (the real work)
The suite was only passing *serially by accident of ordering*. Two latent bugs surfaced under
xdist, found by running the full suite under `-n auto` 5× with a CI-like git config:

1. **Developer git config leaked across tests.** A git test ran `git commit` without
   `-c commit.gpgsign=false`; it only passed because an earlier test leaked a global
   `gpgsign=false`. With a developer's real `commit.gpgsign=true` and per-worker processes, it
   failed. Fix: **`conftest.py`** — a session/autouse fixture pointing
   `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` at an isolated per-worker config (gpgsign off,
   identity, defaultBranch=main). Every test/worker gets a clean git env matching CI; no
   cross-test leakage. (CI has no gpgsign, so this is a local-dev correctness fix that also
   hardens isolation.)
2. **Shared real-repo fixture path.** `test_guard_rules.py`'s `_create_work_tracking_fixture`
   creates folders at FIXED paths under the real repo's `docs/ai/work-tracking/active/`
   (the guard validators resolve paths relative to `REPO_ROOT`, so the fixtures can't move to
   tmp), and ~9 tests reuse the same name → concurrent workers race (create/rmtree collisions).
   The 5-run union showed this is the ONLY true CI-relevant race. Fix: pin the whole module to
   one xdist group (`pytestmark = pytest.mark.xdist_group(...)`) + run with `--dist loadgroup`,
   so those tests serialize on a single worker (like a non-parallel run) while everything else
   stays fully granular. (A worker-unique-rename attempt was rejected — the names test passes
   hardcoded `entries` referencing the fixed path, so renaming desyncs them.)

## Why loadgroup, not loadfile
Default `load` is the most granular (fastest) but exposes the guard-rules race. `loadfile`
(group every file) is robust but makes the biggest file the wall-clock floor. `loadgroup`
pins ONLY the one unsafe file and keeps the rest granular — best speed, justified because the
5-run aggressive-`load` collection showed guard-rules is the sole offender.

## Coverage proof
`-n auto` runs the identical test set (xdist distributes, doesn't drop). No `--cov` in the CI
pytest step, so no cov+xdist coordination needed. No benchmark/perf-marked tests to destabilize
under parallel CPU load.
