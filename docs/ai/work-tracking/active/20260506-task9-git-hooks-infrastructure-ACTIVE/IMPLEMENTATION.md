# Task 9 Setup Git Hooks Infrastructure – Implementation Notes

## Planned Workstreams
- Scope reconciliation against the current portable foundation and existing hook/CI state.
- Add a tracked hook parity verifier for local pre-commit setup.
- Capture regression evidence and close Taskmaster Task 9 without executing stale `.git/hooks/` or `SKIP_HOOKS=1` wording.

## Completed Changes
- Added `python3 scripts/codex-task hooks verify`.
- The verifier checks that `.pre-commit-config.yaml` still contains:
  - `python3 scripts/codex-guard validate --include-untracked`
  - `python3 scripts/codex-guard drift-check --strict --report-dir ""`
  - filename-independent and always-on hook behavior through `pass_filenames: false` and `always_run: true`.
- The verifier prefers `.venv/bin/pre-commit`, falls back to `pre-commit` on `PATH`, and records the detected version.
- Default verification reports a missing local `.git/hooks/pre-commit` install as a warning so fresh clones and CI can inspect state without failing.
- `--require-installed` turns that warning into a failure for local parity checks.
- Installed the local pre-commit hook through `.venv/bin/pre-commit install`; strict verifier now passes.

## Test Coverage
- Added focused `tests/meta_workflow_guard/test_codex_task.py` coverage for:
  - parser support for `hooks verify`
  - missing pre-commit executable failure
  - missing local hook warning mode
  - strict missing local hook failure
  - installed hook acceptance
  - executable but unmanaged hook rejection
  - missing required guard/drift config entry failure
- Re-ran the existing `.pre-commit-config.yaml` regression in `tests/meta_workflow_guard/test_guard_rules.py`.
