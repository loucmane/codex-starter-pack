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
