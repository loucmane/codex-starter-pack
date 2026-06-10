# Task ID: 196

**Title:** Aegis durable delivery evidence report

**Status:** cancelled

**Dependencies:** 194 ✓

**Priority:** high

**Description:** Record post-closeout delivery actions and explicit human approvals as durable evidence artifacts.

**Details:**

Extend the delivery phase introduced by #194 with a content-addressed deliver-report.json (or equivalent) that records push, PR creation, CI/check state, ready-for-review, explicit merge approval, merge command, PR URL/number, mergedAt, approver identity/source, and failure/cleanup outcomes. HP-Coach #73 exposed the current audit inversion: low-stakes edits had dense S:W:H:E entries while the merge approval existed only in chat. Preserve explicit-approval policy and keep merge commands out of copyable repairs until approval is recorded. Acceptance should prove a fresh agent can reconstruct the full push->PR->CI->approval->merge path without the chat transcript.

**Test Strategy:**

No test strategy provided.
