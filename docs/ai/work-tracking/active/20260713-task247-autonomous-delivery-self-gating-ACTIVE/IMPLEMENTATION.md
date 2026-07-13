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
