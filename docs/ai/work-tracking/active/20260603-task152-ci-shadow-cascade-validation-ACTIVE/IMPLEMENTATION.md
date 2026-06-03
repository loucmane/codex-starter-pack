# Task 152 Add CI sacrificial cascade validation for reconcile shadow apply – Implementation Notes

## Planned Workstreams
- `aegis_foundation/taskmaster_toolchain.py`
  - Added the shared Taskmaster provisioning lock for `task-master-ai@0.43.1`.
  - Added install-spec, lock-id, capture, and comparison helpers.
  - Captured version/source, provisioning lock id, Node/Python/runtime, and runner identity so future apply code can refuse stale cascade evidence.
- `aegis_foundation/reconcile_shadow_apply.py`
  - Added `build_ci_shadow_cascade_validation_report` to generate artifact-ready CI evidence.
  - Covered both `.taskmaster/state.json` baseline branches under the same toolchain.
  - Corrected the dynamic predictor from "state.json only if absent" to "state.json is part of the pinned Taskmaster status-cascade delta"; real validation showed Taskmaster rewrites the file when it already exists.
  - Kept all Taskmaster mutation restricted to detached sacrificial clones under temp directories.
- `.github/workflows/ci.yml`
  - Added Node 22 setup.
  - Installed the pinned Taskmaster CLI via `python3 -m aegis_foundation.taskmaster_toolchain install-spec`.
  - Captured `reports/ci/taskmaster-toolchain.json`.
  - Captured `reports/ci/reconcile-shadow-cascade-validation.json` before pytest.
- Tests
  - Added focused tests for CI artifact contents, both `state.json` baseline branches, and toolchain mismatch invalidation.
  - Added workflow contract tests requiring pinned Taskmaster provisioning before pytest and cascade artifact capture without any apply surface.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 uv run black --check aegis_foundation/taskmaster_toolchain.py aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 uv run ruff check aegis_foundation/taskmaster_toolchain.py aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_ci_workflows.py -q` - PASS, 27 tests.
- `env PATH=/home/loucmane/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_prediction_includes_preexisting_state_json_delta tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_ci_shadow_cascade_validation_report_covers_both_state_json_branches -q` - PASS, 5 skipped when `task-master` is absent from PATH.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_ci_workflows.py -k 'reconcile or shadow or workflow'` - PASS, 218 selected tests passed, 1 skipped.
