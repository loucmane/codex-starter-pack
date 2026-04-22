---
id: tool-selection-matrix
title: Tool Selection Matrix
type: decision-matrix
category: selection
status: stable
usage: Determines which tool to use for specific tasks
version: 1.0.0
---

# Tool Selection Matrix

Guides tool selection based on task requirements and problem types.

## Input
Task type or problem to solve

## Output
Recommended tool(s) and usage approach

## Problem Type → Solution Matrix

| Problem | Primary Solution | Fallback | Tools |
|---------|-----------------|----------|-------|
| Can't find symbol | find_symbol with name_path | search_for_pattern | Serena |
| Test failing | Read test, check implementation | debug-issue handler | Grep + Read |
| Build error | Check error message, find file | Fix syntax/imports | LS + Read |
| Type error | Find type definition | Add/fix types | find_symbol |
| Performance issue | Profile first | optimize-code handler | Analyze |
| Security vulnerability | security-check handler | Get expert help | Tools |
| Merge conflict | Review both sides | Manual resolution | Git |
| Deployment failure | Check logs first | Rollback if needed | Logs + Git |
| API not working | Check request/response | Debug endpoint | curl + logs |
| Database issue | Check migrations | Restore backup | psql/mysql |
| Memory leak | Profile heap | Restart service | DevTools |
| Slow queries | Analyze query plan | Add indexes | EXPLAIN |
| Race condition | Add proper locking | Refactor flow | Debug |
| Circular dependency | Map dependencies | Refactor structure | find_referencing |
| Missing handler | Search similar | Create new one | templates/patterns/ |
| File not found | Verify path exists | Search for file | LS + Glob |
| Import error | Check file location | Fix import path | find_symbol |
| Syntax error | Find exact location | Fix syntax | Read + Edit |
| Network timeout | Retry with backoff | Check connection | curl + ping |
| Version mismatch | Check requirements | Update deps | package.json |

## Tool Capabilities

### Serena (MCP)
- **Best for**: Symbol search, references, code navigation
- **Use when**: Need semantic understanding
- **Commands**: find_symbol, find_referencing, search_for_pattern

### Grep
- **Best for**: Text pattern matching, log searching
- **Use when**: Need fast text search
- **Options**: -r (recursive), -i (case-insensitive), -n (line numbers)

### Read
- **Best for**: File content inspection
- **Use when**: Need to see exact content
- **Limitation**: File must exist

### Edit/MultiEdit
- **Best for**: File modifications
- **Use when**: Making changes to code
- **Rule**: Read file first

### Git
- **Best for**: Version control operations
- **Use when**: Managing code history
- **Commands**: status, diff, commit, push

## Selection Rules

1. **Search Operations**
   - Code symbols → Serena
   - Text patterns → Grep
   - File names → Glob/LS

2. **File Operations**
   - View content → Read
   - Modify content → Edit/MultiEdit
   - Find files → Glob

3. **Code Analysis**
   - Symbol usage → find_referencing
   - Type checking → find_symbol
   - Pattern analysis → search_for_pattern

4. **Debugging**
   - Error location → Read + line number
   - Stack trace → Follow file:line
   - Variable values → Debug tools

## Tool Combinations

| Task | Tool Sequence |
|------|--------------|
| Fix bug | Grep error → Read file → Edit fix → Test |
| Find usage | find_symbol → find_referencing → Read contexts |
| Refactor | find_referencing → MultiEdit all → Test |
| Debug | Read error → Grep pattern → Edit fix |
| Review | LS files → Read each → Comment |

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/selection/tool-selection.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
