# Task 152 CI Shadow Cascade Validation

Task 152 adds CI-environment validation for reconcile shadow apply's sacrificial Taskmaster cascade before any live write path exists.

Implemented:

- `aegis_foundation/taskmaster_toolchain.py`: shared Taskmaster provisioning lock/evidence helper for `task-master-ai@0.43.1`, install spec, lock id, evidence capture, and toolchain comparison. Future apply code must use the same helper; a version/source/provisioning/runtime mismatch makes prior cascade evidence stale.
- `aegis_foundation/reconcile_shadow_apply.py`: `build_ci_shadow_cascade_validation_report`, which builds artifact-ready CI evidence for both `.taskmaster/state.json` baseline branches using the pinned toolchain and detached sacrificial clones only.
- `.github/workflows/ci.yml`: Node 22 setup, pinned Taskmaster CLI install via `python3 -m aegis_foundation.taskmaster_toolchain install-spec`, `reports/ci/taskmaster-toolchain.json`, and `reports/ci/reconcile-shadow-cascade-validation.json` before pytest.
- Tests in `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py` and `tests/meta_workflow_guard/test_ci_workflows.py` cover toolchain mismatch invalidation, CI artifact contents, both `state.json` baseline branches, and no apply/governed-repo mutation surfaces.

Important finding:

- Under pinned `task-master-ai@0.43.1`, `.taskmaster/state.json` is part of the Taskmaster status-cascade delta in both branches. If absent, Taskmaster creates it. If already present, Taskmaster rewrites it. The dynamic shadow blast-radius prediction therefore includes `.taskmaster/state.json` in both branches.

Verification:

- Black and Ruff passed for changed Python files.
- Focused shadow/CI tests: `27 passed`.
- No-task-master PATH simulation: 5 real-cascade tests skipped cleanly.
- Adjacent reconcile/workflow suite: `218 passed, 1 skipped`.

Non-goals preserved: no live write path, no `--apply`, no MCP apply tool, no governed-repo Taskmaster mutation, no persistent multi-run ledger. Task 153 remains the first possible default-off write scaffold and must include partial-apply rollback tests.