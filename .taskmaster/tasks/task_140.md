# Task ID: 140

**Title:** Add degraded-event breadcrumb and closeout enforcement

**Status:** done

**Dependencies:** 137 ✓

**Priority:** high

**Description:** Introduce a narrow audited degraded mode for gate infrastructure failure on non-destructive actions, with closeout and doctor visibility.

**Details:**

Agent-runtime-first rationale: agents need a sanctioned recovery path when Aegis infrastructure itself fails, but unsafe actions must still fail closed. Acceptance: gate infrastructure crashes on non-destructive actions write tamper-evident degraded event evidence and allow only the permitted action class; protected/destructive/workflow-state actions still fail closed; doctor reports degraded events; closeout refuses completion until degraded events are acknowledged or resolved; tests cover breadcrumb schema, closeout failure, doctor reporting, and mandatory fail-closed classes.

**Test Strategy:**

No test strategy provided.
