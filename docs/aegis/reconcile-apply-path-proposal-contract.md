# Aegis Reconcile Apply-Path Proposal Contract

**Status:** active Task 149 contract.
**Scope:** design and review contract only. This task does not add an apply path, does
not enable mutation, does not enable mutation by another name, and does not make
`aegis reconcile` an execution surface.

## Contract-Only Boundary

Task 149 defines the first possible future reconcile apply path without implementing it.
`aegis reconcile` remains read-only. The following remain forbidden in this task:

- `--apply`
- `--auto`
- `--auto-fix`
- `--fix`
- `--set-status`
- `--status`
- `--done`
- `--closeout`
- `--mutate`
- `--write`
- `--push`

No writer function may consume `mutation_candidate_preview`. No Taskmaster status write,
git write, PR write, closeout shortcut, branch update, workflow-state write, session write,
plan write, or work-tracking write is introduced by this contract.

## Invocation And Confirmation Decision

The missing safety decision after Tasks 145-148 is not another proof of precision or
rollback. It is who can invoke apply and who can confirm it.

Task 149 decides that the first future apply path must be **agent-excluded**:

- The governed agent that produced or consumed a reconcile report cannot invoke apply.
- The governed agent cannot satisfy operator confirmation.
- Apply cannot be exposed as an MCP tool for the governed agent.
- Apply cannot be exposed as `aegis reconcile --apply`.
- Apply cannot be exposed through the normal agent-facing `scripts/codex-task aegis
  reconcile` path.
- Apply must refuse when invoked from a known governed-agent tool context.

The first acceptable invocation channels are:

- **Post-merge CI invocation:** a repository-controlled workflow runs after merge truth is
  already established on the protected branch. This is the preferred first channel because
  the mutation is a convergence action after the merge has happened.
- **Operator-controlled local invocation:** a human operator runs a separate future apply
  entrypoint outside the governed agent runtime. This still requires explicit non-default
  confirmation and the same side-effect, rollback, audit, and kill-switch gates.

Confirmation means an actor outside the governed agent confirms the exact task, proof,
allowed delta, audit destination, and rollback plan. It does not mean the agent types
`y`, runs a shell command, or calls a tool on behalf of the operator.

## First Future Apply Class

The only first future apply class that this contract is allowed to describe is:

- finding kind: `merged_but_not_done`
- proof: `git_ancestor`
- current Taskmaster state: not `done`
- future requested state: `done`
- allowed data source: opt-in Task 148 `mutation_candidate_preview`
- expected operator-visible action: mark the matching Taskmaster task `done`

This is a future proposal boundary, not an implementation. The action remains unavailable
until a separate Taskmaster task proves every precondition below and adds an explicitly
reviewed execution path.

All other classes stay manual-only or contract-excluded:

- `merged_but_not_done` with `github_pr_merged`
- `done_but_not_merged`
- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- `git_only_non_ancestor_or_missing_base`
- any finding absent from the Task 146 labeled corpus
- any finding with unknown, missing, or mixed proof

## Preconditions From Tasks 144-148

A future apply implementation cannot start from this contract alone. It must satisfy all
of the existing gates:

- **Task 144 promotion contract:**
  `docs/aegis/reconcile-promotion-contract.md` remains the source of truth for separating
  read-only reconcile from any mutation task. The future task must be a separate branch and
  cannot smuggle mutation in through existing report-only surfaces.
- **Task 145 side-effect oracle:**
  `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` remains the authority for
  actual changed-path proof. The future apply path must prove the exact allowed delta
  before and after mutation in an isolated fixture.
- **Task 146 precision corpus:**
  `docs/aegis/reconcile-precision-corpus.md` remains the auto/manual boundary authority.
  The future apply path must show zero auto/manual boundary leaks and zero false positives
  for the apply class on the labeled corpus.
- **Task 147 rollback contract:**
  `docs/aegis/reconcile-mutation-rollback-contract.md` remains the rollback and
  blast-radius contract. The future apply path must capture rollback state before any write
  and verify restoration after any failure or requested rollback.
- **Task 148 inert preview contract:**
  `docs/aegis/reconcile-mutation-candidate-preview-contract.md` remains the preview
  contract. Preview output must stay non-executable and must not be consumed by writers
  until a later task explicitly creates and verifies an execution path.

## Future Apply Acceptance Criteria

A separate implementation task may only add an apply path if it satisfies every item in
this section.

### Agent-Excluded Invocation

The future apply path must prove:

- it is a separate entrypoint from read-only reconcile
- it is unavailable from the governed agent's MCP/tool surface
- it refuses known governed-agent invocation contexts
- it can run from the selected operator or post-merge CI channel
- the selected channel is visible in audit breadcrumbs

This is the load-bearing confirmation model. If the agent can call apply and confirm it,
confirmation is not a safety control.

### Operator Confirmation

The operator must explicitly confirm a non-default action after seeing:

- task id
- current Taskmaster status
- proposed Taskmaster status
- finding kind
- proof source
- merge evidence
- allowed changed paths
- rollback handle summary
- audit destination

No default confirmation, implicit confirmation, or agent-only confirmation is acceptable.

For post-merge CI, confirmation is encoded as repository governance: protected-branch
merge plus an explicitly enabled CI job. The job identity and triggering ref must appear in
the audit breadcrumb. For local operator invocation, confirmation is a human action outside
the governed agent runtime and must be recorded before the first write.

### Audit Breadcrumbs

Before any write, the future apply path must write an audit breadcrumb containing:

- phase: `before`
- handler
- task id
- finding kind
- proof source
- current status
- proposed status
- allowed-delta inventory
- timestamp
- requested outcome

After the write or after rollback, it must write an audit breadcrumb containing:

- phase: `after`
- handler
- task id
- proof source
- actual outcome
- changed-path inventory
- rollback status
- timestamp

The before breadcrumb must exist before the first write. If the before breadcrumb cannot
be written, mutation is blocked before any task state changes.

Apply audit breadcrumbs are separate from degraded-event breadcrumbs. They may reuse the
Task 140 hash-chain primitive, but real mutation needs its own observable audit trail with
before, after, outcome, and rollback data.

### Exact Allowed Delta

The first future apply path may only change:

- `.taskmaster/tasks/tasks.json`
- `.taskmaster/tasks/task_<id>.md`

Task 145's side-effect oracle is the authority. The path prediction in Task 148 preview
records is informational and non-authoritative.

The following surfaces must remain unchanged:

- `.aegis/**`
- `docs/ai/work-tracking/**`
- `sessions/**`
- `plans/**`
- `.plan_state/**`
- `.git/HEAD`
- `.git/refs/**`
- `.git/packed-refs`
- GitHub PR state
- local or remote branches
- closeout reports

### Rollback

Before any write, the future apply path must capture the before state for every registered
changed path. Rollback must restore:

- regular file content
- missing paths
- path type
- permissions mode
- symlink targets
- directory membership when applicable

Rollback verification must compare the restored tree against the before snapshot. A
rollback verification failure must leave the apply path in a blocked or error state, not a
success state.

### Kill-Switch

A future apply implementation must include a global kill-switch that disables apply for
every invocation channel. The kill-switch must default to disabled until the implementation
task explicitly proves the enable conditions. Tests must prove the disabled state holds and
that a governed agent cannot bypass it.

### Failure Behavior

Failure at any precondition blocks mutation before writes. Failure after a partial write
must trigger rollback verification. Failure to verify rollback must be auditable and must
not be hidden by a successful reconcile result.

## Required Negative Tests For Any Future Apply Task

The future implementation task must add tests proving:

- reconcile default output remains read-only and observational
- no apply/mutation flags exist until that task intentionally adds them
- `mutation_candidate_preview` is consumed only by the new apply implementation, never by
  unrelated writers
- manual-only classes cannot enter the apply set
- `github_pr_merged` proof is excluded from the first apply class
- operator confirmation is mandatory and non-default
- agent-context invocation is refused
- post-merge CI or operator-channel identity is recorded
- before audit exists before the first write
- apply audit is separate from degraded-event logging
- exact allowed-delta proof uses the Task 145 oracle
- rollback restores registered paths and detects unregistered deltas
- a global kill-switch disables apply across all invocation channels
- out-of-band agent attempts to mutate Taskmaster status remain blocked by the tool gate
- no closeout, git, PR, session, plan, work-tracking, or Aegis state mutation is bundled
  into the Taskmaster status write

## Proposed Next Tasks

- **Task 150:** build a disabled apply orchestration scaffold after this invocation model
  review. The scaffold must wire positive approved-context proof evaluation, an
  apply-audit transaction model, and kill-switch semantics behind an enable gate that is
  intentionally unsatisfiable. The enable gate that is intentionally unsatisfiable remains
  the core disabled-scaffold invariant.
- **Task 151:** enable a narrowly scoped apply path only after the disabled scaffold and
  external review prove the invocation, audit, kill-switch, precision, side-effect, and
  rollback contracts.

## Claude Discussion Prompt

Use this prompt for external design review before implementing any apply path:

```text
We have completed Aegis Tasks 144-149. Task 149 is contract-only: reconcile remains
read-only, there is no --apply flag, and no writer consumes mutation_candidate_preview.
The main Task 149 decision is that future apply must be agent-excluded: operator- or
post-merge-CI-invoked, never invoked or confirmed by the governed agent.

The proposed first future apply class is only:
- finding kind: merged_but_not_done
- proof: git_ancestor
- future effect: mark the matching Taskmaster task done
- allowed delta: .taskmaster/tasks/tasks.json plus .taskmaster/tasks/task_<id>.md

The future implementation would have to satisfy:
- Task 144 promotion contract
- Task 145 side-effect oracle
- Task 146 precision corpus
- Task 147 rollback contract
- Task 148 inert preview contract
- Task 149 apply-path proposal contract

Please critique this as an agent-runtime-first workflow system:
1. Is merged_but_not_done with git_ancestor proof narrow enough for the first apply path?
2. Is the allowed-delta proof complete, or are Taskmaster side effects still under-modeled?
3. Are rollback and audit breadcrumbs enforceable before any write?
4. Is the invocation model strong enough: operator- or post-merge-CI-invoked, never
   governed-agent-invoked?
5. What exact test proves the governed agent cannot invoke or confirm apply?
6. What should the apply-audit breadcrumb contain beyond degraded-event logging?
7. What kill-switch semantics are sufficient for a fleet-wide disable?
8. Could an autonomous agent misread the preview or this contract as permission to mutate now?
9. What exact negative test would you require before any --apply implementation exists?
10. Should Task 150 be a disabled scaffold with an unsatisfiable enable gate, or is another
    invocation review needed first?
```

## Non-Goals

- No `--apply`, `--auto`, `--fix`, `--set-status`, `--done`, `--closeout`, `--mutate`,
  `--write`, or `--push` reconcile flag.
- No Taskmaster mutation.
- No git mutation.
- No GitHub PR mutation.
- No closeout mutation.
- No workflow-state mutation.
- No enabled execution scaffold.
- No default candidate preview.
- No agent-invoked apply path.
