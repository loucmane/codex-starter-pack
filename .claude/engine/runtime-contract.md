# Claude Runtime Contract

## Status
Implemented by Taskmaster Task 103 and extended by later Aegis portability tasks. Task 103 delivered the initial readiness gate, PreToolUse dispatcher, Claude commands, agents, settings, and focused tests. Task 105 validated the contract against live Claude Code hook behavior. Task 115 adds portable PostToolUse/Stop tracking enforcement for Aegis-installed projects.

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
1. PreToolUse invokes `.claude/scripts/pretooluse-gate.sh` for mutation-capable file, Bash, and MCP tools.
2. The gate invokes `.claude/scripts/readiness.sh --quick`.
3. `BLOCKED` readiness refuses hookable persistent mutation regardless of target.
4. `READY` readiness dispatches target-specific checks:
   - path guard for Codex-owned or workflow-critical paths;
   - Bash command guard for obvious write-surface bypasses;
   - pending S:W:H:E tracking guard for previous unlogged mutations.
5. PostToolUse invokes `.claude/scripts/posttooluse-tracking.sh` after successful persistent mutations and records `.aegis/state/pending-tracking.json` when Aegis current work exists.
6. Stop invokes `.claude/scripts/tracking-stop-gate.sh` and refuses session stop while pending S:W:H:E tracking remains.
7. Every guard emits an actionable remediation message instead of a silent warning.

## Implemented Gate Components
- `.claude/scripts/readiness.sh` verifies branch, Taskmaster, session, plan, ACTIVE tracker, and plan/tracker alignment.
- `.claude/scripts/pretooluse-gate.sh` is the dispatcher registered for `Edit|Write|MultiEdit|NotebookEdit|Bash`.
- `.claude/scripts/posttooluse-tracking.sh` records pending S:W:H:E tracking after successful persistent mutations.
- `.claude/scripts/tracking-stop-gate.sh` blocks session stop until pending S:W:H:E tracking is logged.
- `.claude/scripts/codex-path-guard.sh` blocks direct file-tool writes to Codex-owned paths.
- `.claude/scripts/bash-command-guard.sh` blocks tested Bash write-surface bypasses against Codex-owned paths.
- `.claude/scripts/pretooluse-gate.sh` also classifies MCP tools. Known read-only MCP calls are allowed for inspection, known mutating MCP calls are blocked when readiness is `BLOCKED`, and unknown MCP tools are treated as persistent until proven otherwise.
- `.claude/scripts/config-change-guard.sh` blocks project settings changes from applying to the running Claude session if they remove the required PreToolUse dispatcher or Stop handoff hook.
- `tests/claude_adapter/` contains the focused readiness and PreToolUse test coverage that defines verified behavior.

## Post-Mutation S:W:H:E Requirement
When an installed Aegis project has `.aegis/state/current-work.json`, successful task mutations create pending tracking. The next persistent mutation is blocked until the agent runs the installed logging command:

```bash
aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"
```

If `aegis` is not available on PATH, use the installed shim:

```bash
./.aegis/bin/aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"
```

The log command appends `[S:<date>|W:task<id>-<slug>|H:<handler>|E:<evidence>]` entries to `sessions/current`, the active `TRACKER.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, and `HANDOFF.md`; it also updates the current plan evidence for `plan-step-implement` by default and clears matching pending tracking. Use `--surface findings` or `--surface decisions` when the mutation records those surfaces, and use `--plan-step plan-step-verify --plan-status completed` for final verification evidence. This is the portable enforcement layer for the S:W:H:E discipline; Taskmaster and Serena are optional.

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
- Original implementation: Taskmaster Task 103, archived at `docs/ai/work-tracking/archive/20260506-task103-claude-runtime-adapter-COMPLETED/`
- Current hardening: Taskmaster Task 105, active at `docs/ai/work-tracking/active/20260507-task105-claude-runtime-adapter-hardening-ACTIVE/`
- Current plan: `plans/2026-05-07-task105-claude-runtime-adapter-hardening.md`
