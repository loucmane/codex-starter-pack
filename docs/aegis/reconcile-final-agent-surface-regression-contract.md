# Reconcile Final Agent-Surface Regression Contract

**Status:** active Task 175 contract.
**Closes:** G8: Final Agent-Surface Regression With The Selected Channel Present.
**Verdict:** G8 closed; NO-GO remains for any first guarded apply task until G5 closes.

## Scope

Task 175 re-runs the agent-surface regression after the selected post-merge channel,
audit destination, process oracle, kill-switch control plane, and terminal rollback
resolution machinery exist. This is a regression proof only. It does not enable apply,
does not add an apply command, does not flip the kill-switch, and does not broaden the
candidate class.

The selected channel remains an internal proof and process-oracle model. It is not exposed
through governed-agent surfaces.

## Standing Invariants

- Single-gated-caller audit still holds: `_perform_taskmaster_done_write` is loaded only
  by `run_reconcile_apply_write_apparatus`.
- `run_selected_channel_apply_with_process_oracle` is an internal helper and is not
  reachable from MCP, package CLI, `scripts/codex-task`, hooks, workflows, reports,
  preview consumers, repair, start, kickoff, or closeout surfaces.
- No MCP tool named `aegis.apply`, `aegis.reconcile_apply`, or equivalent exists.
- No package CLI or `scripts/codex-task` reconcile mutation flag exists.
- No agent-writable input can provide `enable_write_path`, `enable_gate_open`,
  `approved_context_proof`, selected-channel confirmation, idempotency claim,
  kill-switch state, kill-switch enablement, terminal-state clearing, terminal-resolution
  proof, validated toolchain evidence, or audit destination selection.
- Behavioral dispatch over real MCP schemas, package CLI parser targets, and
  `scripts/codex-task` parser targets resolves only to the existing installer/read-only
  workflow handlers, never to the apply runtime.
- The default configuration still produces zero governed-repo delta and returns
  `enable_gate_unsatisfiable`.

## Standing No-Go Rule

While any G1-G8 marker remains open, production apply entrypoints are forbidden. Task 176
later closed G5 with a decision packet, but the packet records `NO-GO` because no explicit
operator GO decision exists. The standing regression therefore asserts:

- `docs/aegis/reconcile-enablement-gate-status.json` remains `NO-GO`;
- `first_guarded_apply_task_allowed` remains `false`;
- no production workflow contains `run_selected_channel_apply_with_process_oracle`,
  `run_reconcile_apply_write_apparatus`, or `enable_write_path=True`;
- no governed-agent surface imports or names `reconcile_apply_runtime`;
- no satisfiable enable conjunction is reachable from default config or agent inputs.

## Evidence

- `tests/meta_workflow_guard/test_aegis_reconcile_final_agent_surface_regression.py`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_live_write_function_has_single_gated_caller`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_scaffold_is_not_reachable_from_agent_surfaces`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_kill_switch_control_plane_is_absent_from_agent_writable_surfaces`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_apply_write_apparatus_is_not_reachable_from_agent_surfaces`

## Later Gate Status

Task 176 later closed G5 with a decision packet. The current machine-readable status
remains `NO-GO` because that packet lacks an explicit operator GO decision.

## Non-Goals

- No live apply.
- No enablement.
- No first guarded apply task.
- No kill-switch flip to enabled.
- No operator-local apply command.
- No MCP apply tool.
- No post-merge apply workflow.
- No production approved context that can mutate.
- No terminal-state clearing writer.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
