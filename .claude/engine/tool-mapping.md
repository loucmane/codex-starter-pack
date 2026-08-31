# Claude Tool Mapping

The shared foundation documentation was originally written for Codex and often names Codex tools. Claude must translate those references at call time. Do not edit shared handlers or templates to rename tools.

## Core Translation
| Codex reference | Claude equivalent | Notes |
| --- | --- | --- |
| `update_plan` | Claude task tracker / local checklist | Durable work authority is the Gas City Bead; Aegis plan/tracker files are evidence. |
| `shell` | `Bash` | Use for commands only; prefer file tools for file edits. |
| `shell` file reads | `Read` or `Grep`/`Glob` | Use structured tools where possible. |
| `view_image` | `Read` | Claude can inspect images and PDFs through file reads. |
| MCP tool calls | same `mcp__server__tool` naming | Confirm the MCP server is enabled before relying on it. |
| Sub-agent delegation | Gas City Bead + reviewed `gc sling` | Managed-project `Agent`/`Task` calls are mechanically blocked. A routing failure is not fallback authority. |

## Runtime-Specific Rules
- Before mutation, Claude readiness must be `READY`.
- File mutations flow through `.claude/scripts/pretooluse-gate.sh`.
- Successful mutations flow through `.claude/scripts/posttooluse-tracking.sh`; pending S:W:H:E tracking must be cleared with `aegis log --handler <handler> --evidence <path-or-command> --note "<past-tense note>"` or `./.aegis/bin/aegis log ...` before the next mutation. The log updates the active session, tracker, implementation log, changelog, handoff, and current plan evidence.
- Bash write-surface bypasses are blocked for tested patterns.
- Codex-owned paths remain off limits from Claude sessions.

## Shared State
These state surfaces are shared between Codex and Claude:
- the rig-scoped Gas City Bead store (authoritative, accessed only through supported APIs)
- `sessions/**`
- `plans/**`
- `docs/ai/work-tracking/**`

The `codex-` prefix on `scripts/codex-task` and `scripts/codex-guard` is historical. They are the current agent-agnostic workflow helpers.
