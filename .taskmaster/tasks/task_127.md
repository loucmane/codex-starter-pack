# Task ID: 127

**Title:** Add Aegis handoff auto-repair flow

**Status:** pending

**Dependencies:** 125 ✓

**Priority:** medium

**Description:** Improve Aegis closeout handoff repair so agents do not have to manually rewrite placeholder handoff sections after closeout_ready identifies content gaps.

**Details:**

Add a deterministic repair surface, such as aegis handoff repair or stronger closeout --update-handoff behavior, that can populate Current State, What Was Done, Implementation Evidence, Verification Evidence, Strict Verification Evidence, Current Issues, and Next Steps from current-work state, plan evidence, logged S:W:H:E events, verification report, and closeout_ready failures. Preserve strict closeout gates and do not weaken handoff requirements. Add CLI and MCP coverage, plus live-style fixture tests showing a placeholder handoff can be repaired without ad hoc manual editing.

**Test Strategy:**

No test strategy provided.
