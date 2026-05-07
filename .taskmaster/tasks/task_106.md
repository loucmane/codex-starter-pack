# Task ID: 106

**Title:** Smoke Test Claude Runtime Adapter In Harness

**Status:** done

**Dependencies:** 103 ✓, 105 ✓

**Priority:** high

**Description:** Real-world Claude Code smoke test for the Task 103/105 runtime adapter. Intentionally prioritize this validation ahead of Task 10 to confirm Claude is mechanically gated in the actual harness before continuing normal implementation work.

**Details:**

Create a dedicated branch and run a two-phase smoke test. Phase 1 starts with Taskmaster task/branch state but no sessions/current, plans/current, or ACTIVE work-tracking folder; a fresh Claude session should be able to inspect but should be blocked by PreToolUse/readiness from hookable persistent mutations. Phase 2 scaffolds the normal workflow state and verifies that Claude can perform allowed mutations only after readiness is READY while still blocking protected Codex-owned paths, Bash bypasses, and mutating MCP tools when appropriate. Capture findings, decisions, exact prompts, results, and evidence in normal work tracking after scaffold.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 106.1. Cold-session block test before workflow scaffold

**Status:** done  
**Dependencies:** None  

Run a fresh Claude session on the Task 106 branch before sessions/current, plans/current, or ACTIVE work tracking exist.

**Details:**

Expected: read-only inspection is allowed; hookable persistent mutations through file tools, mutating Bash, mutating MCP, and protected paths are blocked by readiness or the runtime gate. Capture exact Claude prompts and outcomes after scaffold.

### 106.2. Ready-state allowed and protected-path tests after scaffold

**Status:** done  
**Dependencies:** None  

Scaffold normal Task 106 workflow state, then rerun Claude with readiness READY.

**Details:**

Expected: allowed mutations inside Claude-owned/test-safe paths work only after scaffold; protected Codex-owned paths, Bash bypasses, and unsafe MCP mutations remain blocked. Capture exact prompts, outputs, and evidence.

### 106.3. Document smoke-test evidence and adapter follow-ups

**Status:** done  
**Dependencies:** None  

Record smoke-test results, limitations, and any follow-up adapter changes.

**Details:**

After both phases, scaffold/update work tracking with prompts, results, findings, decisions, and verification evidence. If Claude bypasses a hookable mutation, create a follow-up or fix under this task before closing.
