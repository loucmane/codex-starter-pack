# Task 38 Phase 1 Reference Remediation Scope

## Current Inputs

- Taskmaster Task 38 asks for Phase 1 reference fixes in priority order: engine, patterns, then remaining references.
- Task 10 already delivered the safe runner at `scripts/template-ssot-scanner/apply_reference_fixes.py`.
- Task 13 already delivered durable compatibility mapping at `templates/registry/compatibility-map.json`.
- Task 19 already delivered non-destructive rollback checkpoints through `python3 scripts/codex-task rollback checkpoint`.
- Task 23 already delivered migration rehearsal planning.
- Task 25 already confirmed the Phase 0 scanner validation path; current scanner state may warn while error-level checks pass.

## Fresh Scanner Evidence

Regenerated on 2026-05-10:

- `reports/phase1-reference-remediation/scanner-suite-2026-05-10.txt`
- `reports/phase1-reference-remediation/dry-run-regenerated-2026-05-10.txt`
- `reports/phase1-reference-remediation/dry-run-regenerated-2026-05-10.json`
- `reports/phase1-reference-remediation/dry-run-regenerated-file-counts-2026-05-10.txt`

Key scanner results:

- Files scanned: 342
- Security findings: 0
- Broken references: 186
- Circular dependencies: 14
- Orphaned files: 88
- Fix generator total fixes: 188
- Safe reference-fix dry-run: 141 automatic `would-change` results

## Scope Decision

Task 38 will apply only current, automatically generated reference updates from `scripts/template-ssot-scanner/output/data/fix_recommendations.json` through the Task 10 safe runner.

In scope:

- Regenerate scanner outputs before remediation.
- Capture a rollback checkpoint before mutation.
- Apply safe `update_reference` and `update_reference_scoped` fixes through `scripts/template-ssot-scanner/apply_reference_fixes.py --apply`.
- Preserve backup and JSON/text apply evidence.
- Rescan after apply and compare broken-reference counts.
- Update work-tracking, implementation notes, and Taskmaster status from evidence.

Out of scope for this task:

- Manual-review references with no generated `suggested_fix`.
- Broad monolith completion work from `content_updates` such as migrating remaining `REGISTRY.md`, `HANDLERS.md`, `BEHAVIORS.md`, `MATRICES.md`, or `TOOLS.md` sections.
- Circular dependency redesign and orphaned-file decisions unless they are direct fallout from the applied automatic reference fixes.
- Stale root `output/data/*` artifacts from 2025. Task 38 uses the scanner-suite output under `scripts/template-ssot-scanner/output/data/`.

## Safety Gates

Before apply:

- Dry-run evidence must exist.
- Rollback checkpoint evidence must exist.
- Apply command must use the safe runner, not generated shell scripts.

After apply:

- Run scanner suite again.
- Run focused scanner/reference tests.
- Run `python3 scripts/codex-task plan sync`.
- Run `python3 scripts/codex-task work-tracking audit`.
- Run `python3 scripts/codex-guard validate --include-untracked`.
- Run `python3 scripts/codex-task taskmaster health`.
- Run `git diff --check`.

## Initial Finding

The current automatic remediation is broad but mechanically simple: it mostly rewrites relative markdown references to canonical repository-root-relative template paths. It should be applied as one safe-runner batch with backup and rollback evidence, then judged by scanner delta rather than by assuming all Phase 1 remediation is complete.
