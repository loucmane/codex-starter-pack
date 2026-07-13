# Task 247 — Autonomous Delivery Self-Gating

Task 247 is active on `feat/task-247-autonomous-delivery-self-gating`. It fixes the
PR #264 circular dependency in which the required `evidence-gated delivery` job asks
GitHub for clean mergeability while that same required check is still running.

The binding design is
`docs/ai/work-tracking/active/20260713-task247-autonomous-delivery-self-gating-ACTIVE/designs/self-gating-delivery-contract.md`.
The policy now has a non-authorizing `provisional` result only for
`mergeable=true/state=blocked` after every independent gate passes. The required
evaluator is read-only. A separate executor recollects complete current GitHub evidence
and requires a fresh ordinary `allow` before exact-head squash merge and post-merge
dispatch.

Local verification so far: 48 focused policy/workflow tests pass; Ruff, policy asset
parity, and diff checks pass; the full meta-workflow suite passes 1,210 tests with four
documented opt-in release/MCP smoke skips. Remaining proof is repository-wide validation,
hosted exact-head CI, the attended governance merge, and a real ordinary autonomous
canary with exact-merge-SHA dispatch.

Preserve unrelated `.codex`, `.agents`, and local `.aegis` drift. In particular, do not
stage or modify `.codex/deep-work.config.toml`; its protected SHA-256 is
`eca031a94a46de3908dbebab0a36c466be1696e27887ef6477ab714a188868f0`.
