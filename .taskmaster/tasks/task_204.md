# Task ID: 204

**Title:** Capsule PR-1c: gate-decisions dual-write

**Status:** pending

**Dependencies:** 203

**Priority:** high

**Description:** Spec: AEGIS_CAPSULE_SPEC.md section 2 (gate-decisions migration, decided). Dual-write new advisory gate decisions to both the existing .aegis/reports/gate-decisions.jsonl and the ledger for one release; then freeze the JSONL read-only in place. Never migrate history. aegis enforce status and existing tests keep reading what they read today. Ties directly to the PR #199 advisory machinery (gate_block_or_record / append_gate_decision). Merge gate: old-vs-new parity on live decisions.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
