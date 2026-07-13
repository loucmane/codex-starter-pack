# Decisions

- 2026-07-13 — Split required evaluation from merge execution. A provisional blocked
  result may complete the required check but never authorizes merge; only fresh trusted
  `allow` in the second job can call the exact-head merge endpoint.
- 2026-07-13 — Preserve branch protection and all attended categories. Do not solve the
  self-gating cycle by removing the delivery check, accepting dirty/conflicting states,
  or relying on GitHub merge rejection as the primary policy control.
- 2026-07-13 — Keep write permissions out of the required evaluator job. Grant
  `contents:write` and `pull-requests:write` only to the executor that independently
  recollects evidence and receives a fresh `allow`.
- 2026-07-13 — Require a real ordinary canary after the attended governance PR merges;
  deterministic replay and hosted CI are necessary but do not prove GitHub's live
  mergeability transition or exact-merge-SHA dispatch.
- 2026-07-13 — Treat `mergeable=true/state=unstable` as provisional only after every
  independent gate passes. Preserve `dirty`, `behind`, `unknown`, `mergeable=false`, and
  every failed/pending/review/attended condition as non-merging.
- 2026-07-13 — Keep fresh clean `allow` as the sole executor authorization and expose the
  evaluator's reason list in the GitHub job summary. Never use the PR #269 inference as
  evidence that a merge occurred; the same unchanged canary must prove the remediation
  live after the attended policy PR merges.
- 2026-07-13 — Preserve GraphQL `hasNextPage=false` with an explicit null test in both
  trusted collectors. Missing final-page data remains fail-closed as truncated; do not
  replace the check with a permissive default or skip review-thread evidence.
- 2026-07-13 — Test the exact jq filter extracted from the workflow, not a Python
  reimplementation. This binds the regression to the privileged bytes that execute in
  GitHub Actions.
