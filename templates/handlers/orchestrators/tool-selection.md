---
id: tool-selection
name: Tool Selection
role: orchestrator
domain: search
stability: stable
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