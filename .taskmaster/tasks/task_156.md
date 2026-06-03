# Task ID: 156

**Title:** Make Taskmaster the single task authority for Aegis surfaces

**Status:** pending

**Dependencies:** 155

**Priority:** high

**Description:** When Taskmaster is present, Aegis task-selection surfaces must derive from Taskmaster and must not present a competing heuristic next-task verdict.

**Details:**

Scope: remove the live dual-authority drift vector observed in the HPFetcher Claude acceptance test. With .taskmaster/tasks/tasks.json present and valid, Aegis next, inspect, status, doctor, and reconcile must either surface Taskmaster's authoritative next/current task data or remain silent about task selection; they must not print or return an independent heuristic task number that can disagree with Taskmaster. Keep the existing Aegis heuristic only for Taskmaster-absent projects. Acceptance: seed a fixture where Aegis heuristic would choose a different task than Taskmaster; assert every relevant Aegis surface presents only Taskmaster's answer or no task-selection verdict. Add regression coverage that Taskmaster-absent projects still use the local heuristic. No source edits, workflow state mutation, or apply behavior changes beyond task-authority reporting.

**Test Strategy:**

No test strategy provided.
