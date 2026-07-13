# Task ID: 247

**Title:** Fix Autonomous Delivery Self-Gating Race

**Status:** in-progress

**Dependencies:** 246 ✓

**Priority:** high

**Description:** Prevent the trusted evidence-gated delivery workflow from deferring an otherwise eligible PR solely because its own in-progress required check temporarily makes GitHub mergeability non-clean.

**Details:**

Reproduce PR #264 at exact head 77b786d2acfbb1b40ee3c39809d8e065f50ed87c against base 8bf1f1871ff259987fa1b8d66d875b1adaf8d99e: all external required workflows, witness, exact head, current base, complete inventory, zero review threads, and routine path classification passed, but ready-event attempts 29234285884 skipped merge while the evidence-gated delivery check itself was running; identical post-run evidence evaluated allow. Implement a trusted-base, fail-closed correction that recognizes only this self-owned transient blocker and still rejects real conflicts, stale base, pending or failed external required workflows, unresolved reviews, attended paths/labels, incomplete inventory, forks, head movement, and policy changes. Never execute candidate PR code or artifacts, never weaken branch protection, and preserve normal exact-head protected fallback. Add deterministic policy/workflow tests, a secret-free PR #264 replay fixture, current-vs-in-flight mergeability cases, and an ordinary canary proving unattended squash merge plus post-merge dispatch. Document rollback to the current clean-only rule.

**Test Strategy:**

No test strategy provided.
