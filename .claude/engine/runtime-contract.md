# Claude Runtime Contract

## Status
Draft for Taskmaster Task 103, subtask 103.1.

## Principle
Claude must run as a gated participant in the portable Codex foundation. The adapter is not considered complete because a document tells Claude what to do; it is complete only when hooks, scripts, tests, and evidence make the expected behavior mechanical where the tool surface is hookable.

## Required State Before Claude Mutations
Claude may perform persistent mutations only when all required pointers align:
- current branch contains the active Taskmaster task ID;
- Taskmaster parent task is `in-progress`;
- `sessions/current` points to the active session;
- `plans/current` points to the active plan;
- exactly one ACTIVE work-tracking folder exists for the task;
- the plan and tracker agree on required plan-step checkboxes;
- readiness returns `READY`.

## Gate Chain
1. PreToolUse invokes `.claude/scripts/pretooluse-gate.sh` for mutation-capable tools.
2. The gate invokes `.claude/scripts/readiness.sh --quick`.
3. `BLOCKED` readiness refuses hookable persistent mutation regardless of target.
4. `READY` readiness dispatches target-specific checks:
   - path guard for Codex-owned or workflow-critical paths;
   - Bash command guard for obvious write-surface bypasses;
   - stop/handoff guard for untracked audit-trail gaps.
5. Every guard emits an actionable remediation message instead of a silent warning.

## Protected Codex-Owned Paths
Claude-owned Task 103 work must not modify these paths:
- `CODEX.md`
- `templates/**`
- `scripts/codex-*`
- `scripts/template-*`
- `.codex/**`

If a shared change is needed, document the deferral in Task 103 `DECISIONS.md` and create a Codex-led follow-up task.

## Evidence Standard
Each enforcement claim must be one of:
- backed by a focused passing test;
- backed by captured command evidence under the active work-tracking report folder;
- labeled policy-only with limitations documented in `DECISIONS.md` and `HANDOFF.md`.

Memories, including Serena and Claude private memory, are continuity artifacts only. They are not workflow evidence unless referenced from the active tracker/handoff and supported by the normal guard evidence.

## Multimodal Scope
The runtime contract covers more than text-file editing. It must account for:
- Claude file tools;
- Bash commands;
- Taskmaster CLI and MCP tools;
- Serena memory file and MCP writes;
- Git and GitHub operations;
- sub-agent behavior;
- future agent/tool surfaces that can perform persistent mutations.

## Current Task References
- Taskmaster: `103`
- Branch: `feat/task-103-claude-runtime-adapter`
- Active tracker: `docs/ai/work-tracking/active/20260506-task103-claude-runtime-adapter-ACTIVE/TRACKER.md`
- Scope contract: `docs/ai/work-tracking/active/20260506-task103-claude-runtime-adapter-ACTIVE/designs/claude-runtime-file-contract.md`
- Mutation taxonomy: `docs/ai/work-tracking/active/20260506-task103-claude-runtime-adapter-ACTIVE/designs/mutation-taxonomy.md`
