# Task ID: 183

**Title:** Allow safe Aegis repair while readiness is blocked

**Status:** done

**Dependencies:** 182 ✓

**Priority:** high

**Description:** Aegis PreToolUse must allow doctor-prescribed safe repair actions when readiness is BLOCKED, so completed observation or scaffold repair states can recover without human out-of-band commands.

**Details:**

Fix the gate contradiction where doctor reports a safe repair but both CLI and MCP aegis repair --apply are blocked by readiness. Allow project-confined aegis repair apply paths through the PreToolUse gate while readiness is BLOCKED, restricted to Aegis repair surfaces and existing safe-repair validation. Preserve blocking for closeout, kickoff, Taskmaster mutations, arbitrary Bash writes, and out-of-project target dirs. Cover both CLI and MCP repair apply forms in regression tests.

**Test Strategy:**

No test strategy provided.
