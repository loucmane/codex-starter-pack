# Reconcile Terminal Rollback Resolution Contract

**Status:** active Task 174 contract.
**Closes:** G6: Terminal Rollback Failure Operator Resolution.
**Verdict:** G6 closed; NO-GO remains for any first guarded apply task.

Task 174 defines the production operator procedure for a terminal rollback failure without
adding automatic repair, live apply, or an agent-cleared terminal-state path. The runtime
can already enter `terminal_rollback_failed`, write an audit-linked terminal breadcrumb,
engage the kill-switch, and refuse later attempts on `terminal_rollback_failure_present`.
This task defines how a human operator may resolve that state and how the proof is audited.

## Terminal State

A terminal rollback failure record has:

- `record_type: reconcile_apply_terminal_rollback_failure`
- `task_id`
- `finding_kind`
- `proof`
- `idempotency_key`
- `reason`
- `write_error`
- `rollback_error`
- `changed_paths`
- `kill_switch_engaged`
- `audit_log_path`
- `audit_linked: true`
- `operator_resolution_required: true`
- `auto_clear_allowed: false`
- `auto_retry_allowed: false`
- `chain_hash`

The terminal record is appended to the Task 170 audit log and embedded into the engaged
kill-switch state. Any later apply attempt that sees that embedded terminal record refuses
before clone, validation, idempotency, audit, or write work. The system must never retry,
repair, or clear this state automatically.

## Manual Operator Procedure

An approved non-agent operator must:

1. Stop all reconcile apply attempts for the governed repository.
2. Download the Task 170 audit bundle and locate `terminal-rollback-failure.json` or the
   terminal audit JSONL entry.
3. Verify the audit hash chain, task id, idempotency key, changed paths, rollback error,
   and kill-switch engagement.
4. Inspect the governed repository manually and restore or repair the dirty files using a
   reviewed human procedure outside governed-agent tool surfaces.
5. Record a `reconcile_apply_terminal_rollback_resolution` proof bound to the terminal
   `chain_hash`, task id, idempotency key, operator approval, and audit destination.
6. Only after independent review may a future non-agent operator path clear the terminal
   state. Task 174 defines the proof model only; it does not implement the clearing writer.

## Resolution Proof

The resolution proof is a JSON object with:

- `record_type: reconcile_apply_terminal_rollback_resolution`
- `action: clear_terminal`
- `class_key: merged_but_not_done/git_ancestor`
- `task_id`
- `idempotency_key`
- `terminal_chain_hash`
- `proof_id`
- `origin`
- `operator_identity`
- `operator_approval_id`
- `audit_destination`
- `manual_resolution_summary`
- `agent_originated: false`
- `expires_at`

The proof refuses if it is missing, malformed, stale, replayed, wrong-class, mismatched to the terminal breadcrumb, missing operator approval, missing the terminal audit destination,
or governed-agent-originated. A structurally valid proof still returns
`terminal_resolution_gate_unsatisfiable` by default. Tests may pass an isolated
`terminal_resolution_gate_open=True` flag only to prove the proof and audit model.

## Agent Exclusion

Governed agents cannot clear terminal state, delete the breadcrumb, or re-enable the class
through:

- MCP
- package CLI
- `scripts/codex-task`
- hooks
- environment variables
- config files
- workflow state
- reports
- repair/start/kickoff paths

The terminal resolution helpers are pure model functions. They are not imported by CLI,
MCP, `scripts/codex-task`, hook, workflow, or report surfaces.

## Audit Record

`build_terminal_rollback_resolution_audit_record` produces an audited resolution record
that binds:

- terminal record type
- task id
- finding kind
- proof
- idempotency key
- terminal chain hash
- proof id
- operator identity
- operator approval id
- audit destination
- manual resolution summary
- outcome
- `auto_clear_allowed: false`
- `auto_retry_allowed: false`
- `agent_originated: false`
- previous hash and chain hash

This audit record is evidence only. It does not clear the kill-switch, delete the terminal
breadcrumb, retry rollback, or mutate Taskmaster status.

## Evidence

Task 174 is pinned by:

- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_terminal_resolution_requires_approved_non_agent_action_but_is_unsatisfiable_by_default`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_terminal_resolution_can_be_verified_only_in_isolated_gate_open_model`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_agent_originated_terminal_resolution_is_refused`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_terminal_resolution_rejects_forged_shapes`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_terminal_resolution_replay_is_refused`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_terminal_resolution_audit_record_binds_terminal_and_operator_proof`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_rollback_failure_is_terminal_and_engages_kill_switch`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_selected_channel_process_oracle_terminal_on_process_rollback_failure`
- `tests/meta_workflow_guard/test_aegis_reconcile_terminal_rollback_resolution_contract.py`
- `docs/aegis/reconcile-enablement-gate-status.json`

## Remaining Open Gates

- G5: Enablement Evidence Decision Packet
- G8: Final Agent-Surface Regression With The Selected Channel Present

## Non-Goals

- No live apply.
- No automatic repair.
- No agent-cleared terminal state.
- No terminal-state clearing writer.
- No kill-switch flip to enabled.
- No operator-local apply command.
- No MCP apply tool.
- No post-merge apply workflow.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
