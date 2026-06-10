# Task ID: 206

**Title:** Capsule PR-2a: computed aegis brief

**Status:** done

**Dependencies:** 205 ✓

**Priority:** high

**Description:** Spec: AEGIS_CAPSULE_SPEC.md sections 3, 3.1, 3.2. aegis brief compile+print with ALL computed-stratum fields (capsule_meta, repo_pose, delivery_state, verification_ledger with explicit absence reporting, task_truth with claimed-done-vs-shipped cross-check, governance, drift_sentinel, repo_hygiene), recomputed/revalidated at read time — any field failing revalidation renders STALE-recheck, never the cached value. Drift sentinel v1: exactly the 5 deterministic checks, no LLM; sentinel must prove it ran (N attempted / M parsed / K drift; parse failure is itself drift); seeded canary asset at .aegis/capsule/canary.md must always flag or the capsule reports the sentinel broken. risk_register seeding consumed once from .aegis/capsule/risk-seed.json (values per-repo). No injection in this PR. Merge gate: brief output matches independently-checked HP-Coach reality.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
