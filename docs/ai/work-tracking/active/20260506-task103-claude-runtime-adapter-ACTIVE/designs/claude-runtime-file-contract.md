# Claude Runtime File Contract

## Purpose
Task 103 exists to make Claude operate inside the same workflow engine as Codex through a gated runtime, not through memory, convention, or documentation alone. The adapter must support multimodal and multi-agent work across Claude, Codex, shell, MCP, GitHub, memory stores, and future tool surfaces.

## Current Inputs
- Current branch: `feat/task-103-claude-runtime-adapter`
- Taskmaster task: `103`
- Active session: `sessions/current`
- Active plan: `plans/current`
- Active tracker: `docs/ai/work-tracking/active/20260506-task103-claude-runtime-adapter-ACTIVE/TRACKER.md`
- Reference branch: `feat/claude-port-bootstrap`

## Bootstrap Branch Inventory
`feat/claude-port-bootstrap` is raw material only. Files from that branch may not be copied blindly.

| Source commit | Files | Initial verdict |
| --- | --- | --- |
| `4261ea8` | `CLAUDE.md`, `.claude/commands/readiness.md`, `.claude/engine/claude-readiness.md`, `.claude/engine/tool-mapping.md`, `.claude/scripts/readiness.sh` | Rewrite/port after readiness hard-gate design; v1 readiness was a reporter, not enough as a gate. |
| `dff61f4` | `.claude/settings.json` | Rewrite after tool-gate contract; allowlist must match current hook behavior. |
| `34fe103` | `.claude/commands/{guard,kickoff,plan-sync,scanner-run,sessions-update,work-tracking-audit,work-tracking-update}.md` | Port with updates after command surface is checked against current `codex-task`/`codex-guard`. |
| `e689759` | `.claude/scripts/codex-path-guard.sh`, `.claude/settings.json` | Rewrite into a dispatcher model where readiness gates every hookable mutation first. |
| `b41c860` | `.claude/scripts/handoff-nudge.sh`, `.claude/settings.json`, `.gitignore` | Port only if stop-hook behavior proves useful and tested. |
| `601ff3c` | `.claude/AGENTS.md` | Port after agent responsibilities are aligned to the runtime contract. |
| `ba520e8` | `.claude/agents/task-checker.md`, `.claude/agents/task-executor.md`, `.claude/agents/task-orchestrator.md` | Rewrite/port after sub-agent first-action gates are defined. |

## Permanent Claude-Owned Files
These files are owned by Task 103 unless later split:
- `CLAUDE.md`
- `.claude/AGENTS.md`
- `.claude/engine/runtime-contract.md`
- `.claude/engine/claude-readiness.md`
- `.claude/engine/tool-mapping.md`
- `.claude/scripts/readiness.sh`
- `.claude/scripts/pretooluse-gate.sh`
- `.claude/scripts/codex-path-guard.sh`
- `.claude/scripts/bash-command-guard.sh`
- `.claude/scripts/handoff-nudge.sh`
- `.claude/commands/*.md`
- `.claude/agents/task-checker.md`
- `.claude/agents/task-executor.md`
- `.claude/agents/task-orchestrator.md`
- `.claude/settings.json`
- `tests/claude_adapter/**`

## Shared Or Codex-Owned Boundaries
Claude adapter work must not modify these paths in this task:
- `CODEX.md`
- `templates/**`
- `scripts/codex-*`
- `scripts/template-*`
- `.codex/**`

If Claude needs a shared or Codex-side change, record the need in `DECISIONS.md` and create a Codex-led follow-up task. Do not make the change inside Task 103.

## Runtime Chain
The intended runtime chain is:
1. Claude invokes a mutation-capable tool.
2. Claude PreToolUse hook calls `.claude/scripts/pretooluse-gate.sh`.
3. `pretooluse-gate.sh` calls `.claude/scripts/readiness.sh --quick`.
4. If readiness is `BLOCKED`, all hookable persistent mutations are refused.
5. If readiness is `READY` or allowed `WARN`, the dispatcher runs path-specific and command-specific guards.
6. The command/path guard blocks protected Codex-owned paths and obvious Bash write-surface bypasses.
7. Tests prove each supported claim, or the surface is marked policy-only.

## Acceptance
Subtask 103.1 is not complete until:
- this file reflects the current bootstrap inventory;
- `designs/mutation-taxonomy.md` labels mutation surfaces;
- `.claude/engine/runtime-contract.md` exists as the permanent contract draft;
- Task 10 queue deferral and ownership boundaries are recorded in `DECISIONS.md`;
- plan sync and guard pass with this scope.
