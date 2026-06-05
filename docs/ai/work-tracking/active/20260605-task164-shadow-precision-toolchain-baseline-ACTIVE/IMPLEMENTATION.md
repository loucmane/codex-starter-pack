# Task 164 Wire shadow precision CI toolchain staleness to frozen baseline – Implementation Notes

## Planned Workstreams
- Replace the precision corpus CI self-comparison with a source-controlled validated baseline.
- Keep current evidence as a live capture from the provisioned CI toolchain.
- Preserve default-off behavior: no apply, no enablement, no candidate class broadening, and no governed-repo Taskmaster status mutation.
- Pin workflow and artifact-builder regression tests so future CI edits cannot accidentally make the staleness gate dormant again.

## Implemented
- Added `build_validated_taskmaster_ci_toolchain_baseline()` in `aegis_foundation/taskmaster_toolchain.py`.
  - The baseline is derived from pinned source constants: `task-master-ai@0.43.1`, Node major `22`, provisioning lock id/version, and expected CI runner identity `Linux`/`X64`.
  - The helper emits normal toolchain evidence shape plus `evidence_role=validated_ci_baseline` and `baseline_source` metadata for artifact inspection.
- Updated `.github/workflows/ci.yml` precision corpus capture.
  - `validated_toolchain_evidence` now comes from `build_validated_taskmaster_ci_toolchain_baseline(os.environ)`.
  - `current_toolchain_evidence` now comes from `capture_taskmaster_toolchain_evidence(os.environ)`.
  - The precision corpus gate still runs under `$RUNNER_TEMP` and the whole-tree side-effect oracle.
- Added regression tests in `tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py`.
  - A matching live current toolchain passes the frozen baseline.
  - A drifted current Taskmaster version suppresses metrics and fails the precision gate with `toolchain_mismatch`.
- Strengthened `tests/meta_workflow_guard/test_ci_workflows.py`.
  - The workflow must import/use the baseline helper.
  - The workflow must pass `current_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`.
  - The workflow must not pass `validated_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`.
- Updated `docs/aegis/reconcile-shadow-apply-contract.md` to define the two distinct toolchain records and forbid self-comparison as precision evidence.

## Verification
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py -q` -> 19 passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_taskmaster_toolchain_mismatch_invalidates_prior_cascade_evidence -q` -> 20 passed.
- `git diff --check` -> passed.
- `python3 scripts/codex-task taskmaster health` -> passed.
