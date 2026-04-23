
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Codex Tooling & Command Router

This document defines the allowed tools inside the Codex CLI, how to choose between them, and the evidence you must produce when using each one.

## 🚦 Decision Router
Follow this checklist before every tool invocation:

1. **State the intent** – "I need to inspect tests for feature X".
2. **Pick the matching tool** using the table below.
3. **Echo the command** (or MCP call) you will run.
4. **Capture output** and cite file paths / line numbers as evidence.

### Action → Tool Mapping

| I need to… | Preferred tool | Notes |
|------------|----------------|-------|
| Search text/code | `shell` `rg`, `ripgrep`, or project MCP search | Show command + snippet; prefer `rg -n` for line numbers |
| List files | `shell` `ls`, `fd`, or `find` | Use `ls -A` / `fd` for filtered views |
| Inspect files | `shell` `sed`, `cat`, `python3 - <<'PY'` | Provide line numbers when possible |
| Edit files | Editor integration outside Codex or scripted edit + review | Codex CLI is read/write; confirm edits via diff |
| Run tests | `shell` (pytest, npm, etc.) | Capture command + pass/fail summary |
| Open docs/web | `web_search` or MCP HTTP tool (if enabled) | Note when network approvals were required |
| Delegate to agent | Configured MCP specialist (e.g., TaskMaster) | Show request payload and returned summary |

### When MCP Servers Are Available
- Registered under `[mcp_servers]` in `.codex/config.toml`.
- Invoke via the `mcp` commands (e.g., `/mcp call taskmaster-ai plan`).
- Document server name, method, and key response fields.

#### Serena (Semantic Toolkit)
- **Purpose**: Symbol-aware search and edits (`find_symbol`, `find_referencing_symbols`, `replace_symbol_body`, etc.).
- **Command pattern**: `/mcp call serena <tool> ...` (see `templates/shared/tools/tool-selection-matrix.md` for full router).
- **When to use**: Any time you need structured code insight. Use Serena before falling back to plain `rg`/`sed` searches.

#### Taskmaster AI
- **Purpose**: Task planning, dependency tracking, TodoRead/Write integration.
- **Command pattern**: `/mcp call taskmaster-ai <method>`.
- **Evidence**: Paste the request payload and returned task summaries.

#### Context7
- **Purpose**: Live documentation lookup.
- **Command pattern**: `/mcp call context7-mcp get-library-docs --topic "..."`.
- **Notes**: Keep queries scoped (single topic/file) to control token use.

#### Sequential Thinking
- **Purpose**: Guided multi-thought analysis.
- **Command pattern**: `/mcp call sequential-thinking think --total_thoughts 10` (returns structured thought log).
- **Use**: When problems need deliberate reasoning beyond default planning.

## Built-in Tools

### `shell`
Primary interface for filesystem and process commands. Always:
- Show the exact command (prefixed with `$`).
- Provide the working directory if it differs from `~/codex`.
- Capture stderr when the command fails and explain the next step.

### `update_plan`
Lightweight structured plan tracker. Use it to:
- Declare multi-step work before making changes.
- Update after each completed step.
- Close the plan at the end (status `completed`).

### `scripts/codex-task`
Local CLI for S:W:H:E scaffolding. Subcommands:
- `sessions update` – append to active session progress log.
- `work-tracking update` – append to ACTIVE docs (default `TRACKER`).
- `scanner run <tool>` – execute SSOT scanners and optionally log results (`--log-note`).
Always pass `--work`, `--handler`, and `--evidence`; use single quotes to preserve backticks.

### `scripts/codex-guard`
Run `scripts/codex-guard validate [--include-untracked]` before handoff/compaction. Confirms:
- S:W:H:E fields populated (no placeholders).
- Handler paths resolve into `templates/` (when referenced).
- Evidence fields not left `pending`.
- Runtime artifacts stay out of commits (`__pycache__/`, `.pyc`/`.pyo`, `.codex/*.sqlite*`).
- Taskmaster status/file changes include same-day session and tracker evidence.
- Session state stays coherent (`sessions/current`, `sessions/state.json`, paused session references).
- Canonical GAC guidance distinguishes `full-gac-command` from `message-payload-only` and uses the multi-line `Summary:` block.
Roadmap: `--auto-fix` skeletons (document TODOs in work-tracking).

Task 92 expanded this guard coverage to turn recurring workflow mistakes into enforceable checks. When adding new guard rules, update the relevant template/convention docs and add targeted regression coverage in `tests/meta_workflow_guard/test_guard_rules.py`.

### `view_image`
Limited to image previews. Document file path and purpose.

### `web_search` (optional)
Enabled when `.codex/config.toml` sets `tools.web_search = true` and network access is granted. Cite the search query and summarize sources with links.

## Evidence Expectations
- **Searches**: Include command + 1-2 matching lines with context.
- **Edits**: Reference the file and lines modified; run a diff when possible.
- **Tests/Builds**: Provide the command and final status (pass/fail, exit code).
- **MCP Calls**: Log the request + salient parts of the response.

## Anti-Patterns
- Running `grep`/`find` without showing output.
- Modifying files without noting the diff or follow-up plan.
- Invoking network-dependent commands when `network_access=false` and failing to acknowledge the restriction.
- Delegating to MCP servers that are not configured in `.codex/config.toml`.

## Quick Reference
- `rg <pattern> templates/registry` – discover handlers.
- `python3 - <<'PY'` blocks – for JSON/Markdown inspection and summarisation.
- `codex --dry-run -- <command>` – verify wrapper configuration outside the session.

Tools are part of the protocol. Use them deliberately and leave a clear evidence trail every time.

## Progress Log

- **2026-04-23 13:15** — [S:20260423|W:task92-expand-workflow-guard-coverage|H:templates/TOOLS.md|E:docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/designs/guard-coverage-audit.md] Documented the expanded `scripts/codex-guard` coverage for runtime artifacts, Taskmaster evidence, session-state consistency, and canonical GAC guidance
