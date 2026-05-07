# Task 10 Reference Fix Scripts Kickoff

## Context
- Date: 2026-05-07
- Branch: feat/task-10-reference-fix-scripts
- Taskmaster: Task 10 in progress; 10.1 scope complete; 10.2 implementation/verification in progress.

## Scope Decision
Task 10 is not applying generated template reference fixes directly. It implements safe tooling for applying reference fixes later. Scope is captured in docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/designs/scope-reconciliation.md.

## Implementation State
- Added tracked runner: scripts/template-ssot-scanner/apply_reference_fixes.py
- Runner defaults to dry-run; --apply required for writes.
- Apply mode creates backups, supports JSON logs, skips symlinks by default, discovers repo root, supports scoped/global replacement, and supports git rollback through --rollback --apply.
- Updated scripts/template-ssot-scanner/generate_fixes.py so generated apply_reference_fixes.py is a wrapper around the tracked safe runner, and apply_all_fixes.sh defaults to dry-run.
- Updated scripts/template-ssot-scanner/README.md with safe usage.
- Added tests in scripts/template-ssot-scanner/test_cli_behavior.py.

## Evidence
- Current dry-run evidence: docs/ai/work-tracking/active/20260507-task10-reference-fix-scripts-ACTIVE/reports/reference-fix-scripts/dry-run-2026-05-07.json
- Scanner suite: PYTHONDONTWRITEBYTECODE=1 python3 -m pytest scripts/template-ssot-scanner/test_*.py -> 133 passed.

## Next Steps
- Rerun plan sync, work-tracking audit, codex guard, and git diff --check.
- Mark Task 10.2 and Task 10 done if final verification passes.
- Commit/push with regular Git commands and open PR.