# Task ID: 190

**Title:** Support fresh-project PRD bootstrap continuation flow

**Status:** pending

**Dependencies:** 189

**Priority:** high

**Description:** Make Aegis work naturally in brand-new projects that start from no Taskmaster ledger, no current work, and a PRD-driven planning phase.

**Details:**

Define and implement a bootstrap state for fresh projects where Aegis is installed before Taskmaster has tasks. The flow should support task-master init when needed, PRD discovery or creation guidance, task-master parse-prd with explicit user approval, analyze-complexity and expansion guidance, and the first kickoff after tasks exist. The continuation contract must distinguish setup/planning mutations from product implementation and must never force fake task binding before the task ledger exists. Add aegis next brief states for no_taskmaster, taskmaster_empty, prd_available_not_parsed, prd_parsed_tasks_pending, and first_task_ready. Add tests against a temporary brand-new repo proving a short continue prompt can guide install, PRD parse readiness, task generation, and first-task kickoff boundaries without manual JSON edits or state corruption.

**Test Strategy:**

No test strategy provided.
