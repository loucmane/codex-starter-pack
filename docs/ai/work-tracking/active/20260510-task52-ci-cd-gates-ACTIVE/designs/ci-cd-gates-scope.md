# Task 52 CI/CD Gates Scope Reconciliation

## Current Baseline

Task 52 depends on Tasks 19 and 38. Task 19 provides rollback safety, and Task 38 completed the current automatic safe-runner reference remediation queue. Task 20 already established the baseline CI workflow.

Current GitHub Actions coverage:

- `.github/workflows/ci.yml` runs Taskmaster health and full pytest across Python 3.11 and 3.12.
- `.github/workflows/codex-guard.yml` runs plan sync, guard validation, drift check, scanner generation, monitoring, Phase 0 validation, performance, and cost reports.
- `.github/workflows/meta-workflow-guard.yml` runs timestamp tests plus the same guard/scanner/report suite for workflow-sensitive paths.

Current test coverage confirms those workflows include:

- Taskmaster health and full pytest.
- Guard and drift checks.
- Scanner baseline generation.
- Phase 0 validation.
- Monitoring, performance, and cost reports.

## Proven Gap

After Task 38, the safe reference-fix runner reached a useful invariant:

```text
Summary: no fixes
```

The CI workflows regenerate scanner outputs, but they do not currently fail when `fix_recommendations.json` contains automatic reference fixes that would change files. That means a future PR could reintroduce references that the safe runner can fix, and CI would still pass as long as the scanner process itself completed.

## Decision

Implement the Task 52 slice as an automatic-reference-fix CI gate:

1. Extend `scripts/template-ssot-scanner/apply_reference_fixes.py` with a check mode that exits nonzero when dry-run results include file-changing automatic fixes.
2. Run that gate in both guard workflows after `run_all_scanners.py --profile ci` regenerates scanner outputs.
3. Upload a `reports/reference-fix-gate/` artifact so failures have machine-readable evidence.
4. Add regression tests for the CLI behavior and workflow contract.

## Non-Goals

- Do not require zero broken references yet. Task 38 intentionally left 41 manual/broader migration references outside automatic safe-runner scope.
- Do not duplicate the existing Phase 0, monitoring, performance, cost, or guard gates.
- Do not implement branch protection or approval gates locally; those require repository settings or a later GitHub governance task.

## Acceptance

- The reference-fix runner exits `1` when `--fail-on-changes` sees `would-change` or `changed` results.
- The reference-fix runner still exits `0` when no automatic changes are pending.
- Both guard workflows run the new gate after scanner generation and upload `reports/reference-fix-gate/`.
- Focused tests prove the behavior.
