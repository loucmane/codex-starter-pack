# Task ID: 167

**Title:** Correct apply-time oracle claims and log deep gate

**Status:** done

**Dependencies:** 166 ✓

**Priority:** high

**Description:** Close the shallow A1 documentation/operator-trust issue by correcting any claim that Task 145 verifies blast radius at mutation time, and record the deeper apply-time oracle as a future enablement prerequisite.

**Details:**

Scope: update preview/contract/operator-facing text so it does not claim the Task 145 side-effect oracle runs at mutation time if that oracle remains test-only. Add an explicit enablement-gate note that a separate future task must either wire a live apply-time side-effect oracle around mutation or keep the claim absent. Non-goals: do not implement the deep apply-time oracle in this task, do not enable apply, do not change runtime gates, do not add any apply surface.

**Test Strategy:**

No test strategy provided.
