# Task 152 Verification Summary

## Scope

Task 152 moves reconcile shadow cascade validation into the CI toolchain environment before
any live write code exists.

It adds:

- pinned Taskmaster CLI provisioning evidence
- comparable toolchain-binding/invalidation evidence
- CI shadow cascade artifact generation
- coverage for both `.taskmaster/state.json` baseline branches
- workflow tests proving no apply surface or governed-repo Taskmaster mutation was added

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run black --check \
  aegis_foundation/taskmaster_toolchain.py \
  aegis_foundation/reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_ci_workflows.py
```

Result: PASS.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check \
  aegis_foundation/taskmaster_toolchain.py \
  aegis_foundation/reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_ci_workflows.py
```

Result: PASS.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_ci_workflows.py -q
```

Result: PASS, 27 tests passed.

```bash
env PATH=/home/loucmane/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_prediction_includes_preexisting_state_json_delta \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_ci_shadow_cascade_validation_report_covers_both_state_json_branches -q
```

Result: PASS, 5 tests skipped when `task-master` is absent from PATH.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py \
  tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py \
  tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py \
  tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py \
  tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py \
  tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_aegis_mcp_server.py \
  tests/meta_workflow_guard/test_ci_workflows.py \
  -k 'reconcile or shadow or workflow'
```

Result: PASS, 218 selected tests passed, 1 skipped.

## Key Finding

The pinned Taskmaster cascade rewrites `.taskmaster/state.json` even when the file already
exists. Task 152 therefore records `.taskmaster/state.json` as part of the dynamic
blast-radius delta in both absent and pre-existing baseline branches.
