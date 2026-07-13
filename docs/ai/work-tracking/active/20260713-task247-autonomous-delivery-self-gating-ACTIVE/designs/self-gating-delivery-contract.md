# Task 247 Autonomous Delivery Self-Gating Contract

## Incident

PR #264 reached exact head `77b786d2acfbb1b40ee3c39809d8e065f50ed87c`
against current base `8bf1f1871ff259987fa1b8d66d875b1adaf8d99e`. Python 3.11/3.12,
Codex Guard, Meta Workflow Guard, witness, inventory, review-thread, task-branch, and
attended-path checks were green. Both ready-event attempts of run `29234285884` skipped
the merge step. Immediately after each run completed, the same trusted policy and current
GitHub evidence evaluated `allow` with no reasons.

The required branch-protection context is the workflow's own `evidence-gated delivery`
job. While that job evaluates, GitHub reports the otherwise mergeable pull request as
`mergeable=true` and `mergeable_state=blocked`. The current policy treats every non-clean
state as a reason to defer, so the check cannot become green before the decision that
requires it to be green.

## Security Invariant

No intermediate state may authorize a merge. A merge occurs only after a trusted-base
executor recollects current GitHub evidence and receives an ordinary `allow` decision
with `mergeable=true` and `mergeable_state=clean`.

Candidate PR code, actions, artifacts, scripts, and policy bytes are never checked out or
executed. Exact head, current base, complete inventory, required external workflows,
reviews, labels, attended paths, test deletion, same-repository head, and task-branch
checks remain binding.

## Decision Lattice

The deterministic policy has five decisions:

| Decision | Meaning | May merge? |
| --- | --- | --- |
| `allow` | Every gate is current and mergeability is clean. | yes, executor only |
| `provisional` | Every non-mergeability gate passes; GitHub reports `mergeable=true/state=blocked`. | no |
| `defer` | Evidence is incomplete, stale, pending, failed, review-required, conflicting, dirty, or otherwise non-clean. | no |
| `attended` | A protected path/label, fork, policy/governance surface, or other attended category is present. | no |
| `deny` | Evidence is malformed or structurally incomplete. | no |

`provisional` is not an authorization. It exists only to let the required evaluator job
finish successfully so GitHub can clear that job's own protection context. It is returned
only when:

- `mergeable` is exactly `true`;
- `mergeable_state` is exactly `blocked`;
- all policy-required external workflow runs at the exact head are completed successfully;
- head, base, repository, branch, inventory, review threads/decision, labels, paths, and
  deletion checks produce no other reason.

`mergeable=false`, `dirty`, `unknown`, `behind`, or any other state remains `defer`.
`REVIEW_REQUIRED` and `CHANGES_REQUESTED` both remain `defer` unless an attended reason
dominates.

## Two-Job Trusted Workflow

### Required evaluator: `evidence-gated delivery`

- checks out only the default branch into `trusted`;
- has read-only contents/pull-request permissions plus actions read;
- collects current PR, complete file inventory, exact-head external workflow runs, and
  paginated review threads;
- evaluates trusted policy;
- exposes candidate number, expected head, and decision as job outputs;
- never calls the merge endpoint.

### Non-required executor: `policy-authorized merge`

- runs only after evaluator output is `allow` or `provisional`;
- checks out only the current default branch and validates its policy;
- waits a bounded interval for GitHub to recompute mergeability after the evaluator check;
- recollects the complete evidence set rather than trusting evaluator artifacts;
- requires the fresh decision to be exactly `allow`;
- rechecks unchanged head/base immediately before an exact-head squash merge;
- dispatches the exact merge SHA to post-merge CI/guards.

If GitHub remains blocked or any fact changes, the executor fails closed without merging.

## Required Tests

- PR #264 replay: blocked/true plus otherwise complete evidence returns `provisional`.
- Clean equivalent returns `allow`.
- False/dirty, unknown, stale base/head, incomplete inventory, pending/failed workflow,
  review-required/changes-requested, unresolved threads, fork, attended path/label, and
  test deletion never return `allow` or merge.
- Workflow contracts prove the evaluator has no write permission or merge call, executor
  alone has write permission, both use trusted default-branch code, executor recollects
  evidence, and only fresh `allow` reaches an exact-head merge.
- Source and packaged policy bytes remain identical.
- An ordinary canary PR proves evaluator provisional/allow, executor fresh allow, squash
  merge, and exact-merge-SHA post-merge dispatch.

## Rollback

Revert the Task 247 commit through a reviewed PR. This restores the single-job clean-only
policy, causing routine PRs to stop safely at manual protected merge. No branch-protection,
repository setting, data, target installation, ledger, or Taskmaster migration is needed.
