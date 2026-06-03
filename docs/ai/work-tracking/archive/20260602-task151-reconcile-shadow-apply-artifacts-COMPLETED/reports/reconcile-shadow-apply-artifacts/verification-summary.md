# Task 151 Verification Summary

## Scope

Task 151 adds shadow-mode reconcile apply artifacts. It runs the future first-class apply
decision pipeline without enabling live mutation.

Shadow mode:

- emits `would_apply` only for `merged_but_not_done` with `git_ancestor` proof
- validates predicted blast radius in a detached sacrificial clone
- keeps live Taskmaster/Git/workflow-state mutation impossible
- returns artifact-ready JSON in CI mode
- permits only one declared local report path in local/test mode

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
```

Result: PASS, 17 tests passed.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run black --check aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
```

Result: PASS.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run ruff check aegis_foundation/reconcile_shadow_apply.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py
```

Result: PASS.

```bash
env PATH=/home/loucmane/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path \
  tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo
```

Result: PASS, 3 skipped when `task-master` is absent from PATH. This mirrors CI hosts that
run the Python suite without a globally installed Taskmaster CLI while preserving local
real-cascade coverage where the CLI is available.

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

Result: PASS, 213 selected tests passed, 1 skipped.

## Notes

The shadow validator found that `.taskmaster/state.json` can be created when a target lacks
that file before a Taskmaster status mutation. Task 151 handles that as target-specific
dynamic shadow evidence while preserving the Task 147 registered fixture contract.
