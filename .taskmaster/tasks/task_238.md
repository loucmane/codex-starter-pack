# Task ID: 238

**Title:** Enforce Universal Context Budgets Across Aegis Commands

**Status:** in-progress

**Dependencies:** 236 ✓

**Priority:** high

**Description:** Create a shared rendering contract that keeps default Aegis command output within an agent-safe context budget while preserving complete details in report artifacts.

**Details:**

Implement roadmap workstream C2 for status, next, doctor, verify, update, witness, replay, and closeout failures. Default text and JSON output must remain at or below 60 lines and 8 KiB, report exact category counts, show bounded samples and truncation markers, provide one copyable next action, and link full-detail artifacts. Add explicit bounded verbose and intentional full-detail modes. Cover 0, 10, 3500, and 100000 event fixtures; assert byte and line budgets; prove CI failures remain bounded while artifacts retain complete detail; and dogfood HP-Fetcher pending-event status as a one-screen result. Do not delete or drain pending events. Record latency, output size, governance-call, and rollback metrics.

**Test Strategy:**

No test strategy provided.
