# Task 250 Executor Self-Status Contract

## Incident

Task 249's closeout PR #276 reached signed head
`955385929fc0d96285c741bdfe2c6e5e0b97dea6` against merged Task 249 base
`d7ffce5eff8df92d08def1e4e2b7aeef2860a81d`. Witness, Codex Guard, Meta
Workflow Guard, and both CI matrices were green after one Python 3.11 retry of an
unrelated MCP stdio transport stall. The read-only `evidence-gated delivery` job
then passed, but the write-capable executor twice recollected
`mergeable=true/state=unstable` and correctly refused its fresh `provisional`
decision. Both failures recorded only
`mergeability-self-check-pending`; no merge was attempted.

The old Task 247 model assumed GitHub would remove the executor's own non-required
check from mergeability, or settle to `clean`, during the bounded wait. PR #276
proves that assumption is not invariant. The running `policy-authorized merge`
check, and failed earlier attempts with the same check name, can themselves keep
the pull request `unstable`. Requiring `clean` from inside that check is therefore
circular.

The post-merge canary PR #278 exposed a second provenance shape. Its ordinary
candidate checks were complete and green, but the merge-capable retry was
triggered by `workflow_run`. GitHub anchored that executor run and both of its
jobs to trusted `main` at `0088fff`, not to candidate head `eb7933b`. The old
implementation searched only the candidate-head Checks API and therefore failed
closed with `executor-self-check-missing`, even though run `29320216830` and its
active merge job were available from the trusted Actions run/jobs APIs. A current
`workflow_run` executor can never satisfy a candidate-head self-check lookup.

## Invariants

The remediation does not make `blocked` or `unstable` generally mergeable.

1. The read-only required evaluator remains unchanged: clean evidence returns
   `allow`; otherwise-complete `blocked` or `unstable` evidence returns the
   non-authorizing `provisional` decision.
2. Only the trusted default-branch executor may request executor-phase evaluation.
   It passes GitHub's numeric `run_id`; candidate code and candidate policy are
   never executed.
3. Executor phase fetches two independent complete inventories: latest
   candidate-head checks/status contexts, and the current trusted Actions run
   plus all jobs for its exact numeric run ID.
4. Prior candidate-head checks named `policy-authorized merge` are excluded from
   independent status accounting only when they belong to `github-actions` and
   have a canonical repository Actions run/job URL. Current executor identity is
   never inferred from those checks.
5. The current executor must be the sole active `policy-authorized merge` job in
   the exact trusted run, with matching run ID, attempt, workflow name, workflow
   path, repository/head-repository, canonical job URL, and trigger-specific head:
   `pull_request_target` binds to the candidate; `workflow_run` binds to the
   current trusted default branch.
6. Every non-self check must be completed with `success`, `neutral`, or `skipped`.
   Every latest legacy status context must be `success`. Missing, truncated,
   spoofed, pending, failed, cancelled, stale-head, or malformed evidence fails
   closed.
7. Required workflow runs, exact head, current base, same-repository head,
   task-branch shape, complete file inventory, reviews, labels, attended paths,
   and test-deletion checks remain independently binding.
8. Immediately before merge, the executor recollects PR metadata, workflow runs,
   check runs, status contexts, review threads, and its own run/jobs; it reruns
   trusted policy and requires a second ordinary `allow` decision.
9. The merge request remains a SHA-pinned squash through GitHub's normal protected
   API. There is no admin bypass, force operation, candidate checkout, artifact
   execution, or policy override.

## Executor Decision Table

| Mergeability | Current trusted run/job | Independent candidate checks/statuses | Result |
|---|---|---|---|
| `clean` | present | all green and complete | `allow` |
| `blocked` / `unstable` | present | all green and complete | `allow` with `mergeability_self_check_verified=true` |
| `blocked` / `unstable` | missing, completed, ambiguous, or mismatched | any | `defer` |
| `blocked` / `unstable` | present | pending/failed/incomplete | `defer` |
| `dirty`, `behind`, `unknown`, or `mergeable=false` | any | any | `defer` |
| any | any | attended path/label/fork/test deletion | `attended` |

## Verification

- Preserve PR #264 and PR #269 evaluator replays as `provisional`.
- Add direct-telemetry PR #276 replay: evaluator remains `provisional`; trusted
  executor phase becomes `allow` only with the exact current run/job and complete
  green independent inventories.
- Add direct-telemetry PR #278 replay: the current `workflow_run` executor is
  absent from candidate checks but binds exactly to trusted `main` through its
  own run/jobs APIs.
- Reject self-name spoofing, wrong run IDs, workflow path/event/repository/head
  mismatches, duplicate or completed executor jobs,
  independent pending/failing checks, failed legacy statuses, incomplete
  inventories, attended paths, stale head/base, and review failures.
- Prove the workflow has only `checks: read` in addition to its existing executor
  permissions, fetches complete paginated evidence, runs executor policy twice,
  and reaches the merge endpoint only after the second `allow`.
- Run focused tests, full repository tests, source/package parity, Taskmaster
  health, source guards, strict Aegis verification, hosted checks, and a live
  ordinary canary before retrying PR #276.

## Rollback

Revert the Task 250 squash commit through a reviewed protected pull request. That
restores the Task 247 behavior: safe but potentially deadlocked `provisional`
executor decisions. No branch-protection setting, token, secret, target project,
Taskmaster history, or Aegis ledger migration is required.
