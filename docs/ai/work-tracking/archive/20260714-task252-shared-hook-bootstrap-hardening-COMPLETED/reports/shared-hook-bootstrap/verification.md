# Task 252 Shared-Hook Bootstrap Verification

## Incident Reproduction and Root Cause

- Observed failure: installed-project hooks attempted to open `/home/loucmane/codex/.claude/scripts/gate_lib.py` and failed when that mutable source file was transiently absent.
- Root cause: target hook wrappers called the target shim, but the shim imported the central source CLI, whose hook dispatcher executed the central source gate runtime. The apparent target-local bootstrap therefore retained a shared mutable availability dependency.
- Compounding risk: managed install wrote files directly in natural asset order and restored only newly created paths after failure, allowing a mixed old/new runtime generation.

## Implemented Invariants

1. Every generated Codex hook command enters the target's `.aegis/bin/aegis` shim.
2. Non-readiness hooks execute the target's managed `gate_lib.py` before central source resolution.
3. Required policy phases fail closed when local bytes are absent; passive phases stay available.
4. Missing-runtime diagnostics are one line, once per phase, until recovery.
5. Managed writes are atomic; dependencies precede entrypoints; activation files are last.
6. A failed install restores all modified prior bytes and modes, including the manifest, then removes only newly created paths.
7. Exact known legacy hooks migrate; unknown Aegis-like or project-owned hooks are not silently overwritten.
8. Source and packaged runtime mirrors remain byte-identical.

## Focused Results

- `pytest -q tests/meta_workflow_guard/test_codex_hook_bootstrap.py` — **7 passed**.
- Focused compatibility rerun after lifecycle/readiness hardening — **11 passed**.
- Installer/adapter/managed-update compatibility suite — **169 passed, 1 opt-in certification smoke skipped**.
- `git diff --check` — **passed**.
- Source/package byte comparisons for `_aegis_installer.py` and `gate_lib.py` — **passed**.

## Repository-Wide Result

- `pytest -q` from `/tmp/codex-task252-commit` — **2,037 passed, 4 opt-in smokes skipped, 1 failed**.
- The single provisional failure was `test_test_enabled_apply_refuses_governed_repo_target_before_validation`. It deliberately decides whether `REPO_ROOT` is under `/tmp`; the implementation worktree is under `/tmp`, so the fixture was treated as an allowed isolated target and reached the live Task 42 freshness check. The tested production module is unchanged by Task 252.
- `pytest -q` from `/home/loucmane/codex/.git/aegis-verification/task252-bf1c6fb` at exact implementation commit `bf1c6fb` — **2,038 passed, 4 explicit opt-in smokes skipped, 0 failed** in 376.74 seconds.
- The non-temp rerun exercised the test's intended governed-repository branch and removed the only provisional ambiguity.

## Rollback

- Before merge: close the Task 252 PR; installed projects are unchanged.
- After merge: revert the Task 252 squash commit through a reviewed PR.
- After a downstream update: the installer transaction itself restores the previous managed bytes if apply fails. A successful downstream update can be rolled back by updating to the prior reviewed source commit through the supported runtime/update flow.

## Source-Checkout Terminal State

- Taskmaster Task 252 status: **done**.
- Taskmaster health: **251 tasks, 383 subtasks, 439 valid dependency references, 0 invalid**.
- Task 243 generated dependency state: Task 252 **satisfied**.
- `python3 scripts/codex-task work-tracking archive --folder 20260714-task252-shared-hook-bootstrap-hardening-ACTIVE` — **passed**.
- `.claude/scripts/readiness.sh` after archive — **READY, 8/8 checks**, derived from the completed source archive.
- No installed manifest, `.aegis/state/current-work.json`, generic repair, or fabricated target state was introduced into the source checkout.
