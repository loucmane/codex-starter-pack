# Task ID: 185

**Title:** Archive terminalized observation work-tracking folders

**Status:** done

**Dependencies:** 184 ✓

**Priority:** high

**Description:** A completed Aegis observation can remain under docs/ai/work-tracking/active as an *-ACTIVE folder. When a later task kickoff creates a new ACTIVE folder, readiness blocks mutations with expected exactly one ACTIVE work-tracking folder. Completed observations must not poison the next task envelope.

**Details:**

Teach Aegis to treat completed observations as terminal across work-tracking surfaces. Prefer archiving the completed observation ACTIVE folder to an archive/completed location during observation stop/idempotent stop or via a safe repair action. Readiness should not count terminal completed-observation folders as conflicting with the current task. Preserve evidence and reports; do not delete observation artifacts. Regression coverage: completed observation folder remains active, new task kickoff creates a second ACTIVE folder, repair or terminalization leaves exactly one active task folder and mutations can proceed. Validate with focused test_aegis_installer coverage plus the Aegis MCP/pretooluse regression suite.

**Test Strategy:**

No test strategy provided.
