# Aegis Reconcile Enablement Readiness Gates

**Status:** active Task 169 audit.
**Verdict:** NO-GO for creating any first guarded apply task.
**Scope:** evidence-backed gate inventory only. This task does not enable apply, create an
apply invocation channel, flip a kill-switch, add an MCP/CLI apply surface, mutate
Taskmaster status, or make the current test-enabled write apparatus reachable.

## Purpose

Tasks 144-168 built a default-off reconcile apply control plane in small, testable steps:
read-only promotion, side-effect evidence, precision corpus, rollback modeling, inert
candidate preview, agent-excluded apply design, disabled apply gates, shadow evidence,
semantic blast-radius validation, write-and-rollback apparatus, authority/freshness
hardening, corrected operator-facing claims, and Node24-compatible CI artifact transport.

Task 169 re-derived the readiness list after those changes. Task 170 closed the G7
audit-storage boundary, Task 171 closed the G1 approved-channel proof model, Task 172
closed the G4 selected-channel process-level oracle gate, Task 173 closed the G2/G3
agent-excluded enablement and kill-switch control-plane gates, and Task 174 closed the G6
terminal rollback failure operator-resolution gate. The machine-readable gate marker is
`docs/aegis/reconcile-enablement-gate-status.json`. The result remains intentionally
conservative:

- the safety spine is strong enough to keep the current system inert;
- the evidence streams are separated enough to avoid false precision claims;
- the internal write apparatus is still not a production apply path;
- no first guarded apply task may be scoped until the open gates below are closed with
  tests and reviewed evidence.

## Current Inert Boundary

The current implementation still has no governed-agent apply surface:

- no `aegis reconcile --apply` or equivalent mutation flag;
- no MCP apply tool;
- no `scripts/codex-task aegis reconcile` apply route;
- no operator-local apply command;
- no post-merge apply workflow;
- no enabled kill-switch state in repo or CI;
- no Taskmaster status mutation against the governed repository from reconcile.

`aegis_foundation/reconcile_apply_runtime.py` contains an internal write apparatus used by
isolated tests. Its default behavior refuses before validation or mutation. Tests may pass
`enable_write_path=True` only inside temporary fixtures to exercise rollback, idempotency,
audit, authority, freshness, and semantic-delta behavior.

## Closed Gates

These gates are currently satisfied for the default-off apparatus and shadow evidence.
They must remain standing gates in every later task.

| Gate | Current status | Evidence |
| --- | --- | --- |
| Read-only reconcile promotion | Closed | `docs/aegis/reconcile-promotion-contract.md`; reconcile surfaces still reject mutation flags. |
| First apply class narrowed to `merged_but_not_done/git_ancestor` | Closed | `docs/aegis/reconcile-mutation-rollback-contract.md`; Task 148 preview and Task 162 precision corpus use the same first class. |
| Agent-facing apply surface absent | Closed | `tests/meta_workflow_guard/test_aegis_reconcile_apply_write_apparatus.py::test_apply_write_apparatus_is_not_reachable_from_agent_surfaces`; `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py::test_apply_scaffold_is_not_reachable_from_agent_surfaces`. |
| Single live writer caller | Closed | `_perform_taskmaster_done_write` is referenced only by `run_reconcile_apply_write_apparatus`, pinned by `test_live_write_function_has_single_gated_caller`. |
| Default config produces zero governed-repo delta | Closed | `test_default_config_full_apply_path_has_zero_live_delta`. |
| Kill-switch evaluator fails closed | Closed for evaluation only | Missing, unreadable, corrupt, default-disabled, global-disabled, and class-disabled states refuse in scaffold/runtime tests. |
| Taskmaster authority is single-source in shadow and runtime checks | Closed for current shadow/runtime paths | Shadow delegates to `_taskmaster_state`; runtime calls `_taskmaster_state` before toolchain, clone, or write work. |
| Apply-time candidate freshness re-validation | Closed for the internal runtime | Runtime re-runs read-only `reconcile(... preview_candidates=True, use_github=False)` and refuses stale, done, missing, non-merged, or non-`git_ancestor` candidates. |
| Semantic validation fails closed | Closed | Missing, `None`, or false `semantic_delta_matches_prediction` refuses; no default-true semantic gate remains in the runtime. |
| Fresh sacrificial cascade validation required | Closed | Runtime refuses if validation is absent or if path/semantic deltas mismatch. |
| Live write delta/semantic mismatch rolls back | Closed in isolated runtime tests | After the write, actual paths must equal fresh prediction and semantic delta must pass, or snapshot rollback runs. |
| Terminal rollback failure freezes subsequent apply attempts | Closed in isolated runtime tests | Rollback failure writes a terminal breadcrumb, engages a kill-switch state, and later attempts refuse on `terminal_rollback_failure_present`. |
| Shadow evidence stream separation | Closed | Operational accumulation, cascade smoke, and precision corpus have distinct record types and classifications. |
| Replayable precision corpus | Closed for the first class | The corpus replays real synthetic git histories and gates `merged_but_not_done/git_ancestor` at 6 TP, 0 FP, 0 FN, and 0 boundary leaks under the pinned toolchain. |
| CI artifact transport under Node24 actions | Closed | Task 168 migrated to Node24 action majors and verified `reports/ci/` plus `$RUNNER_TEMP/aegis-shadow/` artifact layout on PR CI. |
| Audit storage, retention, and review boundary | Closed by Task 170 | `docs/aegis/reconcile-apply-audit-storage-contract.md`; `docs/aegis/reconcile-enablement-gate-status.json`; before-audit write failure blocks Taskmaster status writes. |
| Approved invocation and confirmation channel | Closed by Task 171 | `docs/aegis/reconcile-apply-approved-channel-contract.md`; selected post-merge CI proof shape; malformed/stale/PR-shaped/wrong/ref-task-proof/replayed/agent-originated confirmations refuse; valid proof remains unsatisfiable by default. |
| Live apply-time side-effect oracle gate | Closed by Task 172 | `docs/aegis/reconcile-apply-live-oracle-contract.md`; selected-channel wrapper snapshots before/after the internal attempt, persists channel/process-oracle artifacts, rolls back process-level unexpected deltas, and refuses non-baseline validated toolchain evidence. |
| Agent-excluded enablement mechanism | Closed by Task 173 | `docs/aegis/reconcile-apply-kill-switch-control-plane-contract.md`; agent-originated enable/clear actions from MCP, CLI, hooks, environment, config, workflow-state, reports, and `scripts/codex-task` refuse; approved non-agent enable remains unsatisfiable by default. |
| Kill-switch enablement and disable semantics | Closed by Task 173 | Durable global/per-class state fails closed for missing, corrupt, unreadable, stale, wrong-class, global-disabled, and class-disabled states before clone/write work; emergency disable is the only default-authorized control action. |
| Terminal rollback failure operator resolution | Closed by Task 174 | `docs/aegis/reconcile-terminal-rollback-resolution-contract.md`; terminal breadcrumbs are audit-linked, never auto-clear or auto-retry, later attempts refuse before clone/write work, and resolution proof requires approved non-agent operator action plus audit binding. |

## Open Gates Still Blocking Any First Guarded Apply Task

The following gates block creation of a first guarded apply task. A future task may close
one or more gates, but no task may scope live apply until every blocker has reviewed
evidence.

### G5: Enablement Evidence Decision Packet

**Status:** open.

Task 162 supplies a precision corpus artifact for the first class, and post-merge
accumulation supplies operational evidence. No final enablement decision packet exists that
names the pre-registered bar, the operational entries, the precision corpus result,
toolchain binding, residual risks, and explicit non-goals.

Required evidence before this gate can close:

- a reviewed decision packet that cites the precision corpus artifact as the precision basis
  and refuses to count empty operational ledgers or cascade smoke as precision;
- toolchain versions in the decision match the validated baseline and live job evidence;
- operational post-merge runs are listed as inertness/context evidence only;
- every unexplained divergence is zero, or each benign normalization is backed by a
  reviewed transform plus negative tests;
- the decision packet states whether the evidence is sufficient for a first apply task, not
  for broad enablement.

### G8: Final Agent-Surface Regression With The Selected Channel Present

**Status:** open.

Existing static tests prove no current agent surface reaches the runtime. Once a future
task adds any approved channel, that proof must be rerun with the new code present.

Required evidence before this gate can close:

- single-gated-caller audit still holds;
- no MCP tool, package CLI command, `scripts/codex-task` path, preview/report consumer,
  repair/start/kickoff flow, or hook can transitively reach apply;
- no agent-writable input can satisfy the selected approved context or kill-switch enable
  path;
- behavioral dispatch tests try the real MCP/CLI/codex-task surfaces and fail to reach the
  write function.

## Gate Closure Rule

Task 169's go/no-go answer, updated by Task 170's G7 closure, Task 171's G1 closure,
Task 172's G4 closure, Task 173's G2/G3 closure, and Task 174's G6 closure, is:

> No first guarded apply task may be scoped until G1-G8 are closed by reviewed code,
> tests, and evidence artifacts. Closing a gate may add refusals, audits, or
> documentation, but must not enable mutation or broaden the candidate class unless a
> later, separately reviewed enablement task explicitly owns that change.

G1, G2, G3, G4, G6, and G7 are now closed; G5 and G8 remain open. The future task
immediately after Task 174 should be another gate-closing task, not an enablement task.
Candidate sequencing:

1. final agent-surface regression with the selected channel present;
2. final enablement evidence decision packet;
3. only then scope a first guarded apply task, if the packet says GO.

## Non-Goals

- No apply or apply-like command.
- No kill-switch flip.
- No production approved context.
- No operator-local invocation.
- No post-merge apply workflow.
- No MCP apply tool.
- No agent-reachable enablement path.
- No new candidate class.
- No Taskmaster status mutation against the governed repository.
- No claim that the current write apparatus is ready for production enablement.
