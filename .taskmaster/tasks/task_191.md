# Task ID: 191

**Title:** Reduce read-only verification tracking tax

**Status:** pending

**Dependencies:** 189, 190

**Priority:** medium

**Description:** Make natural continuation flows less noisy by avoiding pending-tracking churn for known read-only inspection, verification, and browser-observation actions.

**Details:**

Improve command/tool classification so read-only Taskmaster queries, git/status inspection, grep/list/cat/sed style reads, typecheck/lint verification commands, localhost probes, and browser screenshot/snapshot calls do not create unnecessary pending tracking when they do not mutate persistent project state. Preserve strict tracking for source edits, Taskmaster writes, git mutations, repair/apply/closeout, generated file writes, and artifact cleanup. Consider a batch evidence command for runtime verification passes. Add tests showing common continue/verify flows stay pending-clean while mutations are still tracked and stop-gated.

**Test Strategy:**

No test strategy provided.
