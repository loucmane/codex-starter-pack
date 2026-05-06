# Claude Tool Mapping

The shared foundation documentation was originally written for Codex and often names Codex tools. Claude must translate those references at call time. Do not edit shared handlers or templates to rename tools.

## Core Translation
| Codex reference | Claude equivalent | Notes |
| --- | --- | --- |
| `update_plan` | Claude task tracker / local checklist | In this repo, durable task state remains Taskmaster plus plan/tracker files. |
| `shell` | `Bash` | Use for commands only; prefer file tools for file edits. |
| `shell` file reads | `Read` or `Grep`/`Glob` | Use structured tools where possible. |
| `view_image` | `Read` | Claude can inspect images and PDFs through file reads. |
| MCP tool calls | same `mcp__server__tool` naming | Confirm the MCP server is enabled before relying on it. |
| Sub-agent delegation | `Agent` | Sub-agents do not inherit conversation context; brief them with workflow state. |

## Runtime-Specific Rules
- Before mutation, Claude readiness must be `READY`.
- File mutations flow through `.claude/scripts/pretooluse-gate.sh`.
- Bash write-surface bypasses are blocked for tested patterns.
- Codex-owned paths remain off limits from Claude sessions.

## Shared State
These state files are shared between Codex and Claude:
- `.taskmaster/tasks/tasks.json`
- `sessions/**`
- `plans/**`
- `docs/ai/work-tracking/**`

The `codex-` prefix on `scripts/codex-task` and `scripts/codex-guard` is historical. They are the current agent-agnostic workflow helpers.
