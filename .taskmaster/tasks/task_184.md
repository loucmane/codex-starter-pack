# Task ID: 184

**Title:** Treat completed Aegis observations as terminal state

**Status:** done

**Dependencies:** 183 ✓

**Priority:** high

**Description:** Aegis readiness and next guidance must treat completed observation current-work as a terminal observation state, not as an active observation that needs observe stop again. Completed observations should not grant arbitrary mutation readiness on main; normal kickoff/task binding must still be required for mutations.

**Details:**

Fix the HP-Coach post-observation deadlock where doctor reports healthy observation_completed, but readiness blocks with 'observation current work is missing id, slug, or in-progress status' and next still suggests observe stop. Update readiness so completed observation current-work falls through to normal no-task/task-branch checks or emits terminal-state guidance instead of active-observation validation. Update next/status guidance so observe stop is suggested only for in-progress observations. Consider making observe stop idempotently report already_completed for completed observations if safe. Preserve behavior for in-progress observation, pending tracking, task work, and non-task branch mutation blocking. Add regression tests for completed observations on main and in-progress observations.

**Test Strategy:**

No test strategy provided.
