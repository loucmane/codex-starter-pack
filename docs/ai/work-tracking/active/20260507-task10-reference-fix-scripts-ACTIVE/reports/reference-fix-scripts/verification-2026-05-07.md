# Verification - Task 10 Reference Fix Scripts

## Commands

```text
python3 scripts/template-ssot-scanner/apply_reference_fixes.py --help
exit 0; help lists --fixes-file, --apply, --dry-run, --rollback, --allow-symlinks, --backup-dir, --log-file, and --repo-root.
```

```text
python3 scripts/template-ssot-scanner/apply_reference_fixes.py --dry-run --log-file docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/reports/reference-fix-scripts/dry-run-2026-05-07.json
exit 0; dry-run wrote JSON evidence and did not apply template reference fixes.
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest scripts/template-ssot-scanner/test_cli_behavior.py
13 passed
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest scripts/template-ssot-scanner/test_*.py
133 passed
```

```text
python3 scripts/codex-task plan sync
Plan sync recorded for plans/2026-05-07-task10-reference-fix-scripts.md
```

```text
python3 scripts/codex-task work-tracking audit
Audit passed: no issues found.
```

```text
python3 scripts/codex-guard validate --include-untracked
Guard validation passed: all S:W:H:E entries look compliant.
```

```text
git diff --check
<no output>
```

## Result

Task 10 implementation is verified:

- The tracked runner defaults to dry-run and requires `--apply` before writes.
- Apply mode has tested backup behavior.
- Rollback mode has tested `git restore` behavior.
- Symlink targets are skipped by default.
- Generated wrappers delegate to the tracked runner and default to dry-run.
- No generated template reference fixes were applied in this task.
