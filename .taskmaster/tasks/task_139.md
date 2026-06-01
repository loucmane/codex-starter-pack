# Task ID: 139

**Title:** Protect workflow-owned surfaces from direct agent edits

**Status:** done

**Dependencies:** 137 ✓

**Priority:** high

**Description:** Prevent agents from forging Aegis readiness or evidence by directly editing workflow-owned state, while preserving sanctioned Aegis CLI/MCP mutation paths.

**Details:**

Agent-runtime-first rationale: sessions, plans, work-tracking, and .aegis state are authority surfaces; direct Edit/Write can forge in-progress state. Acceptance: direct agent Edit/Write/Bash mutations to .aegis state, sessions, plans, and active work-tracking are blocked unless routed through sanctioned Aegis handlers; sanctioned commands including aegis kickoff, aegis log, handoff repair, closeout, and plan sync continue to work and write structured evidence; tests prove direct edits are denied and real Aegis-owned flows do not self-deadlock.

**Test Strategy:**

No test strategy provided.
