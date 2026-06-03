# Task 151 CI Skip Guard

After PR #147 CI failed on Python 3.11 because GitHub Actions does not have a global `task-master` CLI, the Task 151 shadow-apply tests were adjusted to match the existing rollback contract behavior: real sacrificial Taskmaster cascade tests now call a small `_require_taskmaster_cli()` helper and skip when `task-master` is unavailable.

Local verification on the developer machine with Taskmaster installed still executes the real cascade:

- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py` -> 17 passed.

CI-path verification with `task-master` removed from PATH now skips only the three real-cascade tests:

- `env PATH=/home/loucmane/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo` -> 3 skipped.

Adjacent reconcile/workflow subset after the fix:

- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_ci_workflows.py -k 'reconcile or shadow or workflow'` -> 213 passed, 1 skipped.