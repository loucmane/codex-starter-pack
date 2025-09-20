---
id: tool-selection-patterns
type: pattern
category: selection
title: Tool Selection Patterns
pattern_type: operational
complexity: simple
dependencies:
  - templates/shared/tools/tool-selection-matrix.md
related:
  - patterns/selection/handler-selection.md
  - patterns/selection/agent-selection.md
version: 1.0.0
status: stable
---

# Tool Selection Patterns

## Pattern Description
Patterns for choosing the right tool based on the operation type and context. These patterns ensure tools are used according to their intended purpose and capabilities.

## Important Note
**The comprehensive tool selection matrix is maintained at: [Tool Selection Matrix](../../shared/tools/tool-selection-matrix.md)**
This pattern documents the approach to tool selection, while the matrix provides specific mappings.

## Pattern Structure
1. Identify operation type
2. Check tool selection matrix
3. Apply context-specific rules
4. Select appropriate tool
5. Use tool with correct parameters

## When to Use
- Performing file operations
- Searching for code or text
- Making edits to files
- Understanding code structure
- Creating new content

## When NOT to Use
- Tool is explicitly specified in request
- Only one tool can perform the operation
- Emergency override needed

## Tool Selection Process

### Step 1: Operation Classification
Determine the primary operation:
- **Search**: Finding text, code, or patterns
- **Edit**: Modifying existing content
- **Create**: Making new files or content
- **Understand**: Analyzing code structure
- **Navigate**: Moving through file system
- **Execute**: Running commands or scripts

### Step 2: Context Analysis
Consider the context:
- **Target**: Code vs text vs configuration
- **Scope**: Single file vs multiple files
- **Complexity**: Simple vs complex operation
- **Requirements**: Speed vs accuracy vs features

### Step 3: Tool Selection
Apply the selection matrix (see shared resource) based on:
1. Operation type
2. Target type
3. Complexity level
4. Performance requirements

## Common Tool Selection Patterns

### Search Pattern
**Triggers**: search, find, where, locate, "look for"
**Decision Flow**:
1. Simple text search → Use `Grep`
2. Code understanding → Use `mcp__serena__search_for_pattern`
3. Symbol search → Use `mcp__serena__find_symbol`
4. File patterns → Use `Glob`
5. Complex multi-file → Use `Task` with agent

### Edit Pattern
**Triggers**: edit, update, modify, change, fix
**Decision Flow**:
1. Single line change → Use `Edit`
2. Multiple changes → Use `MultiEdit`
3. Symbol refactoring → Consider Serena tools
4. File creation → Use `Write`

### Code Understanding Pattern
**Triggers**: "how does", understand, analyze, structure
**Decision Flow**:
1. Symbol overview → Use `mcp__serena__get_symbols_overview`
2. Reference finding → Use `mcp__serena__find_referencing_symbols`
3. Deep analysis → Use `Task` with specialized agent

## Tool Selection Anti-Patterns

### Common Mistakes to Avoid
1. **Using grep for code search** → Always prefer Serena for semantic understanding
2. **Manual timestamp typing** → Always use `date` command
3. **Using bash ls** → Use `LS` tool instead
4. **Multiple greps** → Use Task tool for complex searches
5. **Wrong tool for file type** → Check matrix for file-specific tools

### Decision Checkpoints
Before selecting a tool, ask:
- Is this code or plain text?
- Do I need semantic understanding?
- Is this a simple or complex operation?
- Are there multiple steps involved?
- Is there a specialized tool for this?

## Examples

### Simple Text Search
- Request: "Find TODO comments"
- Analysis: Simple text pattern
- Selection: `Grep` tool
- Command: `Grep` with pattern "TODO"

### Code Understanding
- Request: "How does the auth system work?"
- Analysis: Needs semantic understanding
- Selection: Serena search tools
- Command: `mcp__serena__search_for_pattern` with "auth"

### Complex Operation
- Request: "Refactor all error handling"
- Analysis: Multi-file, complex changes
- Selection: `Task` tool with agent
- Command: Task with refactoring specialist

## Tool Capabilities Reference

### Quick Reference
- **Grep**: Fast text search, regex support
- **Serena**: Semantic code understanding
- **Glob**: File pattern matching
- **Edit/MultiEdit**: File modifications
- **Write**: New file creation
- **Task**: Complex multi-step operations
- **LS**: Directory listing

For detailed tool mappings, see: [Tool Selection Matrix](../../shared/tools/tool-selection-matrix.md)

## Variations

### Performance-Optimized Selection
When speed is critical, prefer simpler tools even if less feature-rich

### Accuracy-Optimized Selection
When correctness is critical, use semantic tools even if slower

### Interactive Selection
When unsure, present tool options to user

## Related Patterns
- [Handler Selection](handler-selection.md) - Choosing handlers
- [Agent Selection](agent-selection.md) - Selecting specialist agents
- [Code Creation](../integration/code-creation.md) - Creating new code

## Handler References
[Handler: tool-selection migrated to handlers/orchestrators/tool-selection.md]
[Handler: code-creation migrated to handlers/operators/development/code-creator.md]