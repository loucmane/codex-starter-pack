---
id: tools-index
type: tool-guide
category: index
title: Tool Configuration and Usage Guide
version: 2.0.0
description: Central hub for MCP tool configurations and usage patterns
status: stable
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


# Tool Configuration and Usage Guide

This document serves as the central hub for all tool configurations, usage patterns, and the unified delegation-first workflow.

## 🚨 MANDATORY TOOL SELECTION ROUTER - CHECK BEFORE EVERY TOOL USE! 🚨

**NEVER** use a tool directly. **ALWAYS** follow this protocol:
1. **STATE**: "I need to [action]"
2. **CHECK**: Router table in [tool-selection-matrix](../shared/tools/tool-selection-matrix.md)
3. **CONFIRM**: "Using [tool] for [purpose]"
4. **JUSTIFY**: If deviating, explain why

## 🎯 Quick Navigation

### Core Tool Guides
- **[Tool Selection Matrix](../shared/tools/tool-selection-matrix.md)** - Action → Tool mapping and decision funnel
- **[Serena Search Guide](search/serena-guide.md)** - Semantic code analysis and search
- **[Grep Patterns](search/grep-patterns.md)** - Pattern matching and text search
- **[Edit Strategies](file/edit-strategies.md)** - File modification best practices
- **[Multi-Edit Guide](file/multi-edit.md)** - Batch file operations
- **[Git Commands](git/commands.md)** - Version control operations
- **[Task Agent Usage](task/agent-usage.md)** - Intelligent delegation patterns

## Core Tools Overview

### Built-in Tools (Always Available)

```yaml
File Operations:
  - Read: View file contents
  - Write: Create new files
  - Edit/MultiEdit: Modify existing files
  - Bash: Execute commands
  - Grep/Glob: Search patterns
  - LS: List directories

Task Tool:
  - Purpose: Deploy specialists for complex work
  - Type: Built-in (NOT MCP)
  - Key Feature: Enables unified workflow
```

### MCP Tools (Project-Specific)

```yaml
Serena:
  - Purpose: Semantic code analysis
  - Strengths: Understanding relationships, intelligent refactoring
  - Project: Use full path to avoid errors

TaskMaster:
  - Purpose: Project planning and tracking
  - Strengths: Task dependencies, progress tracking
  - Integration: Syncs with TodoWrite/TodoRead

Context7:
  - Purpose: Latest documentation lookup
  - Usage: Single topics for best results
  - Example: "React hooks", not "React"
```

## ULTRATHINK Integration {#ultrathink-integration}

This file participates in the ULTRATHINK system:

### VOID Resolution
- **S = VOID** → See [resolve-session-void](../conventions#resolve-session-void)
- **W = VOID** → See [resolve-work-void](../workflows#resolve-work-void)
- **H = VOID** → See [resolve-handler-void](../REGISTRY.md#resolve-handler-void)

### Handler Requirements
All tool selection handlers expect valid [S:W:H] context before execution. The tool router MUST verify context before proceeding.

## 📚 See Also

- **[Domain Workflows](../engine/README.md)** - Complete development workflows
- **[CONVENTIONS.md](../conventions)** - Code and communication standards
- **[REGISTRY.md](../REGISTRY.md)** - Handler registry and navigation

## Progress Log

- **2026-05-07 18:29** — [S:20260507|W:task108-legacy-project-blog-cleanup|H:templates/tools/index.md|E:docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/reports/legacy-project-blog-cleanup/project-blog-live-refs-2026-05-07.txt] Removed the stale PROJECT-BLOG see-also link after deleting the old blog-era template.

---

The magic isn't in the tools - it's in how they work together. One workflow, many specialists, unified success.
