# Task 160 Shadow Evidence Hardening Completion

Completed Taskmaster Task 160 on branch `feat/task-160-shadow-evidence-hardening`.

## Runtime Changes
- `aegis_foundation/reconcile_shadow_apply.py`
  - Delegates shadow Taskmaster authority checks to `scripts._aegis_installer._taskmaster_state`.
  - Adds `.taskmaster/state.json` semantic validation for optional shadow deltas.
  - Refuses meaningful state mutations as `state_json_unexpected_mutation`.
  - Forces `build_shadow_accumulation_report()` to emit refused-only reports when `valid_for_shadow` is false.
- `scripts/_aegis_installer.py` and `aegis_foundation/assets/scripts/_aegis_installer.py`
  - Treat empty Taskmaster task authority as invalid.
- `.github/workflows/ci.yml`
  - Writes post-merge shadow accumulation artifacts to `$RUNNER_TEMP/aegis-shadow/`.
  - Keeps job permissions at `contents: read`.
  - Asserts zero governed-repo deltas around the real accumulation step.
- `.gitignore`
  - Ignores `reports/` runtime artifacts.

## Verification
- Focused: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py` -> 51 passed.
- Broader targeted: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py` -> 140 passed, 1 skipped.
- Full: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest` -> 1087 passed, 4 skipped.
