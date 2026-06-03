# Task ID: 158

**Title:** Add post-merge shadow accumulation with mismatch triage

**Status:** pending

**Dependencies:** 157

**Priority:** high

**Description:** Run post-merge shadow/would-apply accumulation on the hardened validator, with explicit mismatch triage for semantic canonicalization coverage before any enablement work.

**Details:**

Scope: after semantic validation and adapter hardening, run shadow apply decisions under the real post-merge trigger and accumulate evidence over real merge events without enabling live apply. The accumulation report must distinguish apply-decision divergence from canonicalization completeness findings. Every semantic mismatch must be triaged as real divergence or unobserved benign normalization. Benign normalization updates may only extend the validator through a specific content-preserving transform plus paired negative tests, never through broad category exemptions. Report coverage as zero unexplained divergences over M merges, with K benign normalizations triaged and added deliberately. Validate the approved post-merge context, preserve no live apply/no enable/no agent-reachable apply path, and keep prior 144-157 invariants green. Acceptance: shadow accumulation runs in the post-merge environment, stores auditable would-apply evidence, emits mismatch-triage status, fails on unexplained divergence, and does not mutate Taskmaster, Aegis state, git refs, or project source outside explicitly declared shadow artifacts.

**Test Strategy:**

No test strategy provided.
