# Task 247 Fix Autonomous Delivery Self-Gating Race – Handoff Summary

## Current State
- The original Task 247 governance change merged through PR #265 as
  `f65bf35b11f4d38dc8a0d72edad5c8b4ba2ca763` after exact-head hosted verification.
- Ordinary canary PR #269 remains open at
  `2f01675029765e6e99a6a784ce9d397f1388dcdf`: every required workflow is green and the
  pull request is currently clean, but trusted run `29270554173` skipped the executor.
- A bounded remediation is in progress on
  `feat/task-247-autonomous-delivery-canary-remediation`: allow `unstable` to complete
  only as non-authorizing `provisional`, retain fresh clean `allow` as the sole merge
  authority, and expose evaluator reasons in the job summary.
- Remediation policy/workflow tests: 55 passed. The repository suite passed 1,912 tests
  with four documented opt-in release/MCP smoke skips and one unrelated `/tmp`-location
  assertion deselected; that exact assertion passes with a non-overlapping process temp
  root. Changed-file Ruff, source/package parity, policy validation, Taskmaster health,
  plan sync, audit, guard, and diff checks pass. Hosted CI must run the complete suite
  unmodified from its normal checkout.
- The required evaluator is read-only and may emit non-authorizing `provisional`; the
  downstream executor recollects full evidence and merges only on fresh clean `allow`.
- Advisory enforcement and all attended categories remain unchanged.
- Local evidence and the intentional source-checkout strict-verification limitation are
  recorded at `reports/autonomous-delivery-self-gating/task-verification.md`.

## Next Steps
1. Complete local plan sync, work-tracking audit, source guard, focused/full tests, and
   policy/workflow parity for the remediation.
2. Publish and merge the attended remediation through the normal exact-head protected
   path.
3. Re-trigger the unchanged PR #269 checks and prove autonomous squash plus
   exact-merge-SHA post-merge dispatch.
4. Only then mark Taskmaster Task 247 done, close out through supported source paths, and
   merge its terminal evidence.
