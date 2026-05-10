# Task 16 Performance Testing Harness Scope Reconciliation

**Captured**: 2026-05-10 12:13 CEST  
**Task**: 16 - Create Performance Testing Harness

## Historical Task Wording

Task 16 asks for a comprehensive performance testing suite:

- `performance_tests.py` with `pytest-benchmark`
- template discovery under 50 ms
- context token usage reduction
- scanner incremental performance under 10 seconds
- guard validation under 5 seconds
- top-template profiling
- baseline capture
- regression detection at warning +20% and critical +50%
- CI performance gates

That wording came from an earlier migration-program framing. The current repository is now a portable Codex workflow foundation with static scripts, Taskmaster state, scanner outputs, template metrics, monitoring reports, Phase 0 validation, and GitHub Actions. Task 16 must therefore implement the remaining measurable performance gap without creating a parallel monitoring platform or duplicating completed scanner/dashboard tasks.

## Current Repository Evidence

- `pyproject.toml` already includes `pytest-benchmark` in the dev dependency group, but no durable performance harness or benchmark suite exists.
- Task 1 captured one-time performance notes in `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/performance-baseline.md`; those measurements are evidence, not a reusable gate.
- Task 17 implemented static monitoring over `reports/template-metrics/latest.json`, but that evaluates static health metrics rather than runtime durations.
- Task 25 implemented `scripts/template-phase0-validation`, but that validates scanner output completeness/security/monitoring status rather than performance regression.
- Task 45 added scanner profiling metadata and fixed scanner statistics, but it does not provide a cross-command performance baseline, regression comparison, or CI artifact.
- Task 61 remains pending and is the right place for deeper template discovery optimization if Task 16 evidence shows a real bottleneck.
- `scripts/template_registry.py` already has TTL cache support and `discovery_metrics()`. A quick current probe measured registry record discovery around `0.029s`, so the old `<50ms` discovery target is plausible but should be measured through a harness rather than hardcoded as a test that flakes.
- `python3 scripts/codex-guard validate --include-untracked` currently fails only because Task 16 scope artifacts are incomplete (`plan-step-scope` evidence missing and Serena memory missing), not because guard runtime is slow.

## Scope Decision

Task 16 should implement a portable, file-based performance harness that times selected foundation operations, evaluates them against repo-local thresholds, compares them with an optional baseline file, and writes durable Markdown/JSON evidence.

Implementation should:

- add a repo-local performance policy under `templates/metadata/`
- add a static performance harness script under `scripts/`
- support built-in and command-based probes without introducing a service, database, or long-running monitor
- time template registry discovery/warm-cache behavior
- time guard validation and scanner no-checkpoint execution as command probes
- classify outcomes as `pass`, `warn`, or `fail`
- classify baseline regressions with warning and critical percentages
- write `reports/template-performance/latest.md` and `latest.json`
- support strict mode that exits nonzero only for fail-level outcomes
- expose the report through `python3 scripts/codex-task report generate --kind performance|all`
- wire CI to generate and upload performance report artifacts
- keep paths portable through `_repo_structure.load_repo_structure()`
- add focused tests for threshold classification, regression classification, report writing, policy loading, codex-task wiring, and CI workflow wiring

## Out of Scope

- Deep template discovery optimization. That belongs to Task 61 after this harness produces durable evidence.
- Live monitoring infrastructure, Prometheus, Grafana, StatsD, Elasticsearch, or remote telemetry. Task 17 intentionally chose static file-based monitoring for this repository.
- Rewriting the scanner suite or adding persistent incremental scanner caches. Task 45 explicitly rejected parallelism/caching until evidence justifies it.
- Committing regenerated scanner runtime outputs under `scripts/template-ssot-scanner/output/data/`; scanner command probes should write temporary outputs.
- Strictly enforcing the old `pytest-benchmark` shape if a static harness gives stronger portability and CI evidence. `pytest-benchmark` remains available for future benchmark tests, but this task should prioritize a deterministic report contract first.

## Proven Gap

The repository can generate scanner outputs, template metrics, monitoring reports, and Phase 0 validation reports, but it cannot yet answer:

- How long did core foundation operations take in this run?
- Did a run exceed repo-local warning or critical duration thresholds?
- Did a run regress from a stored baseline by more than warning or critical percentages?
- Can CI upload a single performance report artifact alongside guard, metrics, monitoring, and Phase 0 reports?
- Can future optimization tasks use measured evidence instead of stale performance assumptions?

## Implementation Boundary For 16.2

Expected code/data/test surface:

- `templates/metadata/template-performance-policy.json`
- `scripts/template-performance-harness`
- `reports/template-performance/README.md`
- `scripts/_repo_structure.py`
- `scripts/codex-task`
- `.github/workflows/codex-guard.yml`
- `.github/workflows/meta-workflow-guard.yml`
- `tests/meta_workflow_guard/test_template_performance_harness.py`
- targeted updates to codex-task/repo-structure/CI workflow tests

Expected behavior:

- policy loads from the configured templates root
- output path defaults to the configured reports root
- built-in probes avoid mutating repository state
- command probes write temporary scanner output when needed
- threshold failures and command failures are visible in both JSON and Markdown
- optional baseline comparison reports `regression_pct`
- `--strict` exits nonzero on fail-level outcomes
- `codex-task report generate --kind all` includes the performance report after existing drift/metrics/monitoring/phase0 steps

## Verification Plan

- Run focused performance harness and codex-task tests.
- Run relevant registry, scanner, metrics, monitoring, phase0, and guard tests touched by this task.
- Generate sample performance report evidence under Task 16 reports.
- Capture plan sync, work-tracking audit, guard, diff-check, and Taskmaster health evidence.

## S:W:H:E

- **2026-05-10 12:13 CEST** - [S:20260510|W:task16-performance-testing-harness|H:docs/scope|E:docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/designs/performance-testing-scope-reconciliation.md] Reconciled Task 16 from broad historical benchmark wording to a portable static performance harness grounded in current foundation evidence.
