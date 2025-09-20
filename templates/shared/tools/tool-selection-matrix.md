---
id: tool-selection-matrix
type: shared-resource
category: tools
title: Tool Selection Matrix and Decision Funnel
version: 1.0.0
description: Comprehensive action-to-tool mapping and decision framework
status: stable
---

# Tool Selection Matrix and Decision Funnel

## Action → Tool Mapping

| I need to... | For... | MUST use... | BLOCKED |
|--------------|---------|-------------|-----------|
| Search | Simple text (TODO, logs) | `Grep` | - |
| Search | Code understanding | `mcp__serena__search_for_pattern` | grep |
| Search | Symbol definitions | `mcp__serena__find_symbol` | grep |
| Search | File patterns | `Glob` | find |
| Understand | Code structure | `mcp__serena__get_symbols_overview` | manual reading |
| Find references | To symbols | `mcp__serena__find_referencing_symbols` | grep |
| Edit | ANY file changes | `Edit` or `MultiEdit` | Serena editing tools |
| Create | New files | `Write` | Serena tools |
| List directory | Contents | `LS` | ls (bash) |
| Timestamp | Any document | `date "+%Y-%m-%d %H:%M %Z"` | manual typing |
| Commit | Code changes | `gac "message"` | git commit |
| Complex search | Multiple files/patterns | `Task` tool with agent | multiple greps |
| Deep analysis | Architecture/patterns | `Task` tool with ultrathink | surface analysis |

## 🎯 Action Triggers

When you catch yourself thinking/saying:
- "I need to search..." → **STOP!** Check router for Serena vs Glob
- "Let me find..." → **STOP!** Serena has semantic understanding
- "I'll update..." → **STOP!** Check timestamp protocol first
- "I'll edit..." → **STOP!** Serena for symbols, Edit for text
- "I'll analyze..." → **STOP!** Serena for structure, Task for deep analysis
- "I'll grep..." → **STOP!** Always use Serena for code search

## 📊 Common Violations (Learn from these!)

1. Using grep instead of Serena for code search
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
├─ **Code patterns/text** → `mcp__serena__search_for_pattern`
├─ **Function/class by name** → `mcp__serena__find_symbol`
├─ **File names** → `Glob` (for patterns) or `mcp__serena__find_file`
├─ **Who uses this symbol** → `mcp__serena__find_referencing_symbols`
└─ **Complex multi-file search** → Deploy specialist with `Task` tool

### Q3: EDIT - What are you editing?
├─ **Whole function/method** → `mcp__serena__replace_symbol_body`
├─ **Small text change** → `Edit` (after Read!)
├─ **Multiple small changes** → `MultiEdit`
├─ **Add code after function** → `mcp__serena__insert_after_symbol`
├─ **Add code before function** → `mcp__serena__insert_before_symbol`
└─ **Replace by pattern** → `mcp__serena__replace_regex`

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
- Type `grep` → **STOP!** Use `mcp__serena__search_for_pattern`
- Type `find` → **STOP!** Use `Glob` or `mcp__serena__find_file`
- Type a timestamp → **STOP!** Use `date "+%Y-%m-%d %H:%M %Z"`
- Edit without reading → **STOP!** Always `Read` first
- Use `ls` in Bash → **STOP!** Use `LS` tool

## 📊 Comprehensive Tool Selection Matrix

### Quick Tool Finder

| I need to... | Best Tool | Why | Example |
|--------------|-----------|-----|---------||
| **Find a file by name** | Glob | Fast pattern matching | `Glob "**/*Header*"` |
| **Search for text in files** | Grep | Content search | `Grep "useState"` |
| **Find a specific function** | Serena find_symbol | Semantic understanding | `find_symbol "handleAuth"` |
| **See file structure** | Serena get_symbols_overview | Shows all symbols | `get_symbols_overview "src/"` |
| **Replace entire function** | Serena replace_symbol_body | Clean replacement | Better than manual edit |
| **Add imports/functions** | Serena insert_before/after | Precise placement | No manual line counting |
| **Complex search task** | Task tool | Deploy search specialist | "Find all auth implementations" |
| **Small text change** | Edit or Serena replace_regex | Quick edits | Use wildcards in regex! |
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
├─ Know text content? → Grep  
├─ Know function/class name? → Serena find_symbol
├─ Need to explore structure? → Serena get_symbols_overview
└─ Complex multi-file search? → Task tool with search specialist

Need to edit code?
├─ Replace whole function? → Serena replace_symbol_body
├─ Add new code? → Serena insert_before/after_symbol
├─ Small text change? → Edit or Serena replace_regex
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
├─ Documentation lookup? → Context7
└─ Blog-specific config? → PROJECT-BLOG.md
```

## Tool Combination Patterns

| Workflow | Tool Sequence | Example |
|----------|---------------|---------||
| **Feature Implementation** | Context7 → Serena → TodoWrite → Implementation → Testing | Research → Analyze → Plan → Build → Verify |
| **Bug Fix** | Grep/Serena → Analyze → Edit → Test | Find issue → Understand → Fix → Validate |
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

**Grep + Serena**:
- Grep finds text → Serena understands structure
- Example: Find "TODO" → Understand context