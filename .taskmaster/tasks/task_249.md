# Task ID: 249

**Title:** Fix pre-adapter Codex manifest update migration

**Status:** in-progress

**Dependencies:** 248 ✓

**Priority:** high

**Description:** Make Aegis update safely migrate existing Codex-enabled projects whose pre-adapter manifest lacks managed .codex/hooks.json, without weakening strict validation or overwriting divergent operator hook files.

**Details:**

Reproduce the Blog rollout failure where update preview succeeds but update --apply calls runtime_update first and validates the old manifest against the new schema before installer migration. Reorder or stage validation so legacy installed manifests may pass only through the supported migration path, while final installed state must satisfy the current schema. Preserve manual-review refusal for divergent .codex/hooks.json; absent or semantically identical hook files remain safely creatable/adoptable. Add regression fixtures for pre-adapter Codex-only and multi-agent manifests, preview refusal on divergent hooks, successful apply when the conflict is explicitly absent/resolved, installer idempotence, current-schema final verification, source/package parity, and no regression to runtime update safety.

**Test Strategy:**

No test strategy provided.
