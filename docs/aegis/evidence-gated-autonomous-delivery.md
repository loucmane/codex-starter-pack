# Evidence-Gated Autonomous Delivery

## Status

Task 246 introduces the first repository-native Aegis delivery authority contract.
It replaces a hardcoded rule that required owner approval for every merge with a
tracked, deterministic, fail-closed policy.

The bootstrap pull request that introduces this mechanism remains attended. The
mechanism cannot authorize its own installation because both its policy and its
privileged workflow are classified as attended paths by the policy on `main`.

## What This Changes

After the bootstrap is merged, an eligible routine task pull request may be squash-
merged without a new chat approval when all required evidence is current and green.
The authority persists in the repository across agent sessions and context compaction.

The source checkout also carries a Codex permission profile for the local execution
half of that authority. `deep-work` uses `approval_policy = "never"` with the scoped
`aegis-autonomous` profile: the workspace and its Git metadata are writable, while the
built-in `:workspace` protections keep `.codex` and `.agents` read-only. Network access
is allowlisted to GitHub, npm, PyPI, and OpenAI domains. This is not
`danger-full-access`.

The same policy carries explicit routine workflow capabilities. In this repository the
active evidence-gated policy authorizes, after the relevant evidence is surfaced:

- supported Taskmaster task transitions and kickoff;
- deterministic safe repair (never manual-review repair);
- non-dry-run closeout after strict verification and successful dry-run preflight;
- task-scoped commit, push, draft/ready PR transitions;
- CI diagnosis and task-scoped remediation;
- trusted exact-head merge when the delivery evaluator returns `allow`.

Disabling any capability in the policy restores an attended boundary for that operation.

This does not grant unrestricted autonomy. It does not:

- use Codex `danger-full-access` or make `.codex`/`.agents` writable;
- bypass GitHub branch protection;
- permit force-pushes, history rewrites, admin merges, or direct pushes to `main`;
- allow a pull request to execute its own policy, workflow, action, or artifact in a
  privileged context;
- auto-merge authority, workflow, secret, deployment, migration, destructive, or
  otherwise high-risk changes;
- replace Aegis readiness, Taskmaster, S:W:H:E tracking, verification, closeout, or
  delivery witness evidence.

## Codex Execution Boundary

Aegis policy and Codex permissions solve different problems:

- the Codex profile decides what local commands can technically do without prompting;
- Aegis decides whether repository evidence authorizes a workflow transition;
- protected CI decides whether an exact pull-request head is eligible to merge.

Disallowed local operations fail instead of being converted into recurring owner
prompts. The profile deliberately retains the built-in workspace sandbox, exposes Git
metadata only for the primary checkout, and avoids wildcard network access. Linked Git
worktrees whose common Git directory resolves outside their workspace remain a separate
first-class-worktree requirement; this bootstrap does not claim that case is solved.

The shared PreToolUse command guard adds a non-overridable tier-c policy above ordinary
strict/advisory enforcement. It blocks destructive reset/clean/restore/checkout modes,
force or deleting pushes, direct or implicit pushes to the configured default branch,
forced branch deletion, remote replacement, and GitHub branch-protection/ruleset
mutation. Advisory mode still records and allows ordinary workflow-state findings, but
it cannot downgrade these operations to `would_block`. Normal feature-branch commits and
pushes, protected PR merges, `git clean --dry-run`, read-only governance inspection, and
index-only `git restore --staged` remain available.

This command policy is defense in depth, not an OS security boundary. It understands
direct Git/GitHub commands, compound shell commands, environment wrappers, and bounded
shell `-c` nesting; it does not claim to interpret arbitrary programs that themselves
write `.git` or invoke an API. The scoped sandbox, attended authority paths, protected
GitHub branch, and trusted-base delivery workflow remain the authoritative containment
layers. A future broker can make local Git mutation non-bypassable without broadening
this bootstrap.

The profile is loaded at process start. A running Codex session must be restarted once
after the profile changes; compaction and later resumptions do not remove the persisted
authority.

## Authority Source

The source of truth is the tracked file `aegis.delivery-policy.json`, validated by
`schemas/aegis/delivery-policy.schema.json` and evaluated by
`scripts/aegis-delivery-policy`.

The backward-compatible default is attended delivery:

- absent policy: attended;
- invalid policy: attended and fail closed;
- `mode: attended`: attended;
- revoked authority: attended;
- valid, active `mode: evidence-gated`: routine eligible changes may be delivered by
  the trusted workflow.

The `routine` object is also fail closed. Its boolean capabilities are effective only
when the policy is valid, active, and evidence-gated. Attended or revoked mode reports
all routine capabilities disabled even if stale booleans remain in the file.

`aegis status` and `aegis next` surface the active delivery mode. Installed guidance
must never claim that merge is always manual or always autonomous; it follows the
validated repository policy.

## Routine Eligibility

The trusted evaluator returns `allow` only when every condition below is true:

1. The pull request is open, non-draft, same-repository, and targets `main`.
2. Its branch matches the configured Taskmaster task-branch pattern.
3. The head SHA exactly matches the triggering SHA.
4. The pull request base SHA exactly matches the current trusted `main` SHA.
5. GitHub reports the pull request mergeable and clean.
6. The complete changed-file inventory was fetched and its count matches GitHub's
   declared `changed_files` count.
7. Every required workflow has a completed successful pull-request run at that exact
   head SHA.
8. There are no unresolved review threads or active changes-requested decision.
9. No attended label, attended path, or test deletion is present.
10. The policy is valid, active, and evidence-gated.

The required workflows for this repository are:

- `CI`
- `Codex Guard`
- `Meta Workflow Guard`
- `aegis-witness`

The merge method is squash. The merge request includes the expected head SHA and uses
GitHub's normal protected merge API without `--admin` or any bypass.

## Decision Classes

`scripts/aegis-delivery-policy evaluate` emits one of five decisions:

- `allow`: all routine evidence is complete and current; trusted CI may merge.
- `provisional`: every non-mergeability gate is complete and current, but GitHub reports
  `mergeable=true` and `mergeable_state=blocked` while the required evaluator itself is
  still running. This result may complete the required check but never authorizes a
  merge.
- `attended`: the change is valid but requires an owner decision because its category
  can alter authority, security, deployment, destructive behavior, or governance.
- `defer`: evidence is incomplete, pending, stale, conflicted, or not green; do not
  merge and wait for or remediate the evidence.
- `deny`: the evidence or policy is malformed, contradictory, or structurally
  incomplete; fail closed.

An attended decision is not a failed test. It is a deliberate authority boundary.

## Trusted Workflow

`.github/workflows/aegis-autonomous-delivery.yml` runs only from the default-branch
workflow definition. It is triggered after relevant pull-request state changes and
after each required workflow completes.

The workflow separates the required decision from the privileged operation.

The required `evidence-gated delivery` evaluator:

1. Checks out only the current default branch into `trusted/`.
2. Does not persist checkout credentials.
3. Never checks out pull-request code.
4. Never downloads or executes pull-request artifacts, actions, scripts, or generated
   policy output.
5. Resolves exactly one open pull request for the triggering head.
6. Fetches pull-request metadata, paginated files, exact-head workflow runs, and
   paginated review-thread state directly from GitHub.
7. Runs the evaluator from `trusted/scripts/aegis-delivery-policy` against
   `trusted/aegis.delivery-policy.json`.
8. Has read-only permissions and never calls the merge or repository-dispatch endpoint.
9. May emit `provisional` only for the evaluator's own transient required-check blocker.

The downstream `policy-authorized merge` executor:

1. Runs only after an evaluator result of `allow` or `provisional`.
2. Checks out and validates the current trusted default-branch policy independently.
3. Waits a bounded interval for GitHub to recompute mergeability after the required
   evaluator check completes.
4. Re-fetches the complete pull-request, file, exact-head workflow, and review-thread
   evidence set instead of consuming evaluator artifacts.
5. Requires the fresh trusted policy result to be exactly `allow`; `provisional` cannot
   merge.
6. Re-fetches head and base immediately before merge.
7. Calls the normal squash-merge endpoint only for the unchanged exact head and clean
   current base, then dispatches the exact merge SHA to post-merge guards.

The workflow is serialized per repository. GitHub branch protection remains the final
server-side enforcement layer and rejects merges that no longer satisfy protected-
branch requirements.

## Attended Categories

The policy explicitly keeps these categories attended:

- the policy, schema, evaluator, privileged workflow, and their installer/runtime
  integration;
- GitHub workflows, local actions, CODEOWNERS, and workflow permissions;
- Aegis/agent authority entrypoints and protected guards;
- secrets, deployments, production changes, database migrations, destructive changes,
  and security-sensitive labels;
- fork pull requests and non-task branches;
- deleted tests;
- any future path or label added to the attended lists.

The tracked policy is the exact list. Documentation summarizes it but does not override
it.

## Completed Work on `main`

Task 244 made completed workflow state derivable from repository evidence. Task 246
extends that derivation to taskless `main` only when all of these agree:

- a valid delivery policy identifies the current default branch;
- `plans/current` and `sessions/current` are contained repository symlinks;
- both pointers identify the same numeric task;
- Taskmaster says that task is done;
- exactly one completed archive exists for that task.

Feature-branch task IDs remain the first source of identity. Missing policy leaves the
fallback inapplicable. Invalid, revoked, escaped, stale, or contradictory state fails
closed. This makes push-to-main validation work after a completed task is archived
without fabricating an active tracker.

## Revocation And Rollback

Immediate stop, without deleting evidence:

1. Change `authority.status` to `revoked` or `mode` to `attended` in a reviewed pull
   request.
2. Because the policy path is attended, that change cannot self-merge.
3. After the attended policy change merges, Aegis status/guidance returns to per-PR
   approval and the trusted workflow emits `attended` instead of merging.

Emergency server-side stop:

- disable `.github/workflows/aegis-autonomous-delivery.yml` in GitHub Actions; or
- tighten/remove the workflow token's branch-protection merge permission.

Code rollback is a reviewed revert of the bootstrap squash commit. Do not delete audit
records or rewrite history as rollback.

## Verification Contract

Changes to this mechanism must preserve:

- deterministic policy tests for allow, provisional, attended, defer, and deny;
- source/packaged script and schema byte parity;
- workflow contract tests proving trusted-default checkout, a read-only required
  evaluator, write permission isolated to the downstream executor, no pull-request code
  execution, and no direct merge path from `provisional`;
- exact-head and current-base revalidation;
- complete file and review-thread pagination before both evaluator and executor policy
  decisions;
- protected-path self-authorization tests;
- source completed-state tests on both task branches and synchronized `main`;
- installer idempotence and backward-compatible attended behavior when policy is absent.
- Codex profile tests proving no Auto-review dependency, no legacy sandbox overlap, no
  `danger-full-access`, scoped Git writes, and a finite network-domain allowlist.
- adversarial command-guard tests proving tier-c destructive operations remain denied in
  advisory mode while the normal feature-branch delivery path remains available.

No future optimization may weaken these checks merely to make more pull requests merge
automatically. A category becomes routine only through an attended policy change backed
by replay and dogfood evidence.
