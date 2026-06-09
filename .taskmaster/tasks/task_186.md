# Task ID: 186

**Title:** Archive orphaned observation ACTIVE folders by name

**Status:** done

**Dependencies:** 185 ✓

**Priority:** high

**Description:** HP-Coach still deadlocks after #192 when a stale completed observation folder remains under docs/ai/work-tracking/active but the observation metadata no longer points at it. Readiness counts the folder, while repair offers no action.

**Details:**

Extend Aegis repair to safely detect orphaned observation work-tracking folders directly by active folder naming, such as *-observe-*-ACTIVE, when they are not the current task work-tracking folder. Offer workflow.archive_completed_observation_work_tracking for that orphan even if current-work.json and observation-report.json do not reference it. Preserve evidence by moving to docs/ai/work-tracking/archive/...-COMPLETED, update observation-report paths only when they match, and keep the existing behavior that random stale task ACTIVE folders are not auto-archived. Add regression coverage for the HP-Coach shape: task #53 current work is active, a stale 20260608-observe...-ACTIVE folder exists, observation-report does not link it, repair preview offers archive, repair apply leaves only the task ACTIVE folder.

**Test Strategy:**

No test strategy provided.
