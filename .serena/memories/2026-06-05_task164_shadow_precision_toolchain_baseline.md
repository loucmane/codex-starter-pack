# Task 164 Shadow Precision Toolchain Baseline

- Branch: `feat/task-164-shadow-precision-toolchain-baseline`.
- PR: #164.
- Goal: make the shadow precision corpus CI staleness gate compare a source-controlled validated toolchain baseline against live captured current toolchain evidence.
- Original finding: `.github/workflows/ci.yml` supplied only `validated_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`, so `build_shadow_precision_corpus_artifact()` fell back to comparing that live capture to itself. The gate was structurally present but dormant at the CI integration point.
- Implementation:
  - Added `build_validated_taskmaster_ci_toolchain_baseline()` to `aegis_foundation/taskmaster_toolchain.py`.
  - Baseline uses pinned constants: `task-master-ai@0.43.1`, Node major `22`, provisioning lock id/version, expected CI runner `Linux`/`X64`, and the active Python matrix version.
  - Updated CI precision corpus capture to pass `validated_toolchain_evidence=build_validated_taskmaster_ci_toolchain_baseline(os.environ)` and `current_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`.
  - Added tests proving matching current evidence passes and drifted Taskmaster current evidence suppresses metrics/fails `toolchain_mismatch`; workflow tests forbid returning to `validated_toolchain_evidence=capture(...)`.
  - Updated `docs/aegis/reconcile-shadow-apply-contract.md` to define distinct validated/current toolchain records and forbid self-comparison.
- CI finding after first PR run `27011627783`: both Python jobs failed in `Capture reconcile shadow precision corpus` because the baseline helper import was added to the cascade step but not the precision step. Fixed locally by moving the import and strengthening `test_python_test_workflow_captures_shadow_precision_corpus_artifact` to inspect only the precision step `run` body.
- Verification so far:
  - `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py -q` -> 19 passed before and after the import fix.
  - `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_taskmaster_toolchain_mismatch_invalidates_prior_cascade_evidence -q` -> 20 passed before the import fix.
  - `git diff --check` passed.
  - `python3 scripts/codex-task taskmaster health` passed.
  - `python3 scripts/codex-task work-tracking audit` passed before the import-fix commit; rerun after committing the fix.
- Remaining before marking Task 164 done: commit/push import fix, wait for PR CI, inspect the precision corpus artifact for `toolchain_binding.comparison.matches == true` and `$RUNNER_TEMP/aegis-shadow`, then close out Taskmaster/work-tracking.