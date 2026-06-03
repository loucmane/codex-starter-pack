# Task 151 Add reconcile shadow apply artifacts – Implementation Notes

## Planned Workstreams
- `aegis_foundation/reconcile_shadow_apply.py`
  - Added shadow report and record builders that produce artifact-ready `would_apply` or `shadow_refused` records.
  - Reused Task 150 approved-context, kill-switch, authorization binding, idempotency, and audit-record primitives.
  - Added dynamic blast-radius prediction: the Task 148 preview paths are the base, and `.taskmaster/state.json` is added only when the target baseline proves Taskmaster would create it during the sacrificial cascade.
  - Added detached sacrificial clone validation that copies the current target tree into `/tmp`, runs Taskmaster mutation only in the clone, compares actual deltas to prediction, and captures rollback baseline metadata.
  - Added CI artifact mode, which returns artifact-ready JSON without writing repo files, and local/test mode, which may write exactly one declared report path.
- `.github/workflows/ci.yml`
  - Added a read-only shadow context proof artifact capture step. It records GitHub Actions-shaped context proof and uploads through the existing CI artifact path; it does not call apply or Taskmaster mutation.
- `docs/aegis/reconcile-shadow-apply-contract.md`
  - Added the active Task 151 contract and enforcement map.
- `docs/aegis/reconcile-promotion-contract.md`
  - Updated the reconcile sequence to include Task 151 as prediction-validated shadow evidence before any future write code.
- Tests
  - Added `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`.
  - Adjusted preview/rollback expectations to keep Task 147's registered fixture intact while Task 151 records target-specific dynamic shadow evidence.
  - Added a CI-compatible skip guard for the three real Taskmaster sacrificial-cascade tests when the `task-master` CLI is not installed. Local environments with Taskmaster still execute the real cascade; CI environments without the CLI skip those optional real-cascade assertions, matching the existing rollback contract behavior.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py` - PASS, 17 tests.
- `PYTHONDONTWRITEBYTECODE=1 uv run black --check aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py` - PASS.
- `PYTHONDONTWRITEBYTECODE=1 uv run ruff check aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py` - PASS.
- `env PATH=/home/loucmane/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo` - PASS, 3 skipped when `task-master` is absent from PATH.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_ci_workflows.py -k 'reconcile or shadow or workflow'` - PASS, 213 selected tests passed, 1 skipped.
