# Task 247 Verification — Autonomous Delivery Self-Gating

Date: 2026-07-13
Branch: `feat/task-247-autonomous-delivery-self-gating`
Base: `origin/main` at `c9c496487215df100f532c822b12480185d36949`

## Behavioral Evidence

- The real policy CLI evaluates the secret-free PR #264 fixture as `provisional` with
  exactly one reason: `mergeability-self-check-pending` for
  `mergeable=true/state=blocked`.
- The result records `mergeability_recheck_required=true`; it is not an authorization.
- The required evaluator has read-only `actions`, `contents`, and `pull-requests`
  permissions and contains no merge or repository-dispatch call.
- The downstream executor alone has write permissions. It recollects current PR, complete
  file inventory, exact-head workflow, and paginated review evidence, then requires a
  fresh result of exactly `allow` before rechecking head/base/open/draft/clean state and
  calling the exact-head squash endpoint.
- Policy regressions prove dirty/conflicting/behind/unknown states, stale head/base,
  incomplete inventory, pending/failed workflows, review-required/changes-requested,
  unresolved threads, forks, attended paths/labels, and test deletion never obtain an
  autonomous merge path.
- The fixture contains no authorization, cookie, password, home path, prompt, transcript,
  or mutable external-state payload. Its head/base and 21-file inventory are internally
  consistent.

## Local Checks

| Check | Result |
| --- | --- |
| Focused policy + workflow contracts | PASS — 48 passed |
| Full meta-workflow suite | PASS — 1,210 passed, 4 documented opt-in release/MCP smoke skips |
| Full repository suite (`-n auto --dist loadgroup`) | PASS — 1,907 passed, 4 documented opt-in release/MCP smoke skips |
| Changed-file Ruff | PASS |
| Source/package policy byte parity | PASS |
| Policy schema validation | PASS — `aegis-source-evidence-gated-v1` |
| Plan sync | PASS |
| Work-tracking audit | PASS — no issues |
| S:W:H:E guard with untracked scope | PASS |
| Taskmaster full-graph health | PASS — 246 tasks, 383 subtasks, 431 dependency refs, 0 invalid |
| Capsule budget/canary check | PASS |
| CI-mode delivery witness | PASS — scope, diff accounting, done-flip containment, delegated CI |
| `git diff --check` | PASS |

Repository-wide Ruff reports 83 pre-existing findings in legacy template-scanner,
template-governance, and unrelated test files. No Task 247 changed Python file appears in
that baseline; task-scoped Ruff passes. This task does not broaden into unrelated lint
cleanup.

Strict installed-target verification is not applicable to this source checkout. The
source repository intentionally has no installed `.aegis/foundation-manifest.json` or
`.aegis/bin/aegis`; `.venv/bin/aegis verify --strict --target-dir .` therefore fails the
single `aegis.manifest` gate and recommends installation. No manifest or installed state
was fabricated. Source policy, tests, guard, Taskmaster, witness, and hosted CI are the
authoritative gates here.

## Integrity

- Workflow SHA-256:
  `21798141b737d84981b5b57397df2ed012c2835c3a66054bee3d36c127087812`
- Source and packaged policy SHA-256:
  `1facb5b80b8b20342eab4d4f8445c91caa5169185d5efd6fbb0a56f4a84939c0`
- PR #264 fixture SHA-256:
  `7a9abd72f1420bda0ef1e15e2ec7e9d50f2c8448fda7d76cc0daeb947710b253`
- Protected unrelated `.codex/deep-work.config.toml` SHA-256 remains:
  `eca031a94a46de3908dbebab0a36c466be1696e27887ef6477ab714a188868f0`

## Remaining Proof

1. Publish the attended governance PR at an exact signed head and pass hosted checks.
2. Merge through the normal protected attended path without admin bypass or force.
3. Open an ordinary routine canary from the merged default branch.
4. Prove the required evaluator completes, the executor obtains a fresh clean `allow`,
   GitHub performs the exact-head squash, and post-merge guards run at the exact merge SHA.

Task 247 is not complete until those hosted and live-canary items pass.

## Hosted Delivery and Live Canary Attempt 1

- The attended governance PR #265 merged normally at reviewed head
  `a21f9719b603fbb3c2b5c3bc54a6f8e094cbad4b` as
  `f65bf35b11f4d38dc8a0d72edad5c8b4ba2ca763`. Local `main` synchronized exactly and
  its post-merge CI passed.
- Ordinary canary PR #269 remains unchanged at exact signed head
  `2f01675029765e6e99a6a784ce9d397f1388dcdf`, with one task-evidence file, no labels,
  no reviews or unresolved threads, current base
  `f65bf35b11f4d38dc8a0d72edad5c8b4ba2ca763`, and all four required
  pull-request workflows successful.
- Trusted `workflow_run` `29270554173` completed evaluator job `86886878595`
  successfully but skipped executor job `86886920814`. PR #269 remained open and
  immediately reported `MERGEABLE/CLEAN` afterward.
- The old job summary omitted both decision and reasons from retrievable API output.
  Therefore the new `state=unstable` fixture is a minimal replay consistent with this
  path; it is not direct evidence of the transient evaluator payload. This limitation is
  encoded in the fixture's provenance field and in the Task 247 findings.
- The remediation permits `blocked` or `unstable` to become only `provisional` after
  every independent gate is clear. It does not authorize a merge. A fresh executor
  recollection must still produce exact-head/current-base `allow` with clean
  mergeability.
- Current primary-checkout protected drift SHA-256 is
  `f5c579c39b7655ca3078e484ffdce007229618f44a08d7a28b63c65dc96a6708`; the isolated
  remediation has not staged, overwritten, or reverted it.

Task 247 remains incomplete until the remediation merges and the same unchanged PR #269
autonomously squash-merges with successful exact-merge-SHA post-merge dispatch.

## Remediation Local Verification

| Check | Result |
| --- | --- |
| Focused policy + privileged-workflow contracts | PASS — 55 passed |
| Full repository suite in isolated worktree | PASS — 1,912 passed, 4 documented opt-in smoke skips, with one location-sensitive assertion deselected as described below |
| Location-sensitive reconcile assertion | PASS when run with a temp root outside the `/tmp` Git worktree |
| Changed-file Ruff | PASS |
| Source/package policy byte parity | PASS |
| Policy schema validation | PASS — `aegis-source-evidence-gated-v1` |
| Plan sync, work-tracking audit, Taskmaster health, S:W:H:E guard | PASS |
| `git diff --check` | PASS |

The isolated remediation worktree itself is under `/tmp`. One unrelated reconcile test
uses `tempfile.gettempdir()` as the security boundary and therefore classifies the
worktree's repository root as a permitted test target, observing
`candidate_already_done` instead of the expected pre-validation
`target_not_isolated_temp`. The exact test passes when its process temp root is moved
outside the `/tmp` worktree. The complete suite passes with only that environmental
assertion deselected; hosted CI must run it unmodified from GitHub's normal non-`/tmp`
checkout before merge.

Remediation integrity:

- Workflow SHA-256:
  `aaeb4c38fd0ea8eb21e867a4f6b17ff492e3474114f797b857c3a0ae3c961132`
- Source and packaged policy SHA-256:
  `44d3518e8df81f9f1e2b4421cb49dff9905ba3aeaa316f713c8dd1955f773005`
- PR #269 replay fixture SHA-256:
  `c7f43dbe2a08fe16d53b471c56e204d6c42fffc1d2e6ff0e157eb50824e32574`

## Hosted Delivery and Live Canary Attempt 2

- PR #270 merged the first canary remediation normally at exact reviewed head
  `d0d1c3f1d361635c2675d407fefcac80a707243d` as
  `94439ab2c74085c3968b12ac1a60473eb3664d14`; the full hosted Python 3.11/3.12 matrix,
  guards, witness, and attended evaluator passed.
- Because PR #269's previous base SHA was no longer current, `main` was merged into its
  branch without rebasing or force-pushing. The signed head became
  `1f5d9492d0dfeb0197656982137337ca27aa441a`, while the pull-request diff remained the
  same single canary evidence file.
- All four required workflows passed at that exact head: CI run `29272753114`, Codex
  Guard `29272753089`, Meta Workflow Guard `29272753086`, and witness `29272753090`.
- Trusted post-CI run `29273244399` completed evaluator job `86895876331` but skipped
  executor job `86895930119`; PR #269 remained open and clean.
- Recollection with the workflow's exact GitHub commands and current trusted policy
  returned `defer` with one reason: `review-threads-truncated`. The raw GraphQL page had
  zero threads and `hasNextPage=false`.
- The collector expression `hasNextPage // true` was the deterministic cause because jq
  coalesces boolean `false` as well as null. Both trusted collectors now use an explicit
  null test. The exact embedded filters are executed against the captured page, and an
  empty-input regression proves missing page data still fails closed.

Task 247 remains incomplete until the review-pagination remediation merges and PR #269
autonomously squash-merges with successful exact-merge-SHA post-merge dispatch.

### Review-Pagination Remediation Local Verification

- Focused delivery-policy and privileged-workflow contracts: PASS — 57 passed.
- Full repository suite in the isolated worktree: PASS — 1,915 passed and four
  documented opt-in smoke skips, with the same unrelated `/tmp`-location assertion
  deselected; that exact assertion passed separately with a non-overlapping temp root.
- The corrected exact workflow aggregation applied to current PR #269 GitHub evidence
  returns `allow` with no reasons at head
  `1f5d9492d0dfeb0197656982137337ca27aa441a` and base
  `94439ab2c74085c3968b12ac1a60473eb3664d14`.
- Complete-page fixture result: zero unresolved threads,
  `threads_truncated=false`, empty review decision.
- Missing-page fixture result: zero unresolved threads,
  `threads_truncated=true`, empty review decision.
- Ruff, plan sync, work-tracking audit, Taskmaster health, S:W:H:E guard, CI-mode
  witness, and diff checks passed.
- Workflow SHA-256:
  `69f0e59c5fcf0b294d0ae1e7929dd2a7eb18798d8af9467918c45f5730f44231`
- PR #269 review-page fixture SHA-256:
  `0fbf050ca1dc7c3d04f946d97f10f0955f3b7160e0e83ee8e307479c4fccc624`

## Terminal Hosted Acceptance

- Attended remediation PR #271 merged at exact signed head
  `284859b4ba7a88eee803c06c1ddb3c29f19d88a5` as
  `195d5a94d7e06bc10ff6f07c21c1a68fd1a3c2c4`. Both Python matrices, witness,
  Codex Guard, Meta Workflow Guard, and the attended delivery evaluator passed.
- Ordinary one-file PR #269 was synchronized without rewriting history at signed head
  `4c0ada5a6816daddf30d22e0662ab852b9a02de7`; its base was current, inventory complete,
  labels/reviews/threads empty, and all seven required checks successful.
- Trusted workflow-run `29275024874` passed evaluator job `86901864517`, recollected all
  evidence in executor job `86901903350`, obtained a fresh `allow`, and autonomously
  squash-merged the exact head as `4407c9141e350ad113baebce3792a805bf380216`.
- The merge emitted three repository-dispatch runs bound to the exact merge SHA:
  CI `29275056303`, Meta Workflow Guard `29275056589`, and Codex Guard `29275056833`.
  Both CI matrices and both guard workflows passed.
- No admin bypass, force operation, manual canary merge, policy override, or unrelated
  primary-checkout drift mutation occurred. Task 247's live acceptance is complete.
