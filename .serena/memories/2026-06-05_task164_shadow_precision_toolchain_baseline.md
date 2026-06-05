# Task 164 Shadow Precision Toolchain Baseline

- Branch: `feat/task-164-shadow-precision-toolchain-baseline`.
- PR: #164.
- Goal: make the shadow precision corpus CI staleness gate compare a source-controlled validated toolchain baseline against live captured current toolchain evidence.
- Original finding: `.github/workflows/ci.yml` supplied only `validated_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`, so `build_shadow_precision_corpus_artifact()` fell back to comparing that live capture to itself. The gate was structurally present but dormant at the CI integration point.
- Implementation:
  - Added `build_validated_taskmaster_ci_toolchain_baseline()` to `aegis_foundation/taskmaster_toolchain.py`.
  - Baseline uses pinned constants: `task-master-ai@0.43.1`, Node major `22`, provisioning lock id/version, expected CI runner `Linux`/`X64`, and the active Python matrix version.
  - Updated CI precision corpus capture to pass `validated_toolchain_evidence=build_validated_taskmaster_ci_toolchain_baseline(os.environ)` and `current_toolchain_evidence=capture_taskmaster_toolchain_evidence(os.environ)`.
  - Added tests proving matching current evidence passes and drifted Taskmaster current evidence suppresses metrics/fails `toolchain_mismatch`; workflow tests forbid returning to `validated_toolchain_evidence=capture(...)` and now inspect the precision step body directly.
  - Updated `docs/aegis/reconcile-shadow-apply-contract.md` to define distinct validated/current toolchain records and forbid self-comparison.
- CI finding: first PR run `27011627783` failed in `Capture reconcile shadow precision corpus` because the baseline helper import was added to the cascade step but not the precision step. Fixed in commit `3f46ee1` by moving the import and strengthening the workflow test.
- Verification:
  - Local focused suite before/after import fix: `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py -q` -> 19 passed.
  - Local broader targeted suite: `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_shadow_precision_corpus.py tests/meta_workflow_guard/test_ci_workflows.py tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_taskmaster_toolchain_mismatch_invalidates_prior_cascade_evidence -q` -> 20 passed.
  - `git diff --check`, `python3 scripts/codex-task taskmaster health`, and `python3 scripts/codex-task work-tracking audit` passed.
  - PR #164 run `27012094260` passed both Python 3.11 and 3.12 plus guard workflows.
  - Downloaded artifacts to `/tmp/aegis-task164-ci-F5w4Zf`; both precision corpus artifacts are under `_temp/aegis-shadow/reconcile-shadow-precision-corpus.json` and report `toolchain_binding.comparison.matches=true`, `mismatches=[]`, `precision_metrics.emitted=true`, `precision_gate.passed=true`, `true_positive=6`, `executed=false`, `mutated_live_repo=false`.
- Ready for closeout: mark Task 164 done, generate only `task_164.md`, archive tracker, commit/push closeout, wait for final CI, merge PR #164.