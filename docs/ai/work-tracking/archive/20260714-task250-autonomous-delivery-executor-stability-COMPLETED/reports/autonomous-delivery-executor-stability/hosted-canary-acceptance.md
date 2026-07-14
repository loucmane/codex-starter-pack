# Task 250 Hosted Canary Acceptance

## Attended remediation merge

- PR #279 exact reviewed head: `6d6792454bf67739ecdc5da88d4c0071661277d4`.
- Protected squash merge: `89ea3a4538e659992b5685b3cc3b3b8116a76c39`.
- Reviewed and merged tree: `3f721e941ef985a1159f373c0d6c7507bd22b7a1`.
- Source/package delivery-policy SHA-256:
  `7500445c5906de20561850210f7884d8607f76fef3371536bbfa0a8e139977bc`.
- Local/remote workflow SHA-256:
  `a0f5ab430fd3caf20f744227a8e41f02d9fa7401803501302d63f53ada7315b3`.
- All required hosted checks passed; there were no reviews, labels, or unresolved threads.
- Merge used the normal protected exact-head path without admin bypass or force operations.

## Autonomous canary

- PR #278 was updated by a signed, non-rewriting merge from current `main`.
- Exact candidate head: `2a0343558bbc39c979255d30b6baddba250d09b7`.
- Candidate diff: only `AUTONOMOUS_DELIVERY_CANARY.md`.
- Candidate CI run `29322819048` passed Python 3.11 and 3.12.
- Witness and source guards passed on the exact candidate head.
- Trusted `workflow_run` executor run `29323250166` recollected exact-head evidence,
  established a fresh allow decision, and completed `policy-authorized merge` successfully.
- The policy—not an attended/manual merge—squash-merged PR #278 as
  `c3daa484932292bc25f0f58d51fb96e63c0200f4`.
- Reviewed and merged tree: `eadb1144f6dd2ccf6694a72be1e96eaa9d3e9afa`.

## Exact-merge-SHA dispatch

Every post-merge workflow below was triggered through `repository_dispatch`, checked out
exact merge SHA `c3daa484932292bc25f0f58d51fb96e63c0200f4`, and passed:

| Workflow | Run | Result |
|---|---:|---|
| CI | `29323282631` | Python 3.11 passed in 5m45s; Python 3.12 passed in 7m02s |
| Codex Guard | `29323282767` | passed |
| Meta Workflow Guard | `29323283044` | passed |

This proves the current executor can distinguish complete candidate evidence from its own
trusted run/job evidence, produce a fresh allow decision, merge the SHA-pinned ordinary
canary, and verify the resulting merge commit independently.

## PR #276 supersession reconciliation

PR #276 contains Task 249 terminal closeout state that became stale after Task 250 was made
the sole active authority. Eleven durable Task 249 files already match signed commit
`955385929fc0d96285c741bdfe2c6e5e0b97dea6` byte-for-byte on `main`. This closeout restores
the twelfth durable file, archived `task-verification.md`, from that same signed commit.

The PR's global `tasks.json`, `sessions/current`, and `sessions/state.json` projections must
not be merged because they would rewind current Task 250 authority. Its deleted ACTIVE
tracker is already absent as intended. Once this closeout branch contains the missing report,
PR #276 can be closed as superseded with all durable Task 249 evidence preserved.
