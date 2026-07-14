# Task 247 Fix Autonomous Delivery Self-Gating Race – Implementation Notes

## Planned Workstreams
- Added a fifth deterministic policy result, `provisional`, for the single
  `mergeable=true/state=blocked` case after every independent policy gate passes.
  `provisional` is explicitly non-authorizing.
- Kept `dirty`, `behind`, `unknown`, conflicts, stale head/base, pending or failed
  workflows, reviews, threads, attended paths/labels, forks, inventory defects, and test
  deletion fail-closed.
- Split `.github/workflows/aegis-autonomous-delivery.yml` into a read-only required
  evaluator and a downstream write-capable executor. The executor recollects all GitHub
  evidence and requires a fresh ordinary `allow` before exact-head squash merge.
- Added a secret-free PR #264 replay fixture plus policy and workflow trust-boundary
  regressions. Source and packaged evaluator assets remain byte-identical.
- Updated the canonical evidence-gated delivery document and the Task 247 design contract
  to describe the five-state lattice, two-job workflow, rollback, and live canary.

## Live-Canary Remediation
- The first unchanged ordinary canary, PR #269, exposed a second GitHub mergeability race:
  all independent gates were green, but trusted run `29270554173` skipped the executor.
- Added a secret-free PR #269 fixture whose `state=unstable` input is explicitly labeled
  as a minimal replay consistent with the live path because the old workflow did not
  retain its ephemeral evaluator result.
- Extended `provisional` to `mergeable=true` with either `blocked` or `unstable` only
  after all independent gates pass. The executor remains incapable of merging anything
  except a freshly recollected ordinary `allow` with clean mergeability.
- Added evaluator reason output to the GitHub step summary so future non-merge decisions
  are inspectable without reconstructing transient API state.

## Review-Pagination Remediation
- Synchronized canary PR #269 with remediation merge `94439ab...` at signed head
  `1f5d949...`; every required workflow passed, but run `29273244399` still skipped the
  executor.
- Recollected the same PR, files, exact-head workflows, and review pages with the trusted
  workflow commands. The policy returned only `review-threads-truncated`.
- Replaced jq's boolean-coalescing `hasNextPage // true` in both evaluator and executor
  with an explicit null test. A real `false` is preserved; absent final-page data remains
  fail-closed as `true`.
- Added a secret-free PR #269 GraphQL page fixture and executable tests that extract and
  run both exact workflow filters, including the no-page fail-closed case.

## Live Acceptance
- PR #271 delivered the trusted collector fix through the attended exact-head path.
- The unchanged ordinary canary was synchronized at signed head `4c0ada5...`; its diff
  remained one evidence document with no labels or review threads.
- Trusted run `29275024874` passed evaluator and executor, then exact-head squash-merged
  PR #269 as `4407c914...` without a manual merge or bypass.
- Repository-dispatch CI, Meta Workflow Guard, and Codex Guard all passed against the
  exact merge SHA, completing the Task 247 acceptance contract.
