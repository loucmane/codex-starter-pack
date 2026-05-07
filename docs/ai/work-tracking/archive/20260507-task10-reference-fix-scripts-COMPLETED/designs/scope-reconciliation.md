# Task 10 Scope Reconciliation

## Current Evidence

- Task 10 originally says to port `apply_reference_fixes.py` from the FPL repo, add safe mode, dry-run preview, an `apply_all_fixes.sh` wrapper, git rollback, logging, and special-case handling.
- The current repo already has scanner and generated-fix infrastructure under `scripts/template-ssot-scanner/`.
- `scripts/template-ssot-scanner/generate_fixes.py` currently emits `output/scripts/apply_reference_fixes.py` as a generated script, but that generated script is not tracked as source, has no real CLI, has no `--dry-run`, has no backup creation, has no git rollback, and applies broad replacements when executed.
- `scripts/template-ssot-scanner/README.md` advertises `python3 output/scripts/apply_reference_fixes.py --dry-run`, but the generated script does not accept that flag.
- `templates/engine/core/portable-foundation-spec.md` says core logic should remain portable and config-driven while repo-local layouts remain adapter data. Task 10 should therefore improve the scanner tool boundary instead of applying stale generated reference fixes directly to templates.

## Scope Decision

Task 10 will implement a first-class, tracked reference-fix application command in the scanner suite and update `generate_fixes.py` so generated scripts delegate to that supported command.

In scope:

- Add `scripts/template-ssot-scanner/apply_reference_fixes.py` as the supported reference-fix runner.
- Default to dry-run behavior unless the user passes `--apply`.
- Support detailed previews, apply mode with backups, JSON/text logging, symlink refusal by default, repo-root discovery, scoped/global replacements, and git-based rollback through explicit `--rollback --apply`.
- Update `generate_fixes.py` to emit safe wrappers instead of embedding an unsafe one-off mutation script.
- Update `scripts/template-ssot-scanner/README.md` to document the safe flow.
- Add focused tests in `scripts/template-ssot-scanner/test_cli_behavior.py`.

Out of scope:

- Applying the current generated reference fixes to the template tree.
- Moving files or archiving duplicates.
- Replacing `safe_reorganize.py`.
- Solving circular dependencies in this task.

## Acceptance

- Dry-run mode does not modify files.
- Apply mode writes backups before modifying files.
- Rollback mode restores changed files via `git restore`.
- Symlink targets are skipped unless explicitly allowed.
- Generated wrappers call the supported runner instead of duplicating unsafe logic.
- Focused scanner tests, plan sync, work-tracking audit, codex guard, and `git diff --check` pass.

## Progress Log

- **2026-05-07 14:32 CEST** — [S:20260507|W:task10-reference-fix-scripts|H:docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/designs/scope-reconciliation.md|E:.taskmaster/tasks/task_010.txt] Reconciled Task 10 against current scanner infrastructure and narrowed implementation to a safe, tracked reference-fix runner plus generated wrappers.
