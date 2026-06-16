# Findings

- 2026-06-16 — Only `ci.yml` runs pytest (meta-workflow-guard uses `unittest`; codex-guard runs
  no tests). So pytest parallelism is contained to one job and won't affect the other workflows.
- 2026-06-16 — The full suite passed serially only by ACCIDENT OF TEST ORDERING. Running it
  under `-n auto` exposed two latent ordering/shared-state bugs (pre-existing, masked by serial
  order): (1) cross-test git-config leakage — a `git commit` without `-c commit.gpgsign=false`
  passed only because an earlier test had leaked a global gpgsign=false; (2) a shared fixed
  real-repo fixture path in `test_guard_rules.py` (~9 tests reuse the same
  `docs/ai/work-tracking/active/20300101-task99-workflow-ACTIVE`).
- 2026-06-16 — Methodology: ran the full suite under `-n auto` 5× with a CI-like isolated git
  config to separate the local-only gpgsign artifact from true CI-relevant races. The 5-run
  union named exactly one offender (the guard-rules file), which directed a minimal fix
  (pin that file) rather than a broad refactor.
- 2026-06-16 — No benchmark tests exist and no test uses the `performance` marker, so parallel
  CPU contention won't destabilize timing-sensitive tests. No `--cov` in the CI pytest step, so
  no pytest-cov + xdist coordination needed.
- 2026-06-16 — Speedup measured: 323s serial → ~60s under `-n auto` (32 cores), stable across
  6 runs with zero failures. On a 4-vCPU runner the pytest portion should see ~3–4×.
