# Task ID: 166

**Title:** Gate live apply on Taskmaster authority and freshness

**Status:** pending

**Dependencies:** 165

**Priority:** high

**Description:** Close D2 and D5 by making the live apply runtime delegate to the authoritative Taskmaster state validator and re-derive merged_but_not_done/git_ancestor at apply time.

**Details:**

Scope: the live apply runtime must call the same authoritative Taskmaster state validator used by reconcile/shadow, not a local reimplementation. Absent, malformed, invalid, duplicate-ID, or empty Taskmaster authority must refuse before sacrificial clone or mutation work. At apply time, re-read live Taskmaster and git state and refuse if the candidate is already done, missing, status-changed, not merged, not git_ancestor, or outside merged_but_not_done/git_ancestor. Freshness reads must be hermetic/read-only: no git fetch, no state-touching Taskmaster command, no governed-repo mutation. Non-goals: no apply enablement, no new apply surface, no kill-switch enable path, no candidate-class broadening.

**Test Strategy:**

No test strategy provided.
