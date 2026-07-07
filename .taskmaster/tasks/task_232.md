# Task ID: 232

**Title:** Clarify update workflow-state evidence

**Status:** done

**Dependencies:** 231 ✓

**Priority:** medium

**Description:** Expose strict workflow-state verification failures in Aegis project update reports as workflow_state_evidence so stale current-work or pending-tracking residue is clearly evidence, not a failed managed refresh.

**Details:**

Keep the change scoped to the project_update report schema, docs, and tests. Add a workflow_state_evidence object derived from strict verification results; include only workflow-state residue gates such as workflow.* and mutation.pending_tracking_empty. Preserve project_update status semantics: managed refreshes still pass when runtime/install/capsule operations are safe and successful, even when strict workflow-state evidence is present. Do not implement fleet update.

**Test Strategy:**

No test strategy provided.
