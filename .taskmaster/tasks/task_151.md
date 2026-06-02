# Task ID: 151

**Title:** Add Reconcile Shadow Apply Mode with Validated Would-Apply Artifacts

**Status:** done

**Dependencies:** 150 ✓

**Priority:** medium

**Description:** Implement an inert reconcile shadow orchestration path that runs the future apply decision pipeline end-to-end for only the first eligible class, `merged_but_not_done` with `git_ancestor` proof, while keeping live Taskmaster, Git, workflow-state, and agent-facing mutation physically impossible.

**Details:**

Build this as the next step after the disabled apply scaffold in `aegis_foundation/reconcile_apply_scaffold.py`, not as a live apply implementation. Add a separate shadow orchestration module or tightly scoped primitives, for example `aegis_foundation/reconcile_shadow_apply.py`, that consumes existing reconcile output from `scripts/_aegis_installer.py::reconcile(..., preview_candidates=True)` and reuses the existing candidate boundary from `_reconcile_mutation_candidate_preview`, `_reconcile_finding_proof`, and the Task 146 classifier in `tests/meta_workflow_guard/reconcile_precision_corpus.py` (`bucket_for_finding`, `FindingKey`) rather than introducing a second eligibility definition. The only finding that may produce a `would_apply` record is `finding_kind=merged_but_not_done` and `proof=git_ancestor`; manual-only, unknown, ambiguous, GitHub-only, and non-first auto classes must produce no `would_apply` entry and should instead be omitted or represented as `shadow_refused` with explicit reasons.

Reuse Task 150 primitives from `aegis_foundation/reconcile_apply_scaffold.py`: `ApplyCandidate`, `evaluate_approved_context`, `evaluate_kill_switch`, `authorization_binding_for`, `idempotency_key_for`, and `build_apply_audit_record`. Shadow mode may accept approved-context-shaped CI/local proofs so it can generate a decision artifact, but it must not make the existing enable gate satisfiable and must never call `run_disabled_apply_scaffold` as a stepping stone to mutation. Preserve the fail-closed behavior for missing, malformed, unapproved, binding-mismatched, kill-switch-disabled, and wrong-proof inputs by emitting `shadow_refused` records.

Add a sacrificial-clone validator that creates a faithful detached copy of the current target repo state, runs the real Taskmaster done cascade only inside that clone (`task-master set-status --id=<task_id> --status=done` plus generated task refresh as established in `tests/meta_workflow_guard/reconcile_mutation_rollback_contract.py::run_taskmaster_done_cascade_fixture`), snapshots before/after with the Task 145 oracle from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py`, and records whether actual deltas match the predicted blast radius from the preview candidate (`.taskmaster/tasks/tasks.json` and the task markdown path from `_taskmaster_generated_task_markdown_rel`). The governed/live repo must never receive this Taskmaster command, generated-file refresh, Git ref update, PR write, `.aegis/state` write, session write, plan write, work-tracking write, or live task-file write.

Emit a machine-readable would-apply audit artifact with fields such as `record_type`, `mode="shadow"`, `executed=false`, `mutated_live_repo=false`, `task_id`, `finding_kind`, `proof`, `candidate_boundary`, `approved_context`, `kill_switch`, `proof_artifact`, `predicted_blast_radius_paths`, `actual_sacrificial_delta_paths`, `sacrificial_delta_matches_prediction`, `rollback_baseline_metadata`, `authorization_binding`, `idempotency_key`, and `external_anchor` for CI runs. Ensure idempotency keys are deterministic for the same merge event across reruns by hashing stable task/proof/proof-artifact fields, not timestamps or temp clone paths.

Add a CI/local output contract. In CI mode, shadow orchestration must write no repo files and only print or return artifact-ready JSON for workflow upload. In local/test mode, it may write exactly one caller-declared report path and no other path. Use a new explicit shadow report path option or function parameter, but do not add `--apply`, do not add an MCP apply tool, do not expose executable command strings, and do not create a `scripts/codex-task` live mutation route. If any CLI surface is added, it must be named and documented as shadow/report-only, keep all existing reconcile mutation flags rejected in `scripts/codex-task`, `aegis_foundation/cli.py`, and `aegis_mcp/server.py`, and keep the Task 150 enable gate unsatisfiable.

**Test Strategy:**

Add focused pytest coverage, likely in `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`, for eligible shadow generation, manual-only findings, unknown/non-ancestor proof, ambiguous findings, missing context, malformed context, unapproved context, binding mismatch, kill-switch missing/corrupt/disabled, and wrong-proof cases. Positive tests must prove only `(merged_but_not_done, git_ancestor)` emits `would_apply` and every shadow record has `mode=shadow`, `executed=false`, and `mutated_live_repo=false`.

Run shadow mode through the Task 145 side-effect oracle. Add local-mode oracle tests proving the only allowed live-tree delta is the declared shadow report path, and CI-mode tests proving zero repo-file deltas. Add sacrificial-clone tests proving the clone is detached/faithful to the current repo state, the real Taskmaster status cascade runs only inside the clone, and actual clone deltas exactly equal the predicted blast radius.

Add negative import/call tests using monkeypatch or inspect-based guards to fail if shadow orchestration imports or calls live Taskmaster/Git/workflow-state writers, including `task-master set-status` against the governed repo, `set_task_status`, Git ref writes, PR writes, `.aegis/state`, sessions, plans, work-tracking, or live `.taskmaster/tasks` writers. Add agent-surface tests confirming there is still no `--apply`, no MCP apply tool, no executable command string in shadow artifacts, and no `codex-task` mutation route.

Add a GitHub Actions CI contract/workflow test fixture showing approved-context-shaped CI input can generate shadow decisions/artifact JSON while still being unable to permit live mutation. Re-run adjacent guards: `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`, `tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py`, `tests/meta_workflow_guard/test_aegis_reconcile_mutation_candidate_preview_contract.py`, `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py`, `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`, and the new shadow test file.
