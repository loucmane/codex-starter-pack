# Task ID: 159

**Title:** Add structural backstops before shadow accumulation

**Status:** done

**Dependencies:** 157 ✓

**Priority:** high

**Description:** Add test-only structural backstops that make Task 157's target-selector confinement and degraded classifier delegation drift-proof before Task 158 shadow accumulation.

**Details:**

Scope: no runtime behavior changes. Add a schema/signature scan test asserting every agent-supplied Aegis MCP tool directory selector uses target_dir; fail CI if a future tool introduces another root/path selector such as root, cwd, project_dir, or repo_dir without adding confinement. Add a structural degraded-classifier test asserting degraded Bash/MCP classification delegates to the main classifier path and has no independent safe-command allowlist. Acceptance: tests fail on simulated alternate path selector and simulated degraded refork, live and packaged gate hooks remain byte-identical, all focused gate/installer/MCP tests pass, and Task 158 remains blocked on this task until merged.

**Test Strategy:**

No test strategy provided.
