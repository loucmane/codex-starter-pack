# Claude Readiness

## Purpose
Claude readiness is the first mechanical gate in the Claude runtime adapter. It is a read-only check that decides whether Claude may perform persistent mutations in the project.

The gate exists because documentation, memories, and verbal commitments are not sufficient. A future Claude session must be blocked by tooling when task/session/plan/work-tracking state is missing or misaligned.

## Command
```bash
bash .claude/scripts/readiness.sh
bash .claude/scripts/readiness.sh --quick
```

`--quick` is intended for PreToolUse hooks. It returns the same exit code as the full command but emits a single status line.

## States
- `READY` exits `0`: branch, Taskmaster parent task, active session, active plan, ACTIVE work-tracking folder, and plan/tracker checklist state all align.
- `WARN` exits `0`: soft issues are present but mutation can proceed. No soft warnings are currently emitted by the first implementation.
- `BLOCKED` exits `2`: required workflow state is missing or inconsistent. Hookable persistent mutations must be refused.

`BLOCKED` does not prohibit read-only discovery. Agents may inspect files and may use read-only Taskmaster CLI/MCP discovery to identify an external numeric task before Aegis kickoff. For Taskmaster MCP, the read-only discovery allowlist is intentionally narrow: `help`, `get_tasks`, `next_task`, and `get_task`. Taskmaster MCP mutations and unknown Taskmaster MCP tools remain blocked until readiness is `READY`, except for the separate post-closeout bookkeeping allowance for the matching task.

## Required Alignment
Readiness blocks unless all of these are true:
- the current branch contains a task ID, such as `feat/task-103-claude-runtime-adapter`;
- `.taskmaster/tasks/tasks.json` contains that parent task with status `in-progress`;
- `sessions/current` is a symlink to an existing session that references the task;
- `sessions/state.json` has `current` equal to the active session basename;
- `plans/current` is a symlink to an existing plan that references the task;
- exactly one `docs/ai/work-tracking/active/*-ACTIVE` folder exists;
- that ACTIVE folder and its `TRACKER.md` reference the task;
- `plan-step-scope`, `plan-step-implement`, and `plan-step-verify` statuses match between the plan table and tracker checklist.

## Multimodal Role
Readiness does not inspect every mutation surface directly. It gives the runtime a single truth source that other gates can call before handling Claude file tools, Bash commands, MCP actions, memory writes, Git/GitHub actions, and future tool surfaces.

Any enforcement claim that depends on readiness must be backed by a focused test or explicitly documented as policy-only in the active Task 103 work-tracking folder.
