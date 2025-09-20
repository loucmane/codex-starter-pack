---
id: tool-integration
type: integration-guide
category: cross-system
title: Tool Integration Guide
audience: developer
complexity: intermediate
dependencies:
  - system-integration
  - creating-handlers
prerequisites:
  - Understanding of available tools
  - Knowledge of tool interfaces
  - Familiarity with error handling
version: 1.0.0
status: stable
---

# Tool Integration Guide

## Overview

This guide covers integrating tools into the Claude Template System, including the core tools (Read, Write, Grep, etc.) and patterns for adding new tool capabilities.

## Prerequisites

- Understanding of available system tools
- Knowledge of tool interfaces and parameters
- Familiarity with error handling patterns
- Understanding of handler-tool interaction

## Core System Tools

### File Operations

#### Read Tool

```markdown
**Purpose**: Read file contents
**Parameters**:
  - file_path: Absolute path to file
  - limit: Optional line limit
  - offset: Optional starting line
**Returns**: File contents with line numbers
**Error Cases**:
  - File not found
  - Permission denied
  - File too large
```

#### Write Tool

```markdown
**Purpose**: Create or overwrite files
**Parameters**:
  - file_path: Absolute path to file
  - content: Content to write
**Returns**: Success confirmation
**Error Cases**:
  - Invalid path
  - Permission denied
  - Disk full
**Constraint**: Must read before editing existing files
```

#### MultiEdit Tool

```markdown
**Purpose**: Multiple edits to single file
**Parameters**:
  - file_path: Absolute path to file
  - edits: Array of edit operations
    - old_string: Text to replace
    - new_string: Replacement text
    - replace_all: Optional, replace all occurrences
**Returns**: Success with edit count
**Error Cases**:
  - String not found
  - File not found
  - Edit conflicts
```

### Search Operations

#### Grep Tool

```markdown
**Purpose**: Search file contents with regex
**Parameters**:
  - pattern: Regex pattern
  - path: Directory or file to search
  - glob: File pattern filter
  - type: File type filter
  - output_mode: content|files_with_matches|count
  - Various flags: -i, -n, -A, -B, -C
**Returns**: Search results based on mode
**Error Cases**:
  - Invalid regex
  - Path not found
  - No matches
```

#### Glob Tool

```markdown
**Purpose**: Find files by pattern
**Parameters**:
  - pattern: Glob pattern (e.g., **/*.js)
  - path: Optional base directory
**Returns**: List of matching file paths
**Error Cases**:
  - Invalid pattern
  - Directory not found
  - No matches
```

## Tool Integration Patterns

### Pattern 1: Sequential Tool Chain

```markdown
#### Handler: refactor-imports
**Process**:
1. **Grep** to find all import statements
2. **Read** each file with imports
3. **MultiEdit** to update import paths
4. **Write** to create import map

**Tool Coordination**:
- Each tool output feeds next tool
- Error in any step halts chain
- Rollback on failure
```

### Pattern 2: Parallel Tool Execution

```markdown
#### Handler: analyze-codebase
**Process**:
1. Parallel execution:
   - **Glob** to find all source files
   - **Grep** to find TODO comments
   - **Grep** to find FIXME tags
2. Aggregate results
3. **Write** comprehensive report

**Benefits**:
- Faster execution
- Independent operations
- Partial results on failure
```

### Pattern 3: Conditional Tool Selection

```markdown
#### Handler: smart-search
**Process**:
1. Analyze search request
2. IF simple pattern:
   - Use **Grep** with basic pattern
3. ELSE IF file search:
   - Use **Glob** for file patterns
4. ELSE IF complex:
   - Use **Grep** with advanced regex
5. Format and return results
```

## Adding New Tools

### Step 1: Define Tool Interface

```typescript
// Conceptual tool interface
interface CustomTool {
  name: string;
  description: string;
  parameters: ParameterSchema;
  execute(params: any): Promise<ToolResult>;
  validate(params: any): ValidationResult;
}
```

### Step 2: Create Tool Wrapper

```markdown
#### Handler: use-custom-tool
**Purpose**: Wrapper for custom tool integration
**Process**:
1. Validate tool availability
2. Parse and validate parameters
3. Execute tool with error handling
4. Transform results for system
5. Handle cleanup if needed
```

### Step 3: Document Tool Usage

```yaml
# Tool documentation format
tool:
  name: CustomAnalyzer
  description: Analyzes code complexity
  parameters:
    - name: file_path
      type: string
      required: true
      description: File to analyze
    - name: metrics
      type: array
      required: false
      default: ["complexity", "lines"]
  returns:
    type: object
    properties:
      complexity: number
      lines: number
      issues: array
  examples:
    - input: {file_path: "src/main.js"}
      output: {complexity: 15, lines: 200}
```

## Tool Error Handling

### Error Categories

```markdown
## Error Types

### Input Errors
- Invalid parameters
- Missing required fields
- Type mismatches
- Out of range values

### Execution Errors
- Tool not available
- Insufficient permissions
- Resource exhausted
- Timeout exceeded

### Output Errors
- Unexpected format
- Partial results
- Encoding issues
```

### Error Recovery Strategies

```markdown
#### Strategy: Graceful Degradation
**Process**:
1. Try primary tool
2. On failure, try alternative
3. If all fail, provide manual steps
4. Always give user actionable info

**Example**:
1. Try **Grep** for search
2. If fails, try **Read** + filter
3. If fails, suggest manual search
```

```markdown
#### Strategy: Retry with Modification
**Process**:
1. Initial attempt fails
2. Analyze error type
3. Modify parameters
4. Retry with changes
5. Report if still fails

**Example**:
1. **Write** fails with permission error
2. Try different directory
3. Or create with different name
```

## Tool Optimization

### Performance Considerations

```markdown
## Optimization Techniques

### 1. Batch Operations
Instead of:
- Read file1
- Read file2
- Read file3

Do:
- Collect all files
- Read in parallel batch
- Process together

### 2. Early Filtering
Instead of:
- Grep all files
- Filter results

Do:
- Use glob/type filters
- Grep only relevant files

### 3. Result Caching
- Cache expensive searches
- Invalidate on file changes
- Share results across handlers
```

### Resource Management

```markdown
## Resource Limits

### File Operations
- Max file size: 10MB
- Max files open: 100
- Max path length: 255

### Search Operations
- Max results: 10,000
- Max pattern length: 1000
- Timeout: 30 seconds

### Memory Management
- Stream large files
- Process in chunks
- Clear buffers after use
```

## Tool Composition Examples

### Example: Code Migration Tool

```markdown
#### Handler: migrate-codebase
**Tools Used**: Glob, Grep, Read, MultiEdit, Write
**Process**:
1. **Glob** to find all source files
2. For each file:
   a. **Read** current content
   b. **Grep** for migration patterns
   c. **MultiEdit** to apply changes
3. **Write** migration report
4. **Write** rollback script

**Error Handling**:
- Transaction-like approach
- Rollback on any failure
- Detailed error logging
```

### Example: Documentation Generator

```markdown
#### Handler: generate-docs
**Tools Used**: Glob, Read, Grep, Write
**Process**:
1. **Glob** to find code files
2. **Read** each file
3. **Grep** for doc comments
4. Parse and extract docs
5. **Write** formatted documentation

**Optimizations**:
- Parallel file reading
- Incremental updates
- Cache parsed results
```

## Testing Tool Integration

### Unit Tests for Tool Handlers

```markdown
## Test Categories

### Input Validation
- Test with valid inputs
- Test with invalid inputs
- Test edge cases
- Test missing parameters

### Tool Execution
- Test successful execution
- Test tool failures
- Test timeouts
- Test resource limits

### Output Processing
- Test result parsing
- Test error messages
- Test partial results
- Test empty results
```

### Integration Tests

```markdown
## End-to-End Tool Tests

### Test Scenario: File Modification
1. Create test file
2. Read content
3. Search for patterns
4. Apply edits
5. Verify changes
6. Clean up

### Test Scenario: Codebase Analysis
1. Set up test project
2. Run analysis tools
3. Verify all tools execute
4. Check result aggregation
5. Validate report format
```

## Best Practices

### DO:
- ✅ Validate inputs before tool execution
- ✅ Handle all error cases explicitly
- ✅ Provide clear error messages
- ✅ Use appropriate tool for task
- ✅ Clean up resources after use
- ✅ Document tool requirements

### DON'T:
- ❌ Assume tool will always succeed
- ❌ Ignore tool-specific constraints
- ❌ Mix tool responsibilities
- ❌ Skip input validation
- ❌ Forget cleanup on errors
- ❌ Use tools beyond their design

## Common Pitfalls

### Wrong Tool Selection
**Problem**: Using Read for large file search
**Solution**: Use Grep for searching

### Missing Error Handling
**Problem**: Tool fails, handler crashes
**Solution**: Wrap all tool calls in try-catch

### Resource Exhaustion
**Problem**: Opening too many files
**Solution**: Process in batches, close after use

### Performance Issues
**Problem**: Sequential operations slow
**Solution**: Parallelize where possible

## Related Resources

- [System Integration](../guides/system-integration.md)
- [Creating Handlers](../guides/creating-handlers.md)
- [MCP Integration](mcp-integration.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- [Best Practices](../best-practices/handler-design.md)