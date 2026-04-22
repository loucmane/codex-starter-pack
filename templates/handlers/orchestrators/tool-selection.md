---
id: tool-selection
name: Tool Selection
title: Tool Selection
role: orchestrator
type: orchestrator
domain: search
stability: stable
status: stable
triggers:
  - "search"
  - "find"
  - "where"
  - "how does"
  - "look for"
  - "locate"
dependencies:
  - search-code
  - grep-search
  - list-files
tools:
  - Grep
  - Serena
version: 1.0.0
---

#### Pattern: tool-selection {#tool-selection}
**Triggers**: search, find, where, "how does", look for, locate
**Pre-conditions**: Operation type clear
**Process**:
1. Identify operation type
2. Load TOOLS.md#tool-selection-matrix
3. Route to appropriate handler:
   - Code understanding → TOOLS.md#search-code
   - Simple text → TOOLS.md#grep-search
   - File listing → TOOLS.md#list-files
**Success**: Correct tool selected
**Failure**: Ask for clarification
**Examples**:
- "Find TODO comments" → Uses Grep
- "How does auth work?" → Uses Serena
- "Where is UserService?" → Uses Serena find_symbol

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/tool-selection.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
