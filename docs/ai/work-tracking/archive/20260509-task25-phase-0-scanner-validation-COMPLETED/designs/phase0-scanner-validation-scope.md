# Task 25 Phase 0 Scanner Validation Scope Reconciliation

**Captured**: 2026-05-09 12:05 CEST  
**Task**: 25 - Execute Phase 0 Scanner Validation

## Historical Task Wording

Task 25 asks to complete a Phase 0 validation gate for the scanner suite:

- run comprehensive scanner unit tests
- execute security validation checks
- generate baseline performance metrics
- document scanner accuracy metrics
- create compatibility baseline report
- set up monitoring infrastructure verification
- prepare Phase 0 gate review documentation
- schedule stakeholder review meeting

That wording came from an earlier migration-program framing. The current repository is a portable foundation/starter-pack with local scanners, static reports, Taskmaster state, GitHub Actions, and work-tracking evidence. It does not need a human scheduling artifact to represent a validation gate.

## Current Repository Evidence

- Task 3 completed the scanner-suite foundation and hardened CLI/runtime behavior.
- Task 4 completed scanner configuration, validation, rule severity, allow/block matching, inheritance, environment overrides, and dependency injection.
- Task 7 completed baseline scanner outputs and added `baseline_summary.json`.
- Task 17 completed static monitoring over template metrics and added `scripts/template-monitoring`.
- `scripts/template-ssot-scanner/run_all_scanners.py` can run the full scanner suite and produce metadata-wrapped outputs under `scripts/template-ssot-scanner/output/data/`.
- `scripts/template-ssot-scanner/security_validator.py` produces metadata-wrapped security findings.
- The repo has raw scanner outputs and raw monitoring outputs, but no single Phase 0 gate report that says whether the scanner baseline is currently acceptable.

## Scope Decision

Task 25 should implement a portable, static Phase 0 scanner validation gate. The gate should consume existing scanner output and monitoring artifacts, classify checks as pass/warn/fail, and write durable Markdown/JSON evidence.

Implementation should:

- add a Phase 0 validation evaluator script
- validate required scanner output files exist and use the metadata wrapper
- validate baseline summary required metrics are present
- validate security findings contain no error-level findings
- validate monitoring status does not fail
- produce `reports/phase0-scanner-validation/latest.md` and `latest.json`
- expose the gate through `python3 scripts/codex-task report generate --kind phase0|all`
- keep paths portable through `_repo_structure.load_repo_structure()`
- add focused tests for pass/warn/fail behavior, missing artifacts, report output, codex-task wiring, and portable roots

## Out of Scope

- Rewriting the scanner suite.
- Changing historical scanner findings just to make the gate green.
- Introducing remote services, dashboards, or manual stakeholder scheduling artifacts.
- Treating warning-level scanner issues as blockers unless a policy explicitly makes them error-level.
- Committing freshly regenerated runtime scanner outputs unless they are intentionally captured as task evidence.

## Proven Gap

The repository can generate scanner outputs, baseline summaries, metrics, and monitoring reports, but it lacks one explicit Phase 0 validation artifact answering:

- Are the scanner outputs complete and metadata-wrapped?
- Are baseline summary metrics present for scanner review?
- Are there error-level security findings?
- Did the static monitoring gate fail?
- Can CI or a reviewer inspect one Phase 0 gate report instead of reading several raw outputs?

## Implementation Boundary For 25.2

Expected code/data/test surface:

- `scripts/template-phase0-validation`
- `reports/phase0-scanner-validation/README.md`
- targeted updates to `_repo_structure.py` and `scripts/codex-task`
- `tests/meta_workflow_guard/test_phase0_scanner_validation.py`
- targeted updates to codex-task/repo-structure tests

Expected behavior:

- evaluator reads existing scanner output files without mutating them
- report status is `fail` for error-level findings, `warn` for warning-only findings, and `pass` when all checks pass
- strict mode exits nonzero only when report status is `fail`
- `codex-task report generate --kind all` runs drift, metrics, monitoring, then phase0
- output paths derive from repo-structure configuration

## Verification Plan

- Run focused phase0/codex-task/repo-structure tests.
- Run the current scanner test suite or full pytest before closeout.
- Generate sample Phase 0 validation evidence under Task 25 reports.
- Capture plan sync, work-tracking audit, guard, diff-check, and Taskmaster health evidence.
