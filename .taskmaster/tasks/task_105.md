# Task ID: 105

**Title:** Validate and Harden Claude Runtime Adapter

**Status:** done

**Dependencies:** 103 ✓, 104 ✓

**Priority:** high

**Description:** Live validation and hardening follow-up for completed Task 103. Prioritize Claude adapter system behavior ahead of Task 10 by explicit user direction because multimodal agent enforcement is foundational for all later work.

**Details:**

Audit Task 103 outputs in the current repository state. Verify that CLAUDE.md, .claude runtime contract, readiness gate, PreToolUse dispatcher, path guard, Bash command guard, handoff nudge, commands, agents, settings, and tests still match the intended gated-runtime behavior after Task 104 and archive closeout. Fix stale permanent metadata such as runtime-contract references to draft or active Task 103 paths. Add or adjust focused tests only for real behavior gaps, especially cold-session zero-mutation, memory or MCP hookability labels, Bash mutation classification, and between-session behavior. Record every gap and decision in normal work tracking. Do not duplicate Task 103 implementation and do not edit Codex-owned surfaces unless explicitly scoped.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 105.1. Audit current Claude hook surface and runtime contract

**Status:** done  
**Dependencies:** None  

Compare completed Task 103 adapter against current Claude Code hook documentation and current repo state.

**Details:**

Review .claude/settings.json, runtime-contract.md, readiness, PreToolUse dispatcher, Bash guard, path guard, handoff nudge, commands, agents, Task 103 archived artifacts, and official Claude Code hook events. Produce work-tracking design notes identifying stale metadata, untested hook surfaces, MCP matcher coverage, config-change risk, slash-command expansion risk, subagent/task lifecycle hooks, memory hookability labels, and any policy-only surfaces. Update runtime contract only after findings are recorded.

### 105.2. Harden hook dispatcher and protected mutation gates

**Status:** done  
**Dependencies:** None  

Implement only proven hardening gaps from the audit so Claude is mechanically blocked on hookable mutation paths.

**Details:**

Apply focused changes to Claude-owned adapter files only. Candidate areas include adding MCP mutating tool matchers or wildcard routing where safe, protecting .claude hook configuration from weakening, improving Bash mutation classification, adding UserPromptExpansion or ConfigChange checks if supported by current docs and tests, and keeping readiness as the first mutation gate. Do not weaken read-only inspection. Do not modify Codex-owned surfaces unless a separate Codex-led scope is created.

### 105.3. Prove cold-session zero-mutation and hookability behavior

**Status:** done  
**Dependencies:** None  

Add or update tests and evidence so every enforcement claim is backed by behavior.

**Details:**

Run focused pytest coverage for readiness, PreToolUse gates, Bash guard, contract files, and any new MCP, ConfigChange, UserPromptExpansion, or lifecycle hook logic added in this task. Tests must exercise both blocked and allowed cases in isolated temp repos where appropriate. Every mutation surface must be labeled verified-hookable, ci-detectable, or policy-only with a documented limitation. No tests may be changed merely to pass without preserving the intended behavior.

### 105.4. Finalize evidence, handoff, and Claude-system continuity

**Status:** done  
**Dependencies:** None  

Close Task 105 with current docs, work tracking, Taskmaster status, and verification evidence.

**Details:**

Capture plan sync, work-tracking audit, codex guard, diff-check, pre-commit, focused pytest, and readiness evidence. Update TRACKER, FINDINGS, DECISIONS, IMPLEMENTATION, CHANGELOG, HANDOFF, and MEMORY-REFS if memory references are used. Ensure the permanent runtime contract reflects current completed state and next-step limitations, not stale Task 103 active paths. Prepare GAC and PR description.
