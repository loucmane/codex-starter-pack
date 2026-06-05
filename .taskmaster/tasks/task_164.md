# Task ID: 164

**Title:** Wire shadow precision CI toolchain staleness to frozen baseline

**Status:** done

**Dependencies:** 162 ✓

**Priority:** high

**Description:** Make the Task 162 shadow precision corpus CI artifact compare current toolchain evidence against a frozen validated baseline instead of self-comparing captured evidence, so toolchain drift suppresses precision metrics and fails the gate at the CI integration point before any enablement work.

**Details:**

Scope: close the Task 162 F1 follow-up from adversarial review. The precision corpus unit test already proves mismatched toolchains mark the corpus stale, emit no metrics, and fail the gate; the CI step currently passes only capture_taskmaster_toolchain_evidence(os.environ), which self-compares and makes the integration staleness guard dormant. Add a frozen/pinned validated toolchain baseline or equivalent expected-version assertion for the CI precision corpus path, compare current evidence against it, and fail the CI artifact when package/version/source/provisioning lock/Node/Python/runner binding fields drift. Keep the artifact under RUNNER_TEMP and wrapped in the whole-tree side-effect oracle. Non-goals: no apply, no enable, no MCP/CLI apply surface, no Taskmaster status mutation against the governed repo, no broadening beyond merged_but_not_done/git_ancestor.

**Test Strategy:**

No test strategy provided.
