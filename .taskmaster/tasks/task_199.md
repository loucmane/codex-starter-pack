# Task ID: 199

**Title:** Aegis mode lattice and micro-mode spec

**Status:** in-progress

**Dependencies:** 194 ✓

**Priority:** medium

**Description:** Define Aegis lifecycle modes and their policy boundaries as a coherent state model.

**Details:**

Write and validate a mode lattice covering observe, implement, delivery, strict, recovery, and touch/micro-mode. For each mode define allowed action classes, boundary gates, evidence requirements, transition rules, current-work/state representation, and how natural prompts such as continue/ship/fix bookkeeping route. Include maintenance micro-mode for one-line status/report/bookkeeping updates without pretending to start product work, and specify how modes compose with future worktree/multi-agent envelopes. Acceptance should be a spec plus tests or fixtures proving next_action/readiness guidance maps common states to the intended mode.

**Test Strategy:**

No test strategy provided.
