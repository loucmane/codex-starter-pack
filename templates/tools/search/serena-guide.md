---
id: serena-guide
type: tool-guide
category: search
title: Serena MCP Integration Guide
version: 1.0.0
description: Complete guide for Serena semantic code analysis tool
status: stable
tools: [mcp__serena__search_for_pattern, mcp__serena__find_symbol, mcp__serena__get_symbols_overview]
---

# Serena MCP Integration Guide

## Overview

Serena is a semantic code analysis MCP tool that provides intelligent code understanding, search, and refactoring capabilities. Unlike text-based search tools, Serena understands code structure and relationships.

## Initial Serena Activation (First Time)

```bash
# Read instructions first
mcp__serena__initial_instructions

# Then activate with project name (configured in your client)
mcp__serena__activate_project project="starter-pack-monorepo"

# Perform onboarding
mcp__serena__onboarding
```

**Note**: The project name in Serena is "blog", not "MomsBlog". Always use the full path.

## Standard Session Starters with Serena

### 1. **New Development Session** (Most Common)
```
mcp__serena__activate_project project="starter-pack-monorepo"
read all memories, and check sessions/current for previous work.
Today I'm working on [specific task/feature].
```

### 2. **Continuing Previous Work**
```
mcp__serena__activate_project project="starter-pack-monorepo"
read the most recent session memory and sessions/current.
Let's continue where we left off.
```

### 3. **TaskMaster Integration**
```
mcp__serena__activate_project project="starter-pack-monorepo"
read all memories.
Check TaskMaster for current task status, then help me work on task [ID].
```

## Serena Tools for This Project

### Semantic Code Analysis

```bash
# Find components using theme
mcp__serena__find_symbol --name_path="theme" --substring_matching=true

# Show package relationships
mcp__serena__get_symbols_overview --relative_path="packages"

# Find type usage across packages
mcp__serena__search_for_pattern --substring_pattern="Animal.*type"
```

### Intelligent Refactoring

```bash
# Update component to standards
mcp__serena__replace_symbol_body --name_path="Button" --relative_path="components/Button.tsx"

# Fix import order
mcp__serena__find_symbol --name_path="import" --include_kinds=[15]
```

## Serena Memory Management

### Create Session Memory

```bash
# Format: session_YYYY-MM-DD_description
mcp__serena__write_memory \
  --memory_name="session_$(date +%Y-%m-%d)_unified_workflow_design" \
  --content="[session details]"
```

### List and Read Memories

```bash
# See all memories
mcp__serena__list_memories

# Read specific memory
mcp__serena__read_memory --memory_file_name="session_2025-01-06_orchestration.md"
```

## Serena's Superpowers

- **Semantic understanding** - Knows code structure, not just text
- **Smart refactoring** - Updates all references automatically
- **Minimal reading** - Only reads what's needed, not entire files
- **Project memory** - Remembers important context between sessions
- **Intelligent regex** - Uses wildcards for efficient replacements

## When to Use Serena vs Other Tools

| Need | Use Serena | Not Serena |
|------|------------|------------|
| Find function/class by name | ✓ `find_symbol` | × grep |
| Understand code structure | ✓ `get_symbols_overview` | × manual reading |
| Find who uses a symbol | ✓ `find_referencing_symbols` | × grep |
| Replace entire function | ✓ `replace_symbol_body` | × Edit |
| Add code before/after symbol | ✓ `insert_before/after_symbol` | × manual line counting |
| Search code patterns | ✓ `search_for_pattern` | × grep for code |
| Simple text search | × Use Grep | ✓ For TODO, logs |
| File modifications | × Use Edit/Write | ✓ For understanding only |

## Common Patterns

### Code Navigation & Understanding

- **Find specific symbol**: `mcp__serena__find_symbol`
- **See file structure**: `mcp__serena__get_symbols_overview`
- **Find references**: `mcp__serena__find_referencing_symbols`
- **Search patterns**: `mcp__serena__search_for_pattern`

### Code Analysis Before Editing

1. Use Serena to understand structure
2. Find exact locations with Serena
3. Switch to Edit/Write for modifications
4. Never use Serena for file writes

## Troubleshooting

### Activation Issues

```bash
# If "project not found"
- Use full absolute path
- Check .serena/ exists
- Try deactivating and reactivating

# If "no memories found"
- Normal for new projects
- Create first memory after work
```

### Search Not Finding Results

- Use substring matching for partial names
- Check relative_path is correct
- Try broader pattern first, then narrow

## Best Practices

1. **Always activate project first** in new sessions
2. **Use full paths** to avoid ambiguity
3. **Read memories** to maintain context
4. **Create memories** at session end
5. **Understand before editing** - Serena for analysis, Edit for changes
6. **Use semantic search** for code, not text patterns