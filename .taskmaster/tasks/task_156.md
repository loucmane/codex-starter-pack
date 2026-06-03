# Task ID: 156

**Title:** Make Taskmaster the single task authority for Aegis surfaces

**Status:** pending

**Dependencies:** 155

**Priority:** high

**Description:** When Taskmaster is present, Aegis task-selection surfaces must derive from Taskmaster and must not present a competing heuristic next-task verdict.

**Details:**

Scope: remove the live dual-authority drift vector observed in the HPFetcher Claude acceptance test. With .taskmaster/tasks/tasks.json present and valid, Aegis next, inspect, status, doctor, and reconcile must either surface Taskmaster's authoritative next/current task data or remain silent about task selection; they must not print or return an independent heuristic task number that can disagree with Taskmaster. Keep the existing Aegis heuristic only for Taskmaster-absent projects. Acceptance: seed a fixture where Aegis heuristic would choose a different task than Taskmaster; assert every relevant Aegis surface presents only Taskmaster's answer or no task-selection verdict. Add regression coverage that Taskmaster-absent projects still use the local heuristic. No source edits, workflow state mutation, or apply behavior changes beyond task-authority reporting.
<info added on 2026-06-03T17:13:21.925Z>
Refinement: treat Taskmaster presence as path-existence based, not parse-success based. In scripts/_aegis_installer.py, and the mirrored aegis_foundation/assets/scripts/_aegis_installer.py, split the current _read_json/_taskmaster_available_task behavior so .taskmaster/tasks/tasks.json missing is the only condition that permits Aegis local heuristic/local task fallback. If TASKMASTER_TASKS_REL exists but cannot be read as valid Taskmaster data, including JSON decode failure, non-object payload, malformed task containers, invalid task ids/status shape, or unreadable file errors, return a distinct Taskmaster-present-invalid state instead of None-as-absent. Aegis next_action, inspect_project/status, doctor, reconcile, and start_local_work must surface that state with source .taskmaster/tasks/tasks.json, reason/category, repair guidance such as inspect/fix tasks.json then run task-master validate-dependencies or python3 scripts/codex-task taskmaster health, and no suggested local task id, no aegis.start recommendation, no local task allocation, and no competing heuristic task-selection verdict. Reconcile should preserve the existing read-only/no-mutation guarantee while reporting Taskmaster as present but invalid/unreadable rather than available false when tasks.json is malformed. Add regression tests in tests/meta_workflow_guard/test_aegis_installer.py for corrupt, malformed, non-object, empty/invalid Taskmaster payloads across next_action, start_local_work, doctor/status/inspect, and reconcile; update the existing malformed reconcile test expectation so present-but-invalid does not collapse to Taskmaster absent. Ensure Taskmaster-absent fixtures still exercise the existing Aegis local heuristic via AEGIS_LOCAL_TASKS_REL.
</info added on 2026-06-03T17:13:21.925Z>

**Test Strategy:**

No test strategy provided.
