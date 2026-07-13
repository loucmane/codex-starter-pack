# Task 241 Verification Evidence

**Status:** LOCAL IMPLEMENTATION VERIFIED — final-head dogfood and hosted CI pending

## Implemented Contract

- Stable semantic classes and process exits: `pass=0`, `fail=1`,
  `unsupported=2`, and `not_derivable_in_ci=0`.
- Deterministic failures take precedence over incomplete CI evidence.
- Local ledger reads are read-only and filter repository, branch, and canonical
  worktree, retaining null attribution only for legacy compatibility.
- Verification requires an explicit commit that resolves to exact current HEAD;
  timestamps never substitute for commit identity.
- NUL-delimited rename-aware diff accounting retains every old/new path.
- Test deletion and test-to-source renames fail; staged and unstaged done flips fail.
- Complete JSON and PR-ready Markdown artifacts retain all evidence while default
  rendering remains one screen and routes through Task 238 budgets.
- Boundary events retain the semantic class, process exit, and both artifact paths.

## Passing Local Evidence

- Focused witness/output/capsule matrix: **45 passed**.
- Witness plus generated legacy projection matrix: **56 passed**.
- Installer, distribution, autonomous-delivery, delivery-policy, passive-ledger,
  legacy-projection, output-budget, and witness compatibility matrix:
  **263 passed, 3 opt-in certification/wheel smokes skipped**.
- Network-excluded full repository suite: **1,912 passed, 4 documented opt-in
  certification/wheel smokes skipped**.
- Ruff lint: all scoped Python files passed.
- Ruff format: all scoped Python files passed.
- Live/package `witness_lib.py` byte parity passed.
- `git diff --check` passed at the implementation checkpoint.

## Honest Local Exceptions

These are not counted as passes and must be covered by hosted CI or a compatible
environment:

1. Two editable-package invocation tests create isolated virtual environments and
   attempt to download `setuptools>=68`; this session has restricted network access.
2. The pre-existing governed-target refusal test treats a checkout under `/tmp` as a
   disposable target. This isolated Task 241 worktree therefore returns
   `candidate_already_done` instead of `target_not_isolated_temp`; prior task evidence
   already reserves this location premise for hosted CI.
3. The unrelated local stdio MCP surface smoke completed its preceding invocation
   tests but did not return under the newly reconfigured session and was interrupted
   without changing files. It is not a witness code path.
4. The Task 240 Black executable stalled when reused from another worktree; Ruff's
   formatter and linter passed. Hosted CI remains the Black authority.

## Still Required Before Final Pass

- commit the exact Task 241 implementation head;
- record verification for that exact HEAD;
- dogfood the real `aegis witness` shipping step and measure latency plus default
  stdout lines/bytes;
- run final Taskmaster, plan, audit, guard, strict Aegis, and witness checks;
- publish the exact head and pass hosted CI, including the locally unavailable
  packaging and path-premise checks; and
- preserve rollback and working-tree evidence through closeout.
