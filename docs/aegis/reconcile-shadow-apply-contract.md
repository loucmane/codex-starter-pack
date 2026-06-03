# Aegis Reconcile Shadow Apply Contract

**Status:** active Task 151/152 contract; consumed by Task 153 fresh validation.
**Scope:** shadow evidence only. This task does not enable reconcile mutation and does not
expose apply through governed-agent surfaces.

## Purpose

Task 151 runs the future reconcile apply pipeline in shadow mode so Aegis can observe the
machine making would-apply decisions before any live write path exists.

Shadow mode is evidence-producing, not execution-producing. It may validate the predicted
Taskmaster done cascade inside a detached sacrificial clone, but it must never mutate the
governed repository.

## Shadow Boundary

The only finding class that may emit `would_apply` is:

- finding kind: `merged_but_not_done`
- proof: `git_ancestor`

All other findings are excluded or represented as `shadow_refused`. This includes
GitHub/squash proof, done-but-not-merged classes, multi-PR ambiguity, stale/ad-hoc stubs,
abandoned in-progress branches, and git-only unknown merge truth.

Every would-apply record must be marked:

- `mode: shadow`
- `executed: false`
- `mutated_live_repo: false`

## Approved Context Proof

Task 151 exercises the Task 150 positive approved-context proof model, but only for shadow
decisions. A well-formed post-merge CI context may allow a shadow artifact to be produced;
it still cannot make live mutation possible.

Missing, malformed, unapproved, or binding-mismatched context proofs produce
`shadow_refused`.

## Sacrificial Clone Validation

Shadow would-apply records must validate the predicted blast radius before reporting it as
safe.

Validation runs the real Taskmaster status cascade only in a detached temporary copy of
the current target state. The governed repository is never the subprocess working
directory. The clone must be faithful for the predicted delta paths before the mutation
runs.

The record must include:

- predicted blast-radius paths
- actual sacrificial-clone delta paths
- whether actual deltas matched prediction
- baseline metadata for predicted paths
- rollback-prep metadata

The shadow prediction starts from the Task 148 preview paths and adds dynamic Taskmaster
runtime paths observed during the real status cascade. Under the pinned Task 152
Taskmaster toolchain, `.taskmaster/state.json` is part of the status-cascade blast radius
whether it is created from absence or rewritten from a pre-existing baseline. The Task 147
rollback contract remains the authority for the older registered done-cascade fixture;
Task 151/152 records target- and toolchain-specific shadow evidence for the future apply
path.

## Artifact Contract

CI mode writes no persistent repo state. It returns or prints artifact-ready JSON for
GitHub Actions artifact upload. The CI workflow captures a real GitHub Actions context
proof artifact before any live write code exists.

Local/test mode may write exactly one caller-declared shadow report path and no other
path. The side-effect oracle is the authority for this boundary.

Shadow artifacts must not contain executable command strings or action-shaped fields that
an agent could treat as an instruction.

## CI Cascade Validation

Task 152 promotes the shadow evidence from locally validated cascade behavior to
CI-environment cascade behavior. GitHub Actions must provision a deterministic pinned
Taskmaster CLI before pytest, then run the same sacrificial cascade validation under that
toolchain.

The pinned Taskmaster toolchain is defined by `aegis_foundation.taskmaster_toolchain` and
includes:

- package name and version
- install source and install spec
- provisioning lock id
- Node major version used to run the CLI
- Python matrix version and runner identity fields

Shadow cascade evidence is valid for a future apply path only when the future apply
toolchain matches the validated toolchain binding. A Taskmaster version/source,
provisioning-lock, Node/Python, or relevant runner identity mismatch invalidates prior
cascade evidence and requires fresh CI sacrificial validation before apply can proceed.

Task 153 does not treat Task 152 evidence as permission to mutate. The write apparatus must
run fresh apply-time sacrificial validation under the current toolchain and refuse on stale
toolchain evidence or mismatched actual deltas.

The CI validation artifact must cover both known Taskmaster state branches:

- `.taskmaster/state.json` absent before mutation: Taskmaster may create it, so the dynamic
  predicted blast radius and actual sacrificial delta must include it.
- `.taskmaster/state.json` already present before mutation: current pinned Taskmaster
  behavior rewrites it, so the dynamic predicted blast radius and actual sacrificial delta
  must still include it.

The skip guard for local environments without `task-master` remains valid test hygiene, but
the supported CI workflow must install the pinned CLI so the real-cascade tests execute
there rather than skip.

## Agent Surface Boundary

Task 151 must not add:

- `--apply`
- an MCP apply tool
- an agent-facing `scripts/codex-task` apply route
- a Taskmaster status writer against the governed repo
- Git, PR, closeout, session, plan, work-tracking, or Aegis-state writes
- an enable gate that can be satisfied

## Enforcement Map

| Contract clause | Enforcing test |
| --- | --- |
| CI shadow mode emits validated `would_apply` and mutates no live repo files | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_ci_mode_emits_prediction_validated_would_apply_without_live_deltas` |
| Local mode writes only the declared report path | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_local_mode_writes_only_declared_report_path` |
| Manual, unknown, ambiguous, and wrong-proof cases never emit `would_apply` | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_manual_unknown_and_wrong_proof_cases_never_emit_would_apply` |
| Missing, malformed, and unapproved contexts refuse before validation | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_refuses_missing_malformed_unapproved_contexts_before_validation` |
| Sacrificial clone validation is faithful, detached, and leaves live state unchanged | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_sacrificial_clone_validation_is_faithful_detached_and_does_not_mutate_live_repo` |
| Pre-existing `.taskmaster/state.json` is included when the pinned Taskmaster cascade rewrites it | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_prediction_includes_preexisting_state_json_delta` |
| CI cascade artifact covers both `.taskmaster/state.json` branches under one pinned toolchain | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_ci_shadow_cascade_validation_report_covers_both_state_json_branches` |
| Toolchain mismatch invalidates prior cascade evidence | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_taskmaster_toolchain_mismatch_invalidates_prior_cascade_evidence` |
| CI context proof is deterministic from GitHub Actions run fields | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_build_ci_shadow_context_proof_uses_stable_github_run_fields` |
| Governed-agent surfaces remain inert | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_shadow_apply_is_not_reachable_from_agent_surfaces` |
| Existing writer functions do not consume shadow apply | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_existing_writers_do_not_consume_shadow_apply` |
| CI workflow captures a shadow context proof artifact without adding apply | `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py::test_ci_workflow_captures_shadow_context_artifact_without_apply_surface` |
| CI provisions the pinned Taskmaster CLI before pytest | `tests/meta_workflow_guard/test_ci_workflows.py::test_python_test_workflow_provisions_pinned_taskmaster_before_pytest` |
| CI captures the full shadow cascade validation artifact without an apply surface | `tests/meta_workflow_guard/test_ci_workflows.py::test_python_test_workflow_captures_shadow_cascade_validation_artifact` |

## Non-Goals

- No enabled mutation.
- No Taskmaster status write against the governed repository.
- No Git or GitHub write.
- No closeout shortcut.
- No workflow-state write.
- No agent-facing apply entrypoint.
- No default-on future apply behavior.
- No use of shadow evidence as a substitute for fresh apply-time validation.
