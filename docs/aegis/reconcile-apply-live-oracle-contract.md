# Aegis Reconcile Apply Live Oracle Contract

**Status:** active Task 172 contract.
**Closes:** G4: Live Apply-Time Side-Effect Oracle Gate.
**Verdict:** G4 closed; NO-GO remains for any first guarded apply task.
**Scope:** selected-channel process-level oracle, audit evidence, and runtime toolchain
baseline binding only. This task does not add a post-merge apply workflow, expose apply,
enable mutation, flip a kill-switch, or mutate Taskmaster status in the governed repo.

## Purpose

Task 171 selected post-merge CI as the first future apply confirmation channel. Task 172
adds the process-level oracle that any such channel must use before it can ever be made
satisfiable. The oracle wraps the internal runtime attempt with a governed-repo snapshot
before and after the attempt, compares the observed delta to the allowed Taskmaster status
cascade, persists operator-readable oracle evidence, and rolls back unexpected deltas.

This closes only G4. The selected channel is still internal, test-enabled only, and
unreachable from CLI, MCP, `scripts/codex-task`, hooks, preview, report, repair, kickoff,
or start surfaces. Task 173 later closed G2/G3, and Task 174 later closed G6. G5 and G8
remain open.

## Process Oracle

The selected-channel wrapper is
`run_selected_channel_apply_with_process_oracle`. It is an internal Python helper, not an entrypoint.
It performs these steps:

1. evaluate the Task 171 selected-channel confirmation proof;
2. refuse by default while the enable gate is unsatisfiable;
3. require the audit destination to be outside the governed repository;
4. persist `channel-confirmation.json` in the Task 170 audit destination before invoking
   the internal runtime;
5. snapshot the governed repository immediately before and after the internal attempt;
6. allow only the runtime-reported Taskmaster status cascade on success, and no governed
   repo delta on refusal, noop, rollback, or runtime error;
7. roll back any unexpected process-level delta;
8. enter terminal fail-closed state if process-level rollback itself fails;
9. persist `process-oracle.json` as operator-facing evidence.

The process oracle report uses record type `reconcile_apply_process_oracle` and records:

- selected channel and proof id;
- task id, finding kind, proof, idempotency key, and audit destination;
- before/after snapshot refs;
- allowed delta paths;
- actual delta paths;
- unexpected and missing delta paths;
- allowed external artifact paths;
- rollback state;
- chain hash.

## Allowed Deltas

The only governed-repo delta allowed by the selected-channel process oracle is the same
freshly validated Taskmaster status cascade that the internal runtime reports:

- `.taskmaster/tasks/tasks.json`;
- `.taskmaster/tasks/task_<id>.md`;
- `.taskmaster/state.json`, only when the validated cascade actually changes it and its
  content-level state contract passes.

No `.aegis`, work-tracking, source, plan, session, workflow-state, git-ref, or unrelated
Taskmaster path may appear in the process-level actual delta. A refusal, noop, rollback,
or runtime error must leave the governed repo byte-identical to the process-level before
snapshot.

## Audit Evidence

Task 172 binds G1 and G7 into the runtime audit path:

- runtime audit records now include the selected channel identity from the confirmation
  proof;
- runtime audit records include the selected audit destination;
- `channel-confirmation.json`, `apply-audit.jsonl`, and `process-oracle.json` share the
  same idempotency-keyed audit root;
- operator-facing text may claim mutation-time blast-radius verification only when backed
  by the process oracle report.

Audit/report artifacts remain outside mutable Taskmaster data. The oracle does not permit
in-repo ledgers or new generated work-tracking, session, plan, source, or workflow files.

## Toolchain Binding

The live runtime now refuses validated toolchain evidence unless it identifies the
source-controlled precision-validated baseline:

- `evidence_role: validated_ci_baseline`;
- `baseline_source.type: source_controlled_constants`;
- Taskmaster package version and install spec match the pinned `task-master-ai@0.43.1`;
- Node major, Python major/minor, runner OS/arch, provisioning lock id, and lock version
  match the validated baseline and current live evidence.

Comparing two live captures to each other is not valid. A missing, malformed, non-baseline,
or stale toolchain record refuses before fresh validation, idempotency claim, audit, or write.

## Enforcement Map

| Contract clause | Enforcing evidence |
| --- | --- |
| G4 is closed and NO-GO remains | `docs/aegis/reconcile-enablement-gate-status.json`; `tests/meta_workflow_guard/test_aegis_reconcile_apply_live_oracle_contract.py` |
| Selected-channel wrapper is not an agent surface | `tests/meta_workflow_guard/test_aegis_reconcile_apply_live_oracle_contract.py::test_live_oracle_contract_keeps_selected_wrapper_internal_and_default_off`; existing agent-surface tests |
| Process oracle persists channel and oracle artifacts | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_selected_channel_process_oracle_wraps_success_and_persists_artifacts` |
| Process-level unexpected delta rolls back | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_selected_channel_process_oracle_rolls_back_validation_side_effect` |
| Process-level rollback failure enters terminal fail-closed state | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_selected_channel_process_oracle_terminal_on_process_rollback_failure` |
| Live runtime refuses non-baseline validated toolchain evidence | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_live_runtime_refuses_non_precision_validated_toolchain_baseline` |

## Remaining Open Gates

Task 172 closed G4 only. Task 173 later closed G2/G3, and Task 174 later closed G6. These
gates remain open and block any first guarded apply task:

- G5: Enablement Evidence Decision Packet
- G8: Final Agent-Surface Regression With The Selected Channel Present

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
