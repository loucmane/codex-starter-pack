# Task ID: 202

**Title:** Capsule PR-1a: passive ledger core (store, schema, redaction)

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Phase 1 of the Session Zero Capsule program per docs/aegis/AEGIS_CAPSULE_SPEC.md. Covers: (1) committing the capsule spec atomically with the AEGIS_VNEXT_PROGRAM.md pointer/G3 update; (2) wiring the nine-PR backlog and reconciling tasks 194-201; (3) PR-1a per spec section 2: assets ledger_lib.py (stdlib-only) with SQLite open/append/read at the XDG state-dir store path, WAL+busy_timeout, redaction helpers, backend-agnostic reader with JSONL fallback, docs/aegis/LEDGER_SCHEMA.md, aegis ledger path + status surfacing, unit tests. No hook registration; zero behavior change.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
