# Task ID: 158

**Title:** Add post-merge shadow accumulation with mismatch triage

**Status:** pending

**Dependencies:** 157

**Priority:** high

**Description:** Run post-merge shadow/would-apply accumulation on the hardened validator, with explicit mismatch triage for semantic canonicalization coverage before any enablement work.

**Details:**

Scope: after semantic validation and adapter hardening, run shadow apply decisions under the real post-merge trigger and accumulate evidence over real merge events without enabling live apply. The accumulation report must distinguish apply-decision divergence from canonicalization completeness findings. Every semantic mismatch must be triaged as real divergence or unobserved benign normalization. Benign normalization updates may only extend the validator through a specific content-preserving transform plus paired negative tests, never through broad category exemptions. Report coverage as zero unexplained divergences over M merges, with K benign normalizations triaged and added deliberately. Validate the approved post-merge context, preserve no live apply/no enable/no agent-reachable apply path, and keep prior 144-157 invariants green. Acceptance: shadow accumulation runs in the post-merge environment, stores auditable would-apply evidence, emits mismatch-triage status, fails on unexplained divergence, and does not mutate Taskmaster, Aegis state, git refs, or project source outside explicitly declared shadow artifacts.
<info added on 2026-06-03T17:17:06.335Z>
Add CI side-effect-oracle coverage around the post-merge shadow accumulation job because GitHub Actions may have repository write credentials in some contexts. Reuse tests/meta_workflow_guard/reconcile_side_effect_oracle.py snapshot_whole_tree/assert_matches patterns and the existing aegis_foundation/reconcile_shadow_apply.py repo_file_write_policy contract to prove CI-mode shadow accumulation mutates zero governed-repo files and produces only declared reports/ci upload artifacts such as reconcile-shadow-context-proof.json, reconcile-shadow-cascade-validation.json, and the new accumulation/triage artifact. Add tests beside tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py and tests/meta_workflow_guard/test_ci_workflows.py that fail on any .taskmaster, .aegis state, docs/ai/work-tracking, plans, sessions, git ref, or source-file delta during the CI accumulation path. Mismatch triage is reporting-only: the accumulation job may flag mismatches, mark the run paused/failed, and emit triage-required evidence, but it must never modify TASKMASTER_SEMANTIC_CANONICALIZATION_VERSION behavior, auto-extend canonicalization exemptions, or write any exempt/normalization list. Any benign-normalization acceptance must land as a separate reviewed code change to validate_taskmaster_apply_semantic_delta or its narrow canonicalization helpers in aegis_foundation/reconcile_shadow_apply.py, with a specific content-preserving transform and paired negative tests proving adjacent semantic drift is still rejected. Count K benign normalizations only after those reviewed validator updates are merged; the promotion gate remains zero unexplained divergences across the accumulated post-merge sample.
</info added on 2026-06-03T17:17:06.335Z>

**Test Strategy:**

No test strategy provided.
