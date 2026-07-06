# Task ID: 227

**Title:** Wire capsule freshness boundary triggers

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Wire capsule compile reasons into real lifecycle boundaries so long-running sessions refresh the canonical capsule after delivery, task-status, verification, pre-delivery, and orientation events without per-mutation ceremony.

**Details:**

Build on TM 226 / PR #244. Keep this additive: no PR-3 narration checkpoints, no surface retirement, no blocking gates. Add focused tests for boundary-triggered compile reasons and preserve read-only brief status behavior.

**Test Strategy:**

No test strategy provided.
