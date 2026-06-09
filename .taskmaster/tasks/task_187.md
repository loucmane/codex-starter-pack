# Task ID: 187

**Title:** Archive closed task trackers and scope closeout repair

**Status:** done

**Dependencies:** 186 ✓

**Priority:** high

**Description:** HP-Coach exposed two closeout lifecycle bugs after #53 closeout and #73 kickoff: the closed task envelope's work-tracking folder stayed under active, and workflow.normalize_completed_closeout grafted the old #53 closeout metadata onto the fresh #73 current-work payload.

**Details:**

On successful task closeout, archive the just-closed task work-tracking folder from docs/ai/work-tracking/active/...-ACTIVE to docs/ai/work-tracking/archive/...-COMPLETED and update current-work/report paths. Add or adjust repair so stale completed task folders can be archived only when backed by matching closeout evidence, not blindly. Scope workflow.normalize_completed_closeout so it only applies when the closeout report's current_work task id and work-tracking path match the current-work payload; never mark a different active task completed from stale closeout evidence. Add regressions for #53 closeout then #73 kickoff: repair must not corrupt #73, must archive #53 safely, and leave exactly one active folder.

**Test Strategy:**

No test strategy provided.
