# Claude Agents Catalog

## Primary Agent
- Entry point: `CLAUDE.md`
- Runtime contract: `.claude/engine/runtime-contract.md`
- Readiness gate: `.claude/scripts/readiness.sh`
- PreToolUse dispatcher: `.claude/scripts/pretooluse-gate.sh`
- PostToolUse tracker: `.claude/scripts/posttooluse-tracking.sh`
- Stop tracking gate: `.claude/scripts/tracking-stop-gate.sh`
- Project settings: `.claude/settings.json`

Claude is allowed to reason before readiness, but hookable persistent mutation requires readiness `READY`. After a successful mutation, pending S:W:H:E tracking must be logged with `aegis log` or `./.aegis/bin/aegis log`; that command updates the active session, tracker, implementation log, changelog, handoff, and current plan evidence before the next mutation.

## Local Sub-Agents
| Agent | Purpose | First action |
| --- | --- | --- |
| `task-orchestrator` | Coordinate Taskmaster task selection and sub-agent delegation | Run readiness; inspect active session, plan, and tracker. |
| `task-executor` | Implement one scoped task/subtask | Run readiness; confirm Taskmaster task and active tracker. |
| `task-checker` | Verify task completion and audit trail | Run readiness; run guard, tests, and plan sync. |

Sub-agents inherit no parent conversation context. Every delegation brief must include task ID, branch, active work-tracking folder, current plan, and the requirement to stop on `BLOCKED` readiness.

## Hooks
| Event | Matcher | Script | Behavior |
| --- | --- | --- | --- |
| `PreToolUse` | `^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$` | `.claude/scripts/pretooluse-gate.sh` | Blocks hookable persistent mutations when readiness is `BLOCKED`; blocks Codex-owned paths, tested Bash bypasses, and protected-path MCP writes when ready. |
| `PostToolUse` | `^(Edit|Write|MultiEdit|NotebookEdit|Bash|mcp__.*)$` | `.claude/scripts/posttooluse-tracking.sh` | Records pending S:W:H:E tracking after successful persistent mutations. |
| `Stop` | all | `.claude/scripts/tracking-stop-gate.sh` | Blocks session stop while pending S:W:H:E tracking remains. |
| `Stop` | all | `.claude/scripts/handoff-nudge.sh` | Emits a non-blocking reminder when dirty workflow state needs handoff/guard attention. |
| `ConfigChange` | all | `.claude/scripts/config-change-guard.sh` | Blocks project settings changes from applying if they remove the required runtime gate hooks. |

## Commands
| Command | Wraps |
| --- | --- |
| `/readiness` | `bash .claude/scripts/readiness.sh` |
| `/kickoff` | `python3 scripts/codex-task wizard kickoff` |
| `/guard` | `python3 scripts/codex-guard validate --include-untracked` |
| `/plan-sync` | `python3 scripts/codex-task plan sync` |
| `/work-tracking-audit` | `python3 scripts/codex-task work-tracking audit` |
| `/sessions-update` | `python3 scripts/codex-task sessions update` |
| `/work-tracking-update` | `python3 scripts/codex-task work-tracking update` |
| `/scanner-run` | `python3 scripts/codex-task scanner run` |

## Ownership Boundaries
Claude-owned:
- `CLAUDE.md`
- `.claude/**`
- `tests/claude_adapter/**`

Codex-owned and blocked:
- `CODEX.md`
- `templates/**`
- `scripts/codex-*`
- `scripts/template-*`
- `.codex/**`

Shared state:
- `.taskmaster/**`
- `sessions/**`
- `plans/**`
- `docs/ai/work-tracking/**`
