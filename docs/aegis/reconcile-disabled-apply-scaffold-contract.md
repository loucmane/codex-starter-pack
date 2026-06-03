# Aegis Reconcile Disabled Apply Scaffold Contract

**Status:** active Task 150 contract, extended by Task 153 runtime tests.
**Scope:** disabled scaffold only. This task does not enable reconcile mutation and does
not expose apply through governed-agent surfaces.

## Purpose

Task 150 implements the safe room described by Task 149. It creates internal primitives
for a future reconcile apply path, while proving the current scaffold cannot mutate under
any input.

The scaffold is not an implementation of apply. It is an always-refusing orchestration
model for:

- positive approved-context proof evaluation
- apply-audit transaction records
- global and per-class kill-switch semantics

## Positive Context Gate

The scaffold does not try to detect agents by denylist. It requires positive proof of an
approved non-agent context and refuses by default.

Future acceptable context families are:

- `post_merge_ci`
- `operator_controlled_local`

Task 150 deliberately makes the default enable gate unsatisfiable. Even a well-formed
future context proof returns refusal unless a later internal runtime explicitly opens the
gate inside an isolated test-enabled context.

## Apply-Audit Transaction Record

The audit model is transaction-shaped, not event-shaped. It records:

- before/after phase
- task id
- finding kind
- proof artifact
- allowed-delta hashes
- approved-context proof id
- authorization binding for task id plus proof
- rollback handle reference
- `rolled_back`
- eligibility/corpus version
- idempotency key
- hash-chain fields
- external-anchor fields

Task 150 validates and serializes the model but does not write audit breadcrumbs to
governed workflow surfaces.

Task 153 extends the audit payload with runtime fields for the isolated write apparatus:
toolchain evidence, predicted and actual delta paths, before/after hashes, outcome, and
rollback state. These fields are still not exposed through governed-agent surfaces.

## Kill-Switch Semantics

Kill-switch evaluation is fail-closed:

- absent state is disabled
- missing state is disabled
- unreadable state is disabled
- corrupt state is disabled
- explicit global disable overrides all enable/proof/confirmation inputs
- explicit per-class disable overrides matching class enable/proof/confirmation inputs
- global and per-class enables remain insufficient because the Task 150 enable gate is
  intentionally unsatisfiable

Task 153 keeps the default behavior fail-closed while allowing the internal runtime tests to
open the gate explicitly. That test-only gate is not a CLI flag, MCP parameter, environment
variable, or report consumer path.

## Agent Surface Boundary

The scaffold is internal. It must not appear as:

- an MCP tool
- `aegis reconcile --apply`
- a package CLI reconcile mutation flag
- an agent-facing `scripts/codex-task aegis reconcile` path
- a Taskmaster status writer
- a git, PR, closeout, session, plan, work-tracking, or Aegis-state writer

## First Future Class

The only class modeled by this scaffold as a future apply candidate is:

- finding kind: `merged_but_not_done`
- proof: `git_ancestor`

All other classes are refused before mutation.

## Enforcement Map

| Contract clause | Enforcing test |
| --- | --- |
| Disabled scaffold has zero filesystem side effects across reconcile fixtures | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_disabled_apply_scaffold_has_zero_side_effects_across_precision_corpus` |
| Enable gate is unsatisfiable under current inputs | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_enable_gate_is_unsatisfiable_for_all_current_inputs` |
| Apply scaffold is not exposed on governed-agent surfaces | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_scaffold_is_not_reachable_from_agent_surfaces` |
| Kill-switch defaults and corrupt/unreadable states fail closed | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_kill_switch_fail_closed_states` |
| Explicit global and per-class disables override enable-shaped input | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_kill_switch_disable_precedence` |
| Apply-audit records validate required transaction fields and bindings | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_audit_record_requires_transaction_fields_and_binding` |
| Audit idempotency and hash-chain fields are stable and task/proof-bound | `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_audit_record_idempotency_and_chain_are_stable` |
| Default-off write apparatus proves zero live-repo deltas | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_default_config_full_apply_path_has_zero_live_delta` |
| Runtime write apparatus remains unreachable from agent surfaces | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_apply_write_apparatus_is_not_reachable_from_agent_surfaces` |
| Rollback and terminal rollback failure are tested under isolated write execution | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_partial_apply_failure_rolls_back_snapshot_restore`; `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_rollback_failure_is_terminal_and_engages_kill_switch` |

## Non-Goals

- No `--apply`, `--auto`, `--fix`, `--set-status`, `--done`, `--closeout`, `--mutate`,
  `--write`, or `--push` reconcile flag.
- No enabled mutation.
- No Taskmaster write.
- No git or GitHub write.
- No closeout shortcut.
- No workflow-state write.
- No agent-facing apply entrypoint.
