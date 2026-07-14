# Task 250 Stabilize Evidence-Gated Autonomous Delivery Executor – Handoff Summary

## Current State
- Task 250 is active on `feat/task-250-autonomous-delivery-executor-run-evidence`.
- The initial governance fix merged as `0088fff`; ordinary canary PR #278 remains open, fully green, and intentionally unmerged after trusted run `29320216830` failed closed with `executor-self-check-missing`.
- The source and packaged policy now separate complete candidate check/status evidence from exact current Actions run/job identity, including distinct `pull_request_target` and `workflow_run` head bindings.
- Focused policy/workflow tests pass (`90 passed`), along with Ruff, Actionlint, parity, Taskmaster health, plan sync, work-tracking audit, source guard, diff hygiene, and changed-diff secret scan.
- The full repository suite reached `1990 passed, 4 skipped` with only the documented `/tmp` location assertion; the exact assertion passes from `/home/loucmane/codex`.
- Task 249 is `done`; its complete terminal evidence now matches signed closeout commit `9553859` byte-for-byte inside the Task 250 change set, resolving the double-ACTIVE bootstrap without bypassing the source guard.
- No merge bypass, branch-protection change, token/secret change, or live target-project mutation occurred.

## Next Steps
1. Create the signed remediation commit, push it, and open the attended governance PR.
2. After exact-head review and protected merge, bring PR #278 to a current base/head and retrigger the autonomous path.
3. Require PR #278 to squash-merge without manual merge and require its exact merge SHA to pass post-merge repository dispatch.
4. Only then complete/archive Task 250 and close obsolete canary/closeout branches as superseded without deleting evidence.
