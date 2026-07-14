# Task ID: 250

**Title:** Stabilize evidence-gated autonomous delivery executor

**Status:** done

**Dependencies:** 247 ✓

**Priority:** high

**Description:** Fix the trusted autonomous-delivery self-gating race reproduced by PR #276, where all required exact-head evidence is green but the non-required merge executor keeps GitHub mergeable_state unstable and can never obtain a fresh allow decision.

**Details:**

Preserve fail-closed semantics and the rule that provisional never authorizes merge. Model required-context state directly from trusted GitHub evidence so the executor can distinguish its own in-progress or prior non-required check from genuinely failing required evidence. Add a sanitized PR #276 replay fixture, policy and workflow contract regressions, adversarial cases for real required-check failures and head/base drift, bounded retries, and a live ordinary canary. Do not weaken attended-path, review-thread, file-inventory, exact-head, same-repo, or protected-path gates. After the fix merges, retrigger PR #276 through the normal evidence-gated path and prove exact-merge-SHA post-merge checks.

**Test Strategy:**

No test strategy provided.
