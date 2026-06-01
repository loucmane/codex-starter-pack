# Task ID: 137

**Title:** Block unclassifiable mutating payloads

**Status:** done

**Dependencies:** 136 ✓

**Priority:** high

**Description:** Close the fail-open path where a non-empty hook payload that cannot be parsed/classified is allowed to proceed.

**Details:**

Agent-runtime-first rationale: an agent must not be allowed to mutate a project when Aegis cannot render a verdict on the action. Acceptance: non-empty malformed/unknown PreToolUse payloads for mutating-capable tools fail closed; empty payloads or known read-only payloads keep existing behavior; structured denial includes a remediation message and does not crash the hook; tests cover malformed JSON, missing tool fields, unknown MCP mutation payloads, and known safe read-only cases.

**Test Strategy:**

No test strategy provided.
