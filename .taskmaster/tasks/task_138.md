# Task ID: 138

**Title:** Short-circuit read-only commands before readiness

**Status:** pending

**Dependencies:** 137

**Priority:** high

**Description:** Classify read-only inspection and test commands before running full readiness, allowing harmless observation and verification without task-state blocking.

**Details:**

Agent-runtime-first rationale: blocking inspection makes agents blind and increases bad mutation risk; read-only commands do not need task attribution. Acceptance: known read-only Bash commands such as ls, cat, sed, rg, git diff/status/show, task-master next/show/list, and non-writing test commands bypass readiness; commands with redirects, writes, generated outputs, status changes, or unknown shell features remain mutation-gated; tests cover classifier positives/negatives and prove readiness is not invoked for read-only payloads.

**Test Strategy:**

No test strategy provided.
