# Task 160 Harden shadow accumulation evidence validation – Implementation Notes

## Planned Workstreams
- Delegate shadow-layer Taskmaster authority checks to the authoritative `_taskmaster_state` model from `scripts/_aegis_installer.py`, preserving the existing public refusal reasons while removing the weaker JSON-only local parser.
- Add a content-level `.taskmaster/state.json` contract to the shadow semantic delta path. Optional state-file path membership remains allowed, but active-tag changes, branch mapping rewrites, unknown keys, malformed values, and invalid JSON now refuse as `state_json_unexpected_mutation`.
- Force `build_shadow_accumulation_report()` to emit refused-only reports when the supplied context is not valid for post-merge shadow accumulation, avoiding `would_apply` records from forged/non-post-merge contexts.
- Move the CI accumulation artifact to `$RUNNER_TEMP/aegis-shadow/` and assert zero governed-repo filesystem deltas around the real accumulation step.
- Add `reports/` to `.gitignore` so local/CI report artifacts remain runtime output.
- Tighten the authoritative Taskmaster state validator to reject empty Taskmaster task authority, mirrored in the packaged installer asset.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py` — 51 passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py` — 140 passed, 1 skipped.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest` — 1087 passed, 4 skipped.
