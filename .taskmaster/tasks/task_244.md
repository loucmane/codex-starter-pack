# Task ID: 244

**Title:** Make Upstream Source Closeout State Derivable

**Status:** done

**Dependencies:** 236 ✓, 235 ✓

**Priority:** high

**Description:** Allow the Aegis source repository to archive completed work tracking without retaining a stale ACTIVE folder or fabricating installed-target current-work state.

**Details:**

Implement the source-checkout lifecycle gap discovered during Task 236 closeout. When no ACTIVE folder exists and the upstream source checkout intentionally has no installed .aegis/state/current-work.json, derive the completed tracker only from fail-closed repository evidence such as a task-bearing branch, a done Taskmaster task, an unambiguous matching -COMPLETED archive, and tracker/task identity parity. Reject ambiguous archives, non-done tasks, mismatched task IDs, paths outside the archive root, and installed targets that should use current-work state. Keep installed-target behavior unchanged. Add focused guard, readiness, kickoff, archive, CI-clean-checkout, and next-task handoff tests. Dogfood by archiving a completed upstream planning task with no fabricated runtime state and proving guard passes. Document rollback to the current sole-completed-ACTIVE compatibility state.

**Test Strategy:**

No test strategy provided.
