# Task 246 Evidence-Gated Autonomy Contract

## Problem Evidence

PR #261 merged Task 245 at reviewed head `af253b287d2052c0fd4b83b350d514b12eb89056` as
`89d3e7b72b317a334f59b0ada8c7af37fe578194`. Every PR check passed. The protected-main
push then failed both guard workflows at `python3 scripts/codex-task plan sync` with:

```text
error: No ACTIVE work-tracking folder found under docs/ai/work-tracking/active/.
```

Python 3.11 and 3.12 each also failed one guard integration test because the same state
resolution error occurred before placeholder-handler validation. Task 244's contract explains
the discrepancy: completed-source derivation requires a task-bearing branch. PR checks expose
`GITHUB_HEAD_REF=feat/task-245-*`; protected-main push checks expose `main`.

A separate usability defect compounds the problem. Aegis delivery guidance hardcodes explicit
per-PR owner approval even when exact-head CI, witness, scope, review, and mergeability evidence
already agree. The owner has explicitly authorized replacing that ceremony with persistent
evidence-gated delivery.

## Authority Layers

1. Codex command execution remains workspace-sandboxed and uses its configured auto-reviewer.
2. Aegis determines workflow state and explains whether project delivery policy is attended or
   evidence-gated.
3. GitHub is the merge authority. A privileged workflow evaluates only trusted base-branch policy
   code and exact-head API evidence.
4. Taskmaster remains task-status authority. Plans, sessions, trackers, handoffs, and S:W:H:E
   remain complementary human context and evidence.

No model, subagent, candidate branch, or generated summary may self-authorize a merge.

## Taskless Default-Branch Derivation

Feature branches keep Task 244's branch-ID path unchanged. A branch without a task ID may use the
new path only when all facts below hold:

1. The checkout is positively identified as the uninstalled Aegis source repository.
2. No installed manifest, current-work state, or ACTIVE work-tracking folder exists.
3. The active delivery policy is valid and names the current branch as its default branch.
4. `plans/current` is a contained symlink to one regular plan under `plans/` whose front matter
   contains exactly one numeric task ID.
5. `sessions/current` is a contained symlink to one regular session under `sessions/`; its path and
   text reference the same task ID.
6. Taskmaster contains that task with status `done`.
7. Exactly one contained, non-symlink direct archive child ending in `-COMPLETED` carries the task
   identity.
8. Its regular `TRACKER.md` references the task and declares `**Status**: COMPLETED`.

Missing policy leaves this fallback inapplicable. Once the fallback is applicable, missing,
ambiguous, stale, escaped, or contradictory evidence raises a fail-closed error.

## Delivery Policy

`aegis.delivery-policy.json` is project-owned, tracked, schema-versioned policy. Absence or invalid
content means `attended`. The source repository opts into `evidence-gated` with:

- repository identity and default branch;
- task-branch pattern;
- squash merge and exact-head requirements;
- required trusted workflow names;
- complete file inventory, current base, clean mergeability, and no unresolved review threads;
- attended labels and path patterns;
- owner authority metadata and revocation conditions.

The policy itself, its schema, evaluator, privileged workflow, guard/authority controls, and any
future policy mutation are attended categories. A candidate PR that adds, changes, renames, or
deletes one of those paths cannot become eligible under the prior trusted policy.

## Privileged Workflow

The autonomous-delivery workflow:

1. triggers after relevant PR workflow completion and safe `pull_request_target` state changes;
2. checks out only the protected default branch with persisted credentials disabled;
3. resolves exactly one same-repository, non-draft PR targeting the unchanged current default;
4. fetches a complete changed-file inventory, exact-head workflow runs, labels, mergeability, and
   bounded review-thread metadata through GitHub APIs;
5. evaluates that JSON with the trusted base-branch policy engine;
6. returns without merge for attended or incomplete evidence;
7. fails closed for malformed or contradictory evidence;
8. squash-merges with expected-head matching only when the decision is `allow`;
9. never uses `--admin`, force, candidate code, candidate artifacts, repository secrets, or
   untrusted forks.

Protected-main validation remains mandatory. A failed post-merge run is authority to create a
narrow remediation task and PR under the standing grant, not evidence that the merge succeeded.

## Eligible Routine Operations

- supported Taskmaster and workflow projections;
- deterministic handoff normalization and final closeout when previews are clean;
- task-scoped source, tests, documentation, and dependency work within recorded scope;
- commits, pushes, draft PRs, ready transitions, CI remediation, and protected squash merge;
- post-merge synchronization and remediation.

## Attended Categories

- delivery policy, privileged workflow, branch protection, guard, witness, or authority changes;
- secrets, credentials, authentication, signing, or workflow-permission changes;
- destructive operations, history rewriting, force/admin bypass, or unknown-work deletion;
- production deployment/data mutation and irreversible migrations;
- billing, legal, privacy, or materially ambiguous product decisions;
- enforcement-mode or legacy-retirement policy changes outside explicit task scope.

## Persistence And Audit

The trusted policy is durable across compaction, restart, and agent changes because it is tracked on
protected `main`. Aegis status/next exposes `policy_id`, mode, validity, and confirmation requirement.
Delivery decisions record the policy ID, exact head, evidence summary, decision, and reasons. The
policy expires only through explicit revocation, repository-identity change, or a later attended
policy amendment.

## Backward Compatibility

- No policy file means attended behavior exactly as before.
- Installed-target enforcement remains unchanged and advisory where already configured.
- Source-only pointer derivation never runs in installed targets.
- Existing feature-branch source derivation remains unchanged.
- Existing legacy evidence surfaces remain preserved.

## Rollback

Before merge, close the bootstrap PR. After merge, use a reviewed revert PR to remove the privileged
workflow and source opt-in policy, restore hardcoded attended guidance, and return taskless-main
derivation to branch-ID-only behavior. Do not delete completed archives or legacy evidence during
rollback.
