# Reconcile Apply Kill-Switch Control Plane Contract

**Status:** active Task 173 contract.
**Closes:** G2: Agent-Excluded Enablement Mechanism and G3: Kill-Switch
Enablement And Disable Semantics.
G3: Kill-Switch Enablement And Disable Semantics is closed by this contract.
**Verdict:** G2 and G3 closed; NO-GO remains for any first guarded apply task.

Task 173 defines the durable enable/disable control plane for the future reconcile apply
path without turning it on. The implementation remains a pure Python data model and
evaluator. It does not add an MCP tool, package CLI command, `scripts/codex-task` route,
hook, workflow, environment variable, or config setting that can enable apply.

## Durable State Shape

The production kill-switch state is a JSON object with:

- `record_type: reconcile_apply_kill_switch_control_plane`
- `version: 1`
- `expires_at`
- `writer.origin`
- `global.enabled`
- `global.disabled`
- `classes.<class-key>.class_key`
- `classes.<class-key>.enabled`
- `classes.<class-key>.disabled`

The first supported class remains `merged_but_not_done/git_ancestor`. A durable state that
omits that class, contains a mismatched class key, has an unknown record type, has an
unsupported version, or has malformed global/classes blocks refuses before clone,
validation, idempotency, audit, or write work.
Every such refusal happens before clone, validation, idempotency, audit, or write work.

No enabled durable state is committed to the repository or CI. Even a valid
enable-shaped state returns `enable_gate_unsatisfiable` unless a later reviewed task makes
the enable conjunction satisfiable. Default local and CI state therefore remain zero-delta
and refused.

## Refusal Semantics

The kill-switch evaluator fails closed for:

- missing state
- corrupt state
- unreadable state
- stale state
- wrong-class state
- global disabled
- class disabled
- default global disabled/off
- default class disabled/off

Explicit disable is load-bearing and outranks valid context, candidate eligibility,
precision evidence, toolchain match, idempotency, and an otherwise enable-shaped state.
Global emergency disable applies before class matching or expiry. Per-class disable
applies before enable.

## Agent-Excluded Control Actions

Task 173 models control-plane write authorization through
`evaluate_kill_switch_control_action`. The evaluator recognizes `enable`, `disable`, and
`clear_terminal` actions but exposes no writer or entrypoint.

Governed-agent origins are always refused, including:

- MCP
- package CLI
- `scripts/codex-task`
- hooks
- environment variables
- config files
- workflow state
- reports
- generic governed-agent origins

Emergency disable may be authorized only from an approved non-agent origin. Enable remains
stricter: an approved non-agent origin and operator approval are still insufficient while
the enable gate is unsatisfiable. Clearing terminal rollback state remains gated by the
future G6 terminal-resolution mechanism and is not opened here.
Clearing terminal rollback state remains gated by the future G6 terminal-resolution mechanism.

## Surface Boundary

The following surfaces must not import or dispatch the kill-switch control-plane helpers:

- `aegis_foundation/cli.py`
- `aegis_mcp/server.py`
- `scripts/codex-task`
- Claude hooks and gate scripts
- workflow/report consumers

The current agent-facing surfaces still expose no apply command, no apply-like flag, no
kill-switch enable command, no kill-switch clear command, and no governed-agent route that
can rewrite the switch.

## Evidence

Task 173 is pinned by:

- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_durable_kill_switch_control_plane_refuses_bad_state`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_durable_kill_switch_disable_precedence_over_enable_shape`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_agent_originated_control_plane_actions_are_refused`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_kill_switch_enable_remains_unsatisfiable_for_approved_non_agent_origin`
- `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_emergency_disable_is_the_only_default_authorized_control_action`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_remove_one_conjunct_refuses_before_mutation_and_expensive_validation`
- `tests/meta_workflow_guard/test_aegis_reconcile_apply_kill_switch_control_plane_contract.py`
- `docs/aegis/reconcile-enablement-gate-status.json`

## Remaining Open Gates

- G5: Enablement Evidence Decision Packet
- G6: Terminal Rollback Failure Operator Resolution
- G8: Final Agent-Surface Regression With The Selected Channel Present

## Non-Goals

- No apply or apply-like command.
- No kill-switch flip to enabled.
- No live apply.
- No operator-local apply command.
- No MCP apply tool.
- No post-merge apply workflow.
- No production approved context that can mutate.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
