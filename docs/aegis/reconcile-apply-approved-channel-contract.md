# Aegis Reconcile Apply Approved Channel Contract

**Status:** active Task 171 contract.
**Closes:** G1: Approved Invocation And Confirmation Channel.
**Verdict:** G1 closed; NO-GO remains for any first guarded apply task.
**Selected first channel:** post-merge GitHub Actions on `refs/heads/main`.
**Scope:** confirmation proof model, replay/idempotency contract, and audit binding only.
This task does not add a post-merge apply workflow, expose apply, enable mutation, flip a
kill-switch, or mutate Taskmaster status.

## Purpose

Task 170 defined where future apply audit records live. Task 171 selects the first future
approved invocation channel and defines the proof that the channel must present before any
future apply can even be considered. At the Task 171 boundary this closed G1 only and
left G2, G3, G4, G5, G6, and G8 open.

Task 172 later closed G4 with the selected-channel process-level oracle. Task 173 later
closed G2/G3 with the agent-excluded kill-switch control plane. Task 174 later closed G6
with terminal rollback operator resolution. Task 175 later closed G8 with the final
agent-surface regression. G5 remains open.

The selected first channel is **post-merge CI**:

- provider: GitHub Actions;
- event: `push`;
- ref: `refs/heads/main`;
- operator identity: repository governance for the protected main branch, recorded as
  `github_actions_protected_main`;
- candidate class: `merged_but_not_done/git_ancestor`;
- audit destination: the Task 170 `$RUNNER_TEMP/aegis-apply-audit/...` destination.

`operator_controlled_local` remains a recognized future context family in the scaffold,
but it is not the selected first channel.

## Confirmation Proof Shape

The selected channel confirmation is a data artifact, not an apply entrypoint. Task 172
later added the process-level oracle wrapper that any selected-channel attempt must use,
but the enable conjunction remains unsatisfiable. The confirmation must bind the exact
candidate and run identity:

- `context_type: post_merge_ci`
- `selected_channel: post_merge_ci`
- `proof_id`
- `task_id`
- `finding_kind`
- `proof`
- `candidate_class`
- `proof_artifact`
- `idempotency_key`
- `audit_destination`
- `operator_identity: github_actions_protected_main`
- `external_anchor`
- `expires_at`
- `agent_originated: false`
- `ci.provider`
- `ci.run_id`
- `ci.run_attempt`
- `ci.workflow`
- `ci.repository`
- `ci.sha`
- `ci.event_name`
- `ci.ref`
- `ci.ref_name`

The `idempotency_key` must derive from the task id, finding kind, proof, and proof
artifact. The `audit_destination` must include the Task 170 audit root, the task id, and
the idempotency key. The `external_anchor` and `proof_id` must identify the same GitHub
Actions run attempt.

Idempotency derivation rule: must derive from the task id, finding kind, proof, and proof artifact.

Audit destination rule: must include the Task 170 audit root, the task id, and the idempotency key.

## Refusal Matrix

The selected channel proof fails closed for:

- missing confirmation;
- malformed confirmation;
- stale confirmation;
- PR-shaped confirmation;
- wrong ref;
- wrong task;
- wrong proof;
- wrong finding kind;
- wrong candidate class;
- wrong operator identity;
- missing or empty proof artifact;
- idempotency mismatch;
- replayed idempotency key;
- audit destination mismatch;
- missing run identity;
- governed-agent-originated confirmation.

Even a structurally valid proof returns `enable_gate_unsatisfiable` until a later task
explicitly makes the enable conjunction satisfiable through an approved non-agent
mechanism.

## Replay And Concurrency

The selected channel's concurrency key is the idempotency key. A future channel must claim
that key atomically before any live write. Two approved invocations of the same candidate
must not both fire: the first successful claim may proceed to later gates, and every later
attempt with the same key must refuse as replayed or already claimed.

Concurrency rule: Two approved invocations of the same candidate must not both fire.

Atomic claim rule: claim that key atomically before any live write.

Task 171 does not create the production claim store. It pins the contract and the proof
model. Existing isolated runtime tests still prove file-backed idempotency is atomic; a
later selected-channel task must bind that claim to the production audit destination
before any live write.

## Audit Binding

The selected channel identity is recorded through the Task 170 audit boundary:

- `channel-confirmation.json` stores the full selected-channel confirmation artifact;
- `apply-audit.jsonl` records the selected channel identity, proof id, external anchor,
  audit destination, task id, finding kind, proof, and idempotency key;
- the before-audit record must still be durable before any Taskmaster status write;
- the audit destination remains outside mutable Taskmaster files.

## Current Implementation Boundary

The scaffold now exposes helpers for building and evaluating the selected proof shape:

- `build_post_merge_ci_apply_confirmation`
- `evaluate_selected_apply_channel_confirmation`

These helpers are internal data validators. They are not imported by package CLI, MCP,
`scripts/codex-task`, repair/start/kickoff flows, hooks, preview consumers, or report
consumers. They do not call `run_reconcile_apply_write_apparatus`, do not call
Taskmaster, do not write git state, and do not write Taskmaster status.

## Enforcement Map

| Contract clause | Enforcing evidence |
| --- | --- |
| G1 is closed and NO-GO remains | `docs/aegis/reconcile-enablement-gate-status.json`; `tests/meta_workflow_guard/test_aegis_reconcile_apply_approved_channel_contract.py` |
| Valid selected channel proof remains unsatisfiable by default | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_selected_post_merge_ci_confirmation_is_bound_but_unsatisfiable_by_default` |
| Malformed, stale, PR-shaped, wrong-ref/task/proof, replayed, and agent-originated confirmations refuse | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_selected_post_merge_ci_confirmation_rejects_forged_shapes`; `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_selected_post_merge_ci_confirmation_replay_refuses_by_idempotency_key` |
| Channel identity binds into audit records | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_audit_record_requires_transaction_fields_and_binding` |
| No governed-agent surface reaches the selected channel helpers | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_scaffold_is_not_reachable_from_agent_surfaces` |

## Remaining Open Gates

Task 171 closed G1. Task 172 later closed G4. Task 173 later closed G2/G3. Task 174 later
closed G6. Task 175 later closed G8. This gate remains open and blocks any first guarded
apply task:

- G5: Enablement Evidence Decision Packet

## Non-Goals

- No apply or apply-like command.
- No post-merge apply workflow.
- No operator-local apply command.
- No production approved context that can mutate.
- No kill-switch flip.
- No MCP apply tool.
- No package CLI apply flag.
- No `scripts/codex-task` apply route.
- No agent-reachable enablement path.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
