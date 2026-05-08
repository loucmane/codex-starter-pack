---
id: serena-guide
type: tool-guide
category: search
title: Serena MCP Integration Guide
version: 2.0.0
description: Capability-aware Serena MCP contract for semantic inspection, memory continuity, and template fallback evidence
status: stable
tools: [mcp__serena__get_current_config, mcp__serena__list_memories, mcp__serena__read_memory, mcp__serena__write_memory, mcp__serena__search_for_pattern, mcp__serena__find_symbol, mcp__serena__get_symbols_overview]
---

# Serena MCP Integration Guide

## Contract

Serena is part of the workflow runtime, not a note-taking preference. A session that depends on template discovery, template analysis, compaction recovery, or cross-session evidence must verify Serena configuration and record the Serena memory handoff when the task reaches a meaningful checkpoint.

The current portable foundation uses a split contract:

- Deterministic local template resolution goes through `TemplateRegistry`, scanner outputs, compatibility maps, and `rg` for exact text checks.
- Serena provides semantic inspection when the MCP exposes symbol/search tools.
- Serena memory is mandatory evidence for session continuity when guard/work-tracking requires a same-day memory reference.
- `TemplateRegistry.resolve(..., allow_serena=True)` keeps Serena as a structured fallback action for unresolved template queries: `source=serena`, `fallback_action=serena_search`.

Do not replace deterministic registry/scanner behavior with ad hoc Serena calls. Do not claim Serena evidence exists unless a memory was written and referenced from the tracker/session.

## Configuration Check

Run the local status helper before relying on Serena in a workflow:

```bash
python3 scripts/codex-task serena status --strict
```

For evidence capture:

```bash
python3 scripts/codex-task serena status --strict \
  --report-file docs/ai/work-tracking/active/<folder>/reports/<slug>/serena-status-YYYY-MM-DD.txt
```

The helper verifies:

- `.codex/config.toml` exposes `mcp_servers.serena`.
- `.mcp.json` exposes a project-level `mcpServers.serena` entry for clients such as Claude.
- Serena starts through `uvx ... serena start-mcp-server --project-from-cwd`.
- `.serena/memories/` exists and reports recent memories.

Inside an active agent session, confirm the runtime tool surface with:

```text
mcp__serena__get_current_config
```

If the runtime exposes fewer tools than the docs list, use the tools actually present and record the limitation in `FINDINGS.md` / `DECISIONS.md`. Never silently invent a Serena capability.

## Session Start

For Codex and Claude sessions with Serena available:

1. Confirm normal workflow state first: Taskmaster task, branch, `sessions/current`, `plans/current`, and ACTIVE work-tracking folder.
2. Run `python3 scripts/codex-task serena status --strict` when the task scope depends on Serena.
3. Call `mcp__serena__get_current_config` to confirm the active project is the current repository.
4. Read only relevant memories. Prefer exact memory names from the session handoff, tracker, or `MEMORY-REFS.md`; avoid bulk reading every memory.

## Template Discovery

Use this order for template work:

1. `scripts/template_registry.py` / `TemplateRegistry` for registered template IDs, paths, metadata, compatibility redirects, and deterministic suggestions.
2. `scripts/template-ssot-scanner` and related scanner reports for repository-wide template inventory and drift.
3. `rg` for exact text, frontmatter keys, report labels, and simple file-pattern checks.
4. Serena semantic tools for code/template structure questions when they are exposed by the active MCP session.
5. Serena fallback evidence when local registry/compatibility/legacy discovery misses and the query needs semantic or memory-backed investigation.

Expected fallback signal:

```text
source=serena
fallback_action=serena_search
trace includes serena:fallback
```

## Tool Use

Use the runtime tools that `mcp__serena__get_current_config` reports as active. Common tools include:

| Need | Preferred Serena Tool | Notes |
| --- | --- | --- |
| Confirm project/tool state | `get_current_config` | First Serena check for tool availability |
| Find a symbol | `find_symbol` | Use `relative_path` and `substring_matching` when helpful |
| Inspect file structure | `get_symbols_overview` | Prefer before reading large source files |
| Search structured patterns | `search_for_pattern` | Scope with `relative_path` to keep output small |
| Find references | `find_referencing_symbols` | Use before symbol-level edits |
| Write session memory | `write_memory` | Required when guard/work-tracking expects Serena evidence |
| Read specific memory | `read_memory` | Use named memories from handoff/tracker |
| List candidate memories | `list_memories` | Filter by topic when possible |

Editing through Serena may be available in some runtimes, but repository policy still applies. Do not use Serena editing tools to bypass ownership boundaries, workflow gates, or normal file-review expectations.

## Memory Rules

Serena memories are continuity artifacts. They do not replace session logs, plan updates, tracker entries, findings, decisions, implementation notes, handoff docs, or test evidence.

Required memory points:

- End of a meaningful session or checkpoint.
- Before compaction when the next agent needs exact resume context.
- After completing a task implementation or verification phase.
- When guard requires a same-day Serena memory reference in the active tracker.

After writing a memory:

1. Reference the memory name in `TRACKER.md`.
2. Reference it in the active session log with handler `serena/memory`.
3. Include the memory in `HANDOFF.md` if it is needed for continuation.
4. Run `python3 scripts/codex-guard validate --include-untracked`.

## Failure Modes

| Failure | Correct Response |
| --- | --- |
| `.mcp.json` lacks Serena | Add/repair the project MCP entry or document why the current task cannot require Serena |
| `.codex/config.toml` lacks Serena | Repair Codex runtime config before relying on Serena |
| Serena MCP does not start | Record the startup failure, use deterministic registry/scanner evidence, and do not claim Serena-backed evidence |
| Required semantic tool missing | Use available Serena tools or `rg`/registry fallback, then record the limitation |
| Tracker lacks same-day memory reference | Write the Serena memory, log it in tracker/session, rerun guard |

## Change Log

- **2026-05-08 14:25** — [S:20260508|W:task15-serena-integration-template-system|H:templates/tools/search/serena-guide.md|E:docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/designs/serena-integration-scope-reconciliation.md] Reframed Serena as a capability-aware runtime contract for memory continuity, semantic inspection, and template fallback evidence.
