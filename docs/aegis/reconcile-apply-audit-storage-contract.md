# Aegis Reconcile Apply Audit Storage Contract

**Status:** active Task 170 contract.
**Closes:** G7: Audit Storage, Retention, And Review Boundary.
**Verdict:** G7 closed; NO-GO remains for any first guarded apply task.
**Scope:** audit/report destination contract, review boundary, and regression evidence
only. This task does not add an apply channel, expose apply, enable mutation, flip a
kill-switch, or mutate Taskmaster status.

## Purpose

Tasks 150 and 153 created an internal audit payload and test-only write apparatus. Task
170 defines where a future approved apply channel must persist those records and how an
operator reviews them. This closes only the storage/review boundary. It intentionally does
not select the approved invocation channel, build the channel, or make the enable
conjunction satisfiable.

Task 170 does not select the approved invocation channel. Task 170 introduced the
machine-readable gate marker at `docs/aegis/reconcile-enablement-gate-status.json`,
recording G7 as closed by this task. Later gate-closing tasks may update that current
marker while preserving the G7 `closed_by_task: 170` evidence.

## Audit Destinations

Future apply audit records are durable artifacts outside mutable Taskmaster data. The
Taskmaster status cascade may change `.taskmaster/tasks/tasks.json`,
`.taskmaster/tasks/task_<id>.md`, and the validated `.taskmaster/state.json` shape only
when a later approved channel is enabled. Audit and review artifacts must be stored
separately from that cascade.

Allowed out-of-Taskmaster report paths are:

- CI channel artifact root: `$RUNNER_TEMP/aegis-apply-audit/<run-id>/<task-id>/<idempotency-key>/`
- operator-controlled local state root:
  `$XDG_STATE_HOME/aegis/reconcile-apply/audit/<repo-id>/<task-id>/<idempotency-key>/`
- isolated test fixture roots under the platform temp directory

No future apply audit may write to `.taskmaster/tasks/**`, `.taskmaster/state.json`,
`.aegis/state/**`, `docs/ai/work-tracking/**`, `sessions/**`, `plans/**`, source files,
workflow-state files, git refs, or generated task files except through the already
validated Taskmaster status cascade and later process-level oracle allow-list.

Each future approved attempt must persist these breadcrumb files in the selected audit
root:

- `channel-confirmation.json`: selected channel identity, task id, finding kind, proof,
  ref/run/operator identity, exact candidate class, audit destination, and idempotency
  key. This file is defined here so Task 171 can bind the selected channel to the audit
  root without inventing a second destination.
- `apply-audit.jsonl`: append-only hash-chained audit records. The first record is
  `phase: before`; later records capture `phase: after` for success, rollback, or
  terminal failure outcomes.
- `rollback-handle.json`: opaque rollback handle reference and before-state hashes for
  every predicted path.
- `terminal-rollback-failure.json`: durable terminal breadcrumb when rollback itself
  fails. It must be un-auto-clearable and checked before any later apply attempt.
- `review-summary.json`: operator-readable index of the artifact bundle, record count,
  chain head, outcome, alert severity, and review decision.

## Persistence Order

The before-audit breadcrumb is load-bearing:

1. evaluate candidate class, approved context, kill switch, authority, toolchain,
   freshness, idempotency, and fresh validation;
2. capture the rollback snapshot and build the before-audit record;
3. persist the before-audit record to the audit root;
4. only after step 3 succeeds may any Taskmaster status write run.

If the before-audit record cannot be written, mutation is blocked before any Taskmaster
status write. This before any Taskmaster status write ordering is the load-bearing G7
invariant. A failed before-audit write may leave a non-mutating idempotency claim in an
isolated state root, but it must not change governed Taskmaster files. Any later channel
task that introduces production idempotency must document operator review of that
non-mutating claim.

After success, rollback, or terminal failure, the corresponding audit record must be
written after the outcome is known. If rollback fails, the terminal breadcrumb and terminal
kill-switch state are the durable stop condition; an operator resolution task owns the
clear procedure.

## Required Audit Binding

Every `reconcile_apply_audit` record must bind these fields:

- `task_id`
- `finding_kind`
- `proof`
- `proof_artifact`
- `approved_context_proof_id`
- `authorization_binding`
- `external_anchor`
- `toolchain_evidence`
- `predicted_delta_paths`
- `actual_delta_paths`
- `allowed_delta_hashes`
- `before_hashes`
- `after_hashes`
- `semantic_validation`
- `rollback_handle_ref`
- `rollback_state`
- `rolled_back`
- `idempotency_key`
- `previous_hash`
- `chain_hash`
- `outcome`

The hash chain must make deletion, reordering, and replacement observable. The
`authorization_binding` and `idempotency_key` must derive from the exact task id, finding
kind, proof, and proof artifact. In other words, they bind the exact task id, finding
kind, proof, and proof artifact. A record that omits any binding field is not valid
enablement evidence.

Binding rule: exact task id, finding kind, proof, and proof artifact; record that omits any binding field is not valid enablement evidence.

## Retention And Review Procedure

Minimum retention is 90 days for success and rollback artifacts. Terminal rollback failure
artifacts must be retained until the operator-resolution record is reviewed and a later
retention task explicitly permits archival. Terminal rollback failure artifacts must be
retained until operator review completes. CI artifact retention may be longer, but it must
not be shorter.

Retention rule: Terminal rollback failure artifacts must be retained until operator review completes.

Review procedure:

1. download the audit artifact bundle from the selected channel run or the
   operator-controlled local state root;
2. verify `review-summary.json` names the same task id, finding kind, proof, context proof
   id, idempotency key, and chain head as `apply-audit.jsonl`;
3. verify the `apply-audit.jsonl` hash chain from the first `before` record to the final
   outcome record;
4. verify `predicted_delta_paths`, `actual_delta_paths`, `semantic_validation`,
   `toolchain_evidence`, and rollback hashes match the Task 172 process-level oracle
   report;
5. verify no out-of-Taskmaster artifact path appears outside the allowed roots in this
   contract;
6. record the operator review decision in the later decision packet; empty operational
   ledgers and cascade smoke are not precision evidence.

## Observability Expectations

Task 170 defines alerting expectations but does not wire alerts. Later channel and
operator-resolution tasks must implement these notifications:

- **apply fired:** informational notification with task id, finding kind, proof,
  context proof id, external anchor, idempotency key, audit artifact URL/path, and chain
  head.
- **rollback executed:** warning notification with task id, rollback reason, actual delta
  paths, rollback handle ref, rolled-back status, audit artifact URL/path, and chain head.
- **terminal rollback failure entered:** high-severity notification with task id,
  terminal breadcrumb path, kill-switch state, rollback error, operator-resolution
  required flag, and explicit statement that auto-clear is forbidden.

Audit storage is not a substitute for alerting. Alert delivery is a later gate, but every
alert must point to the same immutable audit bundle defined here.

## Enforcement Map

| Contract clause | Enforcing evidence |
| --- | --- |
| G7 is the only gate closed by Task 170 | `docs/aegis/reconcile-enablement-gate-status.json`; `tests/meta_workflow_guard/test_aegis_reconcile_apply_audit_storage_contract.py` |
| Before-audit failure blocks mutation before a Taskmaster write | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_before_audit_write_failure_blocks_taskmaster_status_write` |
| Audit records bind task/proof/context/toolchain/delta/rollback/idempotency/hash fields | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_audit_record_requires_transaction_fields_and_binding` |
| Default config remains zero-delta | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_default_config_full_apply_path_has_zero_live_delta` |
| Apply runtime remains agent-unreachable | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_apply_write_apparatus_is_not_reachable_from_agent_surfaces` |

## Remaining Open Gates

Task 170 closed G7 only. Later tasks closed G1, G2, G3, and G4. These gates remain open
and block any first guarded apply task:

- G5: Enablement Evidence Decision Packet
- G6: Terminal Rollback Failure Operator Resolution
- G8: Final Agent-Surface Regression With The Selected Channel Present

## Non-Goals

- No apply or apply-like command.
- No approved invocation channel.
- No production approved context.
- No operator-local invocation.
- No post-merge apply workflow.
- No MCP apply tool.
- No kill-switch flip.
- No agent-reachable enablement path.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
- No claim that the current write apparatus is ready for production enablement.
