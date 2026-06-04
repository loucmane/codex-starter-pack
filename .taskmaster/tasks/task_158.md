# Task ID: 158

**Title:** Add post-merge shadow accumulation with mismatch triage

**Status:** pending

**Dependencies:** 157 ✓, 159 ✓

**Priority:** high

**Description:** Run post-merge shadow/would-apply accumulation on the hardened validator, with explicit mismatch triage for semantic canonicalization coverage and measurement/trigger correctness fixes from the integrated adversarial retrospective before any enablement work.

**Details:**

Scope: after semantic validation and adapter hardening, run shadow apply decisions under the real post-merge trigger and accumulate evidence over real merge events without enabling live apply. Build on the existing inert shadow surfaces in `aegis_foundation/reconcile_shadow_apply.py`, especially `build_shadow_report`, `build_shadow_record`, `validate_sacrificial_taskmaster_done_cascade`, `validate_taskmaster_apply_semantic_delta`, `build_ci_shadow_context_proof`, and `build_ci_shadow_cascade_validation_report`, plus CI wiring in `.github/workflows/ci.yml` and tests under `tests/meta_workflow_guard/`.

Acceptance criteria and required implementation details:

1. Preserve shadow-only behavior. The accumulation path must never execute live apply, enable apply, flip any kill switch, expose an agent-reachable apply/write path, mutate Taskmaster, mutate Aegis state, mutate git refs, or alter project source. The only allowed outputs are declared CI upload artifact files under the CI artifact/report path, for example the existing `reports/ci/reconcile-shadow-context-proof.json`, `reports/ci/reconcile-shadow-cascade-validation.json`, and a new post-merge accumulation/triage artifact. There must be no in-repo accumulation ledger, no committed state file, and no repository-state track record.

2. Bind evidence to the real post-merge trigger. The shadow context proof must distinguish real `push` to `main` post-merge CI from `pull_request` CI. Evidence captured from PR CI must be emitted with `valid_for_shadow=false` and must not be accepted as `post_merge_ci` accumulation evidence. Pull-request artifacts may still be useful diagnostics, but they must not be able to forge a post-merge proof into the accumulation ledger/artifact.

3. Add post-merge accumulation and triage reporting. The accumulation artifact must distinguish apply-decision divergence from canonicalization completeness findings. Every semantic mismatch must be reported as triage-required and classified as real divergence or unobserved benign normalization. Mismatch triage is reporting-only: the job may flag mismatches, mark the run paused/failed, and emit triage-required evidence, but it must never modify `TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION`, auto-extend canonicalization exemptions, or write an exemption/normalization list. Any benign-normalization acceptance must land later as a separate reviewed code change to `validate_taskmaster_apply_semantic_delta` or narrow canonicalization helpers in `aegis_foundation/reconcile_shadow_apply.py`, with a specific content-preserving transform and paired negative tests proving adjacent semantic drift is still rejected. Count K benign normalizations only after those reviewed validator updates are merged. The promotion gate remains zero unexplained divergences across the accumulated post-merge sample.

4. Fix dynamic `.taskmaster/state.json` prediction. Sacrificial cascade validation must derive `.taskmaster/state.json` membership from the actual sacrificial-clone delta or treat it as allowed-but-not-required, rather than relying on a static present/absent prediction. Add a steady-state fixture where `.taskmaster/state.json` already contains `migrationNoticeShown:true` and a legitimate candidate records `would_apply` rather than `sacrificial_delta_mismatch`. This amends the current static coverage around `test_shadow_prediction_includes_preexisting_state_json_delta` and `test_ci_shadow_cascade_validation_report_covers_both_state_json_branches`.

5. Fix precision evidence labeling. Precision evidence must be keyed and labeled by the live `(finding_kind, proof_source)` pair, not by `finding_kind` alone and not by the old `task146-v1` corpus label. Update the precision helper pattern in `tests/meta_workflow_guard/reconcile_precision_corpus.py` so reports do not emit precision or promotion figures for zero-observation pairs. A `git_ancestor` evidence stream must never imply coverage for `github_pr_merged` or any other proof source.

6. Add process-level CI side-effect oracle coverage around the actual post-merge accumulation command/job. Wrap the real accumulation step with the whole-tree snapshot patterns from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` (`snapshot_whole_tree` / `assert_matches`) and fail on any governed-repo delta in `.taskmaster`, `.aegis` state, `docs/ai/work-tracking`, `plans`, `sessions`, git refs, or source files. Reuse the existing `repo_file_write_policy` contract in `aegis_foundation/reconcile_shadow_apply.py`. The workflow should keep `permissions: contents: read` for shadow-only jobs, and tests in `tests/meta_workflow_guard/test_ci_workflows.py` must assert that read-only permission discipline remains present.

7. Keep artifact discipline explicit. The accumulation job may write declared JSON artifacts for CI upload, but those files must be outside governed repository state and treated as upload artifacts only. It must not create or update an in-repo ledger, committed state file, `.taskmaster` data, `.aegis/state`, work-tracking files, plan/session files, git refs, or source files.

8. Re-run and name the standing Task 157/159 gates with the new post-merge job present: agent-facing surfaces remain unable to reach apply/write paths; `target_dir` remains the sole Aegis MCP target selector; degraded classification remains structurally delegated to the main classifier; no single-gated-caller invariant and no read-only classifier invariant may be weakened. Treat the retrospective risks as Task 158 measurement/trigger correctness fixes, not safety escapes.

Non-goals: no live apply, no enablement, no kill-switch flip, no in-repo accumulation ledger, no auto-extension of semantic canonicalization exemptions, and no treating PR-CI shadow artifacts as post-merge accumulation evidence.

**Test Strategy:**

Add focused pytest coverage beside `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`, `tests/meta_workflow_guard/test_ci_workflows.py`, and `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py`. Required tests: (1) steady-state `.taskmaster/state.json` with `migrationNoticeShown:true` yields `would_apply` and not `sacrificial_delta_mismatch`; (2) precision metrics are keyed by `(finding_kind, proof_source)`, omit zero-observation promotion figures, and do not let `git_ancestor` imply `github_pr_merged`; (3) PR CI context proofs are `valid_for_shadow=false` while push/main proofs are accepted; (4) the actual post-merge accumulation command/job is wrapped in `snapshot_whole_tree`/`assert_matches` and permits only declared CI artifact outputs; (5) `.github/workflows/ci.yml` keeps `permissions: contents: read` and does not include apply-shaped commands for shadow jobs; (6) mismatch triage artifacts are reporting-only and do not mutate `TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION` behavior or normalization lists; (7) Task 157/159 guard suites still pass with the new post-merge job present, including agent-facing apply/write path isolation, `target_dir` selector discipline, delegated degraded classification, single-gated-caller, and read-only classifier invariants.

## Subtasks

### 158.1. Bind post-merge shadow context and artifact-only accumulation

**Status:** pending
**Dependencies:** None

Implement the post-merge accumulation path against the real push/main trigger while marking PR-CI evidence invalid for shadow accumulation.

**Details:**

Update `build_ci_shadow_context_proof`/related accumulation plumbing in `aegis_foundation/reconcile_shadow_apply.py` and `.github/workflows/ci.yml` so only real push/main post-merge CI can produce valid accumulation evidence. Emit declared CI upload artifacts only, with no in-repo ledger or state writes.

### 158.2. Make state.json prediction dynamic

**Status:** pending
**Dependencies:** None

Amend sacrificial cascade validation so `.taskmaster/state.json` is derived from the actual sacrificial delta or treated as allowed-but-not-required.

**Details:**

Adjust prediction/validation around `validate_sacrificial_taskmaster_done_cascade` and `_predicted_paths` in `aegis_foundation/reconcile_shadow_apply.py`. Add the steady-state `migrationNoticeShown:true` fixture and ensure legitimate candidates still emit `would_apply`.

### 158.3. Key precision evidence by finding/proof pair

**Status:** pending
**Dependencies:** None

Update precision reporting so evidence and promotion figures are keyed by `(finding_kind, proof_source)` and never by finding kind alone.

**Details:**

Revise `tests/meta_workflow_guard/reconcile_precision_corpus.py` and any accumulation evidence schema to avoid `precision_by_kind`-only semantics and avoid old `task146-v1` labels for live promotion evidence. Do not emit precision or promotion figures for zero-observation pairs.

### 158.4. Wrap real accumulation in CI side-effect oracle

**Status:** pending
**Dependencies:** None

Add process-level side-effect oracle coverage around the actual post-merge accumulation step.

**Details:**

Reuse `snapshot_whole_tree`/`assert_matches` from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` and the `repo_file_write_policy` contract in `aegis_foundation/reconcile_shadow_apply.py` to prove governed repo surfaces remain unchanged during CI accumulation.

### 158.5. Keep mismatch triage reporting-only

**Status:** pending
**Dependencies:** None

Ensure semantic mismatch triage can fail or pause accumulation but cannot modify canonicalization behavior or exemption lists.

**Details:**

The accumulation artifact should classify mismatches as unexplained divergence or triage-required benign normalization candidates. Do not update `TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION`, auto-extend exemptions, or write normalization lists from the accumulation job.

### 158.6. Re-run Task 157 and 159 standing gates

**Status:** pending
**Dependencies:** None

Verify new post-merge shadow accumulation does not weaken read-only classification, target selection, classifier delegation, or apply/write isolation invariants.

**Details:**

Name and run the standing gates covering agent-facing apply/write path isolation, `target_dir` as the sole Aegis MCP target selector, degraded classification delegated to the main classifier, single-gated-caller invariants, and read-only classifier invariants.

### 158.7. Refuse shadow evidence on invalid Taskmaster authority

**Status:** pending
**Dependencies:** None

Ensure shadow accumulation refuses or marks valid_for_shadow=false when Taskmaster authority is malformed or invalid, so invalid tasks.json cannot be normalized into a false would_apply ledger entry.

**Details:**

Scope: compose the Task 156 single-authority invariant into the Task 158 shadow path. Add malformed-tasks.json coverage proving validate_sacrificial_taskmaster_done_cascade or the accumulation entry point does not emit would_apply when TaskmasterState would be invalid/unreadable. The result must be refused, triage-required, or valid_for_shadow=false, and no candidate may enter the accumulation ledger from invalid authority. Keep this shadow-only; live apply TaskmasterState gating remains an enablement prerequisite outside Task 158.
