# Task ID: 189

**Title:** Add agent-ready continuation brief to aegis next

**Status:** pending

**Dependencies:** 188

**Priority:** high

**Description:** Extend aegis next so agents can translate short user intents into the next safe workflow action without bespoke prompts.

**Details:**

Add a machine-readable continuation brief to aegis next output with current task authority, workflow phase, continue_means text, next_safe_action, suggested commands, protected confirmation boundaries, artifact policy, and stop conditions. Cover common states including no current work, active implementation, dirty scoped files, verified but uncommitted work, committed but not closed out, closeout passed with Taskmaster not done, pending tracking, safe repair available, manual-review repair, observation ready, and observation completed. Add tests for the state table and concise CLI output suitable for agent consumption.

**Test Strategy:**

No test strategy provided.
