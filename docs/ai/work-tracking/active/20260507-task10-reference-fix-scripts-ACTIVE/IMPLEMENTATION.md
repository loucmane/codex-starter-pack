# Task 10 Implement Reference Fix Scripts – Implementation Notes

## Planned Workstreams
- Scope reconciliation: complete. Current gap is safe supported reference-fix execution, not direct application of generated fixes.
- Implement safe runner: complete. Added `scripts/template-ssot-scanner/apply_reference_fixes.py` with dry-run-by-default behavior, explicit `--apply`, backups, JSON logging, symlink skipping, repo-root discovery, and git-backed rollback.
- Update fix generator wrappers and README: complete. `generate_fixes.py` now emits a wrapper delegating to the tracked runner, and `apply_all_fixes.sh` defaults to dry-run until `--apply`.
- Add tests for dry-run, apply backup, rollback, and symlink safety: complete. `scripts/template-ssot-scanner/test_cli_behavior.py` covers runner behavior and generated wrapper output.
- Evidence: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest scripts/template-ssot-scanner/test_*.py` passed with `133 passed`; current dry-run evidence is stored in `reports/reference-fix-scripts/dry-run-2026-05-07.json`.
