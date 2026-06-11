# Task ID: 213

**Title:** Per-session hashed capsule A/B assignment

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** Replace spec §7 calendar-day A/B assignment with deterministic per-session hashing: brief.json ab_assignment=session-hash makes the SessionStart hook decide capsule on/off from a hash of session_id (AEGIS_CAPSULE env still wins); session_begin records assignment mode; add 'aegis ab' to count genuine cold starts (source=startup) per arm against a fixed-n stopping rule (n>=15/arm) replacing the 2-week window; amend spec §7.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
