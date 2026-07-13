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
