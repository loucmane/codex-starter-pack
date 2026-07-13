# Task 247 Fix Autonomous Delivery Self-Gating Race – Handoff Summary

## Current State
- Task 247 implementation is complete locally on
  `feat/task-247-autonomous-delivery-self-gating` but not yet committed or delivered.
- Focused policy/workflow tests: 48 passed. Full meta-workflow suite: 1,210 passed with
  four documented opt-in release/MCP smoke skips. Full repository suite: 1,907 passed
  with the same four opt-in skips. Changed-file Ruff, source/package parity, policy
  validation, Taskmaster health, capsule, witness, plan sync, audit, guard, and diff
  checks pass.
- The required evaluator is read-only and may emit non-authorizing `provisional`; the
  downstream executor recollects full evidence and merges only on fresh clean `allow`.
- Advisory enforcement and all attended categories remain unchanged.
- Local evidence and the intentional source-checkout strict-verification limitation are
  recorded at `reports/autonomous-delivery-self-gating/task-verification.md`.

## Next Steps
1. Run plan sync, work-tracking audit, source guard, repository-wide tests, and strict
   Aegis/witness verification.
2. Close out Task 247 through supported paths and publish the governance PR with an
   explicit task-only staging allowlist.
3. Obtain the policy-required attended merge for this governance change after exact-head
   hosted CI passes.
4. Open an ordinary routine canary PR and prove autonomous squash plus exact-merge-SHA
   post-merge dispatch before declaring Task 247 complete.
