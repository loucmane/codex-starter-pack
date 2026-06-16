# Task 193 Reduce CI feedback time without reducing coverage – Implementation Notes

## Changes
- `.github/workflows/ci.yml` — pytest step now `python3 -m pytest -n auto --dist loadgroup`
  (parallel across runner cores; same tests/coverage).
- `pyproject.toml` — `pytest-xdist>=3.5.0,<4.0.0` added to the dev dependency group.
- `conftest.py` (new, repo root) — session/autouse fixture isolating
  `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` per worker (gpgsign off, identity, defaultBranch=main),
  so git tests don't depend on the developer's global config or leak config across tests.
- `tests/meta_workflow_guard/test_guard_rules.py` — `pytestmark = pytest.mark.xdist_group(...)`
  pins the module's real-repo-mutating tests to one worker (serial among themselves).

## Why these (root causes, found empirically)
Running the full suite under `-n auto` 5× surfaced exactly two latent ordering bugs that made
the suite unsafe to parallelize: (1) cross-test git-config leakage (a commit missing
`-c commit.gpgsign=false` only passed because another test leaked gpgsign=false), and (2) a
shared fixed real-repo fixture path in test_guard_rules.py. See designs/wizard-flow.md.

## Measurement
Local full suite: 315s serial → ~70s under `-n auto` (32 cores). On a 4-core runner expect
~3–4× on the pytest portion. See reports/ for the parallel-run evidence.

## Verification
Serial full suite green with the conftest; N× `-n auto --dist loadgroup` runs green
(parallel-safe). Captured under reports/.
