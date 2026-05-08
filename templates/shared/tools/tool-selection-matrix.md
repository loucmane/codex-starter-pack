---
id: tool-selection-matrix
type: shared-resource
category: tools
title: Tool Selection Matrix and Decision Funnel
version: 1.0.0
description: Comprehensive action-to-tool mapping and decision framework
status: stable
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Tool Selection Matrix and Decision Funnel

## Action → Tool Mapping

| I need to... | For... | MUST use... | BLOCKED |
|--------------|---------|-------------|-----------|
| Search | Simple text (TODO, logs, frontmatter, evidence labels) | `rg` / `Grep` | claiming Serena evidence for plain text search |
| Search | Code understanding | `mcp__serena__search_for_pattern` when active; otherwise `rg` with fallback note | pretending an unavailable Serena tool was used |
| Search | Symbol definitions | `mcp__serena__find_symbol` when active | grep-only symbol claims without fallback note |
| Search | File patterns | `rg --files` / `Glob` | find-first workflows |
| Understand | Code structure | `mcp__serena__get_symbols_overview` when active | bulk reading large files without a reason |
| Find references | To symbols | `mcp__serena__find_referencing_symbols` when active; otherwise targeted `rg` | silent fallback |
| Edit | ANY file changes | `Edit` or `MultiEdit` | Serena editing tools |
| Create | New files | `Write` | Serena tools |
| List directory | Contents | `LS` | ls (bash) |
| Timestamp | Any document | `date "+%Y-%m-%d %H:%M %Z"` | manual typing |
| Commit | Code changes | `direct-git-execution`: `git add -A`, `git commit -m ... -m ...`, `git push` when delegated and auth is available; `full-gac-command` only on explicit request; `message-payload-only` for message-only requests; `auth-refresh-required` when SSH/GPG cache is expired | defaulting to `gac` after delegated Git work |
| Complex search | Multiple files/patterns | `Task` tool with agent | multiple greps |
| Deep analysis | Architecture/patterns | `Task` tool with ultrathink | surface analysis |

## 🎯 Action Triggers

When you catch yourself thinking/saying:
- "I need to search..." → **STOP!** Check whether this is exact text (`rg`) or semantic structure (Serena)
- "Let me find..." → **STOP!** Use Serena for semantic understanding when active; record fallback when it is not
- "I'll update..." → **STOP!** Check timestamp protocol first
- "I'll edit..." → **STOP!** Serena for symbols, Edit for text
- "I'll analyze..." → **STOP!** Serena for structure, Task for deep analysis
- "I'll grep..." → **STOP!** Confirm this is exact text/file evidence, not semantic code navigation

## 📊 Common Violations (Learn from these!)

1. Using `rg` as a silent substitute for Serena semantic inspection
2. Typing timestamps instead of using date command
3. Using Edit for whole function replacement (use Serena)
4. Using ls in Bash instead of LS tool
5. Not using Task tool for complex multi-step searches

## 😦 DECISION FUNNEL - Follow the Questions!

### Q1: What type of operation?
├─ **SEARCH/FIND** → Go to Q2
├─ **EDIT/MODIFY** → Go to Q3  
├─ **RUN/EXECUTE** → Go to Q4
└─ **ANALYZE/UNDERSTAND** → Go to Q5

### Q2: SEARCH - What are you searching for?
├─ **Exact text / frontmatter / report label** → `rg -n`
├─ **Code patterns with structural meaning** → `mcp__serena__search_for_pattern` when active; otherwise `rg -n` + fallback note
├─ **Function/class by name** → `mcp__serena__find_symbol` when active
├─ **File names** → `rg --files` / `Glob`; `mcp__serena__find_file` when active
├─ **Who uses this symbol** → `mcp__serena__find_referencing_symbols` when active
└─ **Complex multi-file search** → Deploy specialist with `Task` tool

### Q3: EDIT - What are you editing?
├─ **Whole function/method** → `mcp__serena__replace_symbol_body`
├─ **Small text change** → `Edit` (after Read!)
├─ **Multiple small changes** → `MultiEdit`
├─ **Add code after function** → `mcp__serena__insert_after_symbol`
├─ **Add code before function** → `mcp__serena__insert_before_symbol`
└─ **Replace by pattern** → `Edit` / `MultiEdit`; `mcp__serena__replace_content` when active and policy allows

### Q4: RUN - What are you running?
├─ **Shell command** → `Bash`
├─ **List directory** → `LS` (NOT ls in Bash!)
├─ **Git operations** → `Bash` with proper commands
└─ **Complex automation** → Deploy specialist with `Task` tool

### Q5: ANALYZE - What do you need to understand?
├─ **Code structure overview** → `mcp__serena__get_symbols_overview`
├─ **Deep architectural analysis** → Deploy specialist with `Task` tool
├─ **Simple file reading** → `Read`
└─ **Documentation lookup** → `mcp__context7__get-library-docs`

## 🚫 FORBIDDEN PATHS

If you find yourself wanting to:
- Type `grep` → **STOP!** Prefer `rg`; use Serena for semantic structure when active
- Type `find` → **STOP!** Prefer `rg --files`, `Glob`, or `mcp__serena__find_file` when active
- Type a timestamp → **STOP!** Use `date "+%Y-%m-%d %H:%M %Z"`
- Edit without reading → **STOP!** Always `Read` first
- Use `ls` in Bash → **STOP!** Use `LS` tool

## 📊 Comprehensive Tool Selection Matrix

### Quick Tool Finder

| I need to... | Best Tool | Why | Example |
|--------------|-----------|-----|---------||
| **Find a file by name** | Glob | Fast pattern matching | `Glob "**/*Header*"` |
| **Search for text in files** | `rg` / Grep | Content search | `rg -n "useState"` |
| **Find a specific function** | Serena `find_symbol` when active | Semantic understanding | `find_symbol "handleAuth"` |
| **See file structure** | Serena `get_symbols_overview` when active | Shows all symbols | `get_symbols_overview "src/"` |
| **Replace entire function** | Serena `replace_symbol_body` when active | Clean replacement under normal policy | Better than manual edit when ownership allows |
| **Add imports/functions** | Serena `insert_before_symbol` / `insert_after_symbol` when active | Precise placement under normal policy | No manual line counting |
| **Complex search task** | Task tool | Deploy search specialist | "Find all auth implementations" |
| **Small text change** | Edit or Serena `replace_content` when active | Quick edits | Use wildcards carefully and respect ownership gates |
| **Multiple changes in file** | MultiEdit | Batch operations | All edits in one go |
| **Run commands** | Bash | System operations | Always quote paths! |
| **Track work** | TodoWrite | Task management | Before starting work |
| **Plan project** | TaskMaster | Dependencies + progress | Major features |
| **Remember for later** | Serena write_memory | Session knowledge | End of session |
| **Get documentation** | Context7 | Latest docs | Single topic queries |

## Tool Decision Tree

```
Need to find something?
├─ Know exact filename? → Glob
├─ Know text content? → `rg -n`
├─ Know function/class name? → Serena `find_symbol` when active
├─ Need to explore structure? → Serena `get_symbols_overview` when active
└─ Complex multi-file search? → Task tool with search specialist

Need to edit code?
├─ Replace whole function? → Serena replace_symbol_body
├─ Add new code? → Serena insert_before/after_symbol
├─ Small text change? → Edit or Serena `replace_content` when active
├─ Multiple changes? → MultiEdit
└─ Complex refactor? → Task tool with clear instructions

Need analysis/planning?
├─ Track current work? → TodoWrite
├─ Plan features? → TaskMaster
├─ Check progress? → TaskMaster get_tasks
├─ Remember info? → Serena memory
└─ Document work? → Work tracking 6-file system

Need project info?
├─ What did we do before? → Serena list/read memories
├─ Current project state? → Serena get_current_config
└─ Documentation lookup? → Context7
```

## Tool Combination Patterns

| Workflow | Tool Sequence | Example |
|----------|---------------|---------||
| **Feature Implementation** | Context7 → Serena → TodoWrite → Implementation → Testing | Research → Analyze → Plan → Build → Verify |
| **Bug Fix** | `rg`/Serena → Analyze → Edit → Test | Find issue → Understand → Fix → Validate |
| **Code Understanding** | Serena overview → find_symbol → find_referencing | Survey → Locate → Trace usage |
| **Refactoring** | Serena find_referencing → TodoWrite → MultiEdit | Find usage → Plan → Execute |
| **Research Task** | Context7 → Task → Serena memory | Learn → Deep dive → Remember |

## Tool Synergy Guide

**Serena + Task**:
- Serena finds the code → Task specialist analyzes deeply
- Example: Find all auth code → Security review

**TaskMaster + TodoWrite**:
- TaskMaster provides structure → TodoWrite tracks progress
- Example: Get subtasks → Track completion

**Context7 + Memory**:
- Context7 gets docs → Memory saves insights
- Example: Research Next.js → Save patterns found

**`rg` + Serena**:
- `rg` finds exact text → Serena understands structure when active
- Example: Find "TODO" → Understand context

## Change Log

- **2026-05-08 14:25** — [S:20260508|W:task15-serena-integration-template-system|H:templates/shared/tools/tool-selection-matrix.md|E:docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/designs/serena-integration-scope-reconciliation.md] Clarified Serena-vs-`rg` routing so exact-text evidence stays deterministic while semantic inspection uses Serena when the active MCP exposes it.
- **2026-05-07 10:34** — [S:20260507|W:task104-targeted-taskmaster-generation-helper|H:templates/shared/tools/tool-selection-matrix.md|E:docs/ai/work-tracking/active/20260507-task104-targeted-taskmaster-generation-helper-ACTIVE/TRACKER.md] Documented direct Git execution when SSH/GPG auth is cached and the user delegates Git work to Codex.
