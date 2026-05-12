# Task 68 Final Validation Scope Reconciliation

## Purpose

Task 68 originally asked for a broad final validation suite: checklist automation, reference integrity, performance, security, compatibility, cost, report generation, and validation sign-off.

That wording predates the current portable foundation. The current implementation must therefore reconcile the old request against the validation pieces that now exist, then add the smallest missing layer that makes final validation repeatable.

## Current Repository Evidence

The current foundation already has these validation primitives:

- `python3 scripts/codex-task taskmaster health` validates the full Taskmaster dependency graph and avoids filtered-list false warnings.
- `python3 scripts/codex-task plan sync` validates plan/tracker parity and records sync evidence.
- `python3 scripts/codex-task work-tracking audit` validates active work-tracking/session state.
- `python3 scripts/codex-guard validate --include-untracked` validates workflow, plan, session, tracker, metadata, and timestamp rules.
- `python3 scripts/codex-guard drift-check --strict` validates governed template drift.
- `python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci` regenerates scanner evidence, including reference/security scanner outputs.
- `python3 scripts/template-ssot-scanner/apply_reference_fixes.py --dry-run --fail-on-changes` fails when automatic reference fixes are pending.
- `python3 scripts/codex-task report generate --kind all --strict-drift --strict-monitoring --strict-phase0 --strict-performance --strict-cost` runs the static drift, metrics, monitoring, Phase 0, performance, and cost report pipeline.
- `python3 scripts/codex-task agent compatibility-report --strict` validates and summarizes the portable agent compatibility matrix.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest` is the CI-backed regression suite.
- `git diff --check` validates whitespace and patch formatting.

## Confirmed Current Gap

The repository has strong individual validation commands, but no single final-validation command that:

- maps Task 68's historical checklist to the current command set;
- executes or dry-renders the full sign-off suite in one predictable order;
- captures stdout/stderr evidence per validation check;
- produces a machine-readable summary and a human runbook;
- keeps sign-off criteria explicit without duplicating the existing validator engines.

Without that layer, final validation remains a remembered checklist assembled by the current agent, which is exactly the behavior the foundation is meant to avoid.

## Chosen Implementation Shape

Implement a `python3 scripts/codex-task validation final-suite` subcommand.

The command will:

1. Build a final-validation manifest from the current Git, workflow, Taskmaster, and Serena snapshots.
2. Define requirement coverage for checklist automation, reference integrity, security, performance, cost, compatibility, report generation, regression tests, and sign-off.
3. Provide a dry-run mode that prints the suite plan without executing commands.
4. Provide an execute mode that runs the suite, captures per-check logs under a chosen report directory, and writes JSON plus Markdown runbook outputs.
5. Continue through all checks so failures produce complete evidence, then fail the command unless `--allow-failures` is explicitly passed.

This keeps Task 68 aligned with the portable foundation: it orchestrates existing validators and captures sign-off evidence rather than creating parallel security/performance/cost engines.

## Non-Goals

- Do not replace `codex-guard`, Taskmaster health, work-tracking audit, scanner, performance, cost, or compatibility validators.
- Do not add external services, hosted dashboards, approval integrations, or GitHub repository settings.
- Do not require a clean working tree during active task work; final status evidence records dirty state while `git diff --check` handles patch hygiene.
- Do not mutate repository files outside the report outputs produced by the validation suite and the existing report generators it runs.

## Planned Files

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/engine/validation/foundation-adoption-guide.md`
- `docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/` task artifacts
- Taskmaster Task 68 artifacts

## Evidence Plan

- `python3 scripts/codex-task validation final-suite --dry-run`
- `python3 scripts/codex-task validation final-suite --execute --report-dir docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Decision

Proceed with a suite orchestrator plus sign-off report. This satisfies the historical Task 68 acceptance language by making final validation explicit, executable, evidence-backed, and portable without duplicating validators that already exist.
