# Claude Runtime Adapter

This repo uses Claude as a gated participant in the portable Codex foundation. The adapter is a runtime system, not a reminder document: readiness, PreToolUse/PostToolUse/Stop hooks, tests, and work-tracking evidence define whether Claude may mutate project state.

## First Rule
Before Claude performs any persistent mutation, readiness must be `READY`.

```bash
bash .claude/scripts/readiness.sh
```

`BLOCKED` means no file edits, Bash mutations, Taskmaster mutations, memory writes, Git writes, GitHub writes, or MCP mutations. Fix the workflow state first by using the kickoff/session/plan/work-tracking flow. Read-only inspection is allowed.

The PreToolUse dispatcher in `.claude/scripts/pretooluse-gate.sh` enforces this for hookable Claude file tools and tested Bash mutation patterns. After a successful mutation, `.claude/scripts/posttooluse-tracking.sh` records pending S:W:H:E tracking and `.claude/scripts/tracking-stop-gate.sh` blocks session stop until `aegis log` has updated the session, tracker, implementation log, changelog, handoff, and plan evidence.

## Required Workflow State
Claude mutations require all of these to align:
- current branch contains the active Taskmaster task ID;
- Taskmaster parent task is `in-progress`;
- `sessions/current` points to the active session for the task;
- `plans/current` points to the active plan for the task;
- exactly one ACTIVE work-tracking folder exists for the task;
- `TRACKER.md` and the active plan agree on plan-step status;
- `bash .claude/scripts/readiness.sh --quick` exits `0`.

## Operating Loop
1. Run readiness and stop on `BLOCKED`.
2. Read `sessions/current`, `plans/current`, and the active `HANDOFF.md`.
3. Review the Taskmaster task with `task-master show <id>`.
4. Work one subtask at a time.
5. For every meaningful step, run `aegis log` or `./.aegis/bin/aegis log` before attempting the next mutation. The log must update the active session, tracker, implementation log, changelog, handoff, and current plan evidence; add `--surface findings` or `--surface decisions` when the mutation captured one of those records.
6. Capture command evidence under the active work-tracking `reports/` folder.
7. Run focused tests, `python3 scripts/codex-task plan sync`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, `git diff --check`, and pre-commit before checkpointing.

## Claude-Owned Paths
Claude adapter work may edit:
- `CLAUDE.md`
- `.claude/**`
- `tests/claude_adapter/**`
- task/session/plan/work-tracking files for the active task

## Codex-Owned Paths
Claude must not edit these paths from this task:
- `CODEX.md`
- `templates/**`
- `scripts/codex-*`
- `scripts/template-*`
- `.codex/**`

The PreToolUse gate blocks direct file edits and tested Bash bypasses against these paths. If a change is needed there, document it in `DECISIONS.md` and create a Codex-led follow-up.

## Multimodal Scope
This workflow is not text-only. Treat the same state discipline as mandatory for:
- Claude file tools;
- Bash commands;
- Taskmaster CLI and MCP;
- Serena and Claude memory stores;
- Git and GitHub operations;
- sub-agents;
- future tool surfaces that can perform persistent mutations.

Every enforcement claim must be backed by a passing test or labeled policy-only in the active task's `DECISIONS.md` and `HANDOFF.md`.

## Slash Commands
Claude project commands live under `.claude/commands/`.

Core runtime commands:
- `/readiness` -> `bash .claude/scripts/readiness.sh`
- `/kickoff` -> `python3 scripts/codex-task wizard kickoff`
- `/guard` -> `python3 scripts/codex-guard validate --include-untracked`
- `/plan-sync` -> `python3 scripts/codex-task plan sync`
- `/work-tracking-audit` -> `python3 scripts/codex-task work-tracking audit`
- `/sessions-update` -> `python3 scripts/codex-task sessions update`
- `/work-tracking-update` -> `python3 scripts/codex-task work-tracking update`
- `/scanner-run` -> `python3 scripts/codex-task scanner run`

Taskmaster commands under `.claude/commands/tm/` remain available for Taskmaster-specific flows.

## Supporting References
- Runtime contract: `.claude/engine/runtime-contract.md`
- Readiness spec: `.claude/engine/claude-readiness.md`
- Tool mapping: `.claude/engine/tool-mapping.md`
- Agent catalog: `.claude/AGENTS.md`
- Taskmaster integration guide: `@./.taskmaster/CLAUDE.md`
