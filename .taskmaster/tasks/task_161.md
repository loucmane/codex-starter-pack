# Task ID: 161

**Title:** Review post-merge shadow evidence and pin Taskmaster state initialization contract

**Status:** pending

**Dependencies:** 160 ✓

**Priority:** high

**Description:** Ratify the first post-merge shadow accumulation run as operational evidence, separate operational evidence from precision evidence, and pin the pinned Taskmaster CLI state.json initialization behavior that keeps the Task 160 active-tag presence guard from becoming a false refusal.

**Details:**

Scope: inspect GitHub Actions run 26959807056 from merge commit ac2a8f13fc5aed9e9a30ebffbee12372fa47a6f8 and record it as operational post-merge shadow entry number 1 only if the artifact facts hold: post_merge_ci context, valid_for_shadow true, artifact-only accumulation under runner temp, executed false, mutated_live_repo false, candidate_count 0, would_apply 0, shadow_refused 0, and no unexplained divergence. Document that this run is evidentially empty for precision: real codex main is structurally candidate-free because Taskmaster tasks are done before merge, so empty real accumulation cannot be cited as precision evidence for enablement. Precision evidence must remain tied to the labeled corpus and cascade fixtures. Add a direct regression test for the pinned task-master-ai 0.43.1 CLI initialization behavior: freshly initialized .taskmaster/state.json must not introduce tag, currentTag, or branchTagMapping keys. Keep it skip-guarded when the CLI is unavailable, following the existing toolchain test pattern. Add or update documentation/schema notes so operational entries and precision observations are not conflated downstream. Non-goals: no apply, no enable, no MCP apply tool, no operator-local apply, no Taskmaster status mutation, no live write path, no in-repo shadow ledger. Acceptance criteria: run 26959807056 is captured in committed evidence as operational entry 1 with its exact partition and a no-precision-signal label; docs/tests prevent future enablement from citing empty real accumulation as zero-divergence precision; the pinned CLI state-init regression fails if tag/currentTag/branchTagMapping appear; existing Task 144-160 inertness and shadow tests remain green.

**Test Strategy:**

Add artifact parsing coverage for GitHub Actions run 26959807056 or a committed fixture derived from it, asserting post_merge_ci context, valid_for_shadow true, executed false, mutated_live_repo false, candidate_count 0, would_apply 0, shadow_refused 0, and no unexplained divergence. Add an isolated tempdir regression using the pinned task-master-ai 0.43.1 CLI that proves freshly initialized .taskmaster/state.json does not contain tag, currentTag, or branchTagMapping, skip-guarded when the CLI is unavailable. Keep or add a negative semantic validation test proving injected tag/currentTag still refuses. Run focused shadow and workflow tests plus Taskmaster health, work-tracking audit, codex guard validation, and git diff check.
