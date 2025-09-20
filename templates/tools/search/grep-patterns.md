---
id: grep-patterns
type: tool-guide
category: search
title: Grep Pattern Search Guide
version: 1.0.0
description: Text pattern search with Grep tool
status: stable
tools: [Grep, Glob]
---

# Grep Pattern Search Guide

## Overview

Grep is the primary tool for text-based pattern searching in files. Use it for finding literal text, log messages, TODOs, and simple patterns. For semantic code understanding, use Serena instead.

## When to Use Grep vs Serena

### Use Grep For:
- Simple text patterns (TODO, FIXME, logs)
- Error messages and strings
- Configuration values
- Comments and documentation
- Quick text searches

### Use Serena For:
- Code structure understanding
- Function/class definitions
- Symbol references
- Import analysis
- Semantic patterns

## Basic Grep Usage

```bash
# Simple text search
Grep --pattern "TODO" --path "."

# Case insensitive
Grep --pattern "error" -i

# Show context lines
Grep --pattern "function" -C 3

# Specific file types
Grep --pattern "import" --type "js"

# With line numbers
Grep --pattern "console.log" -n
```

## Output Modes

```bash
# Show matching lines (default with context)
Grep --pattern "error" --output_mode "content"

# Show only file paths
Grep --pattern "TODO" --output_mode "files_with_matches"

# Show match counts
Grep --pattern "import" --output_mode "count"
```

## Advanced Patterns

### Regex Patterns

```bash
# Function definitions
Grep --pattern "function\\s+\\w+\\s*\\("

# Import statements
Grep --pattern "^import.*from"

# API routes
Grep --pattern "/api/.*POST"

# Error handling
Grep --pattern "catch\\s*\\(.*\\)"
```

### File Filtering

```bash
# Search in specific extensions
Grep --pattern "useState" --glob "*.tsx"

# Exclude directories
Grep --pattern "config" --glob "!node_modules/**"

# Multiple patterns
Grep --pattern "(TODO|FIXME|HACK)" --glob "**/*.js"
```

### Context Control

```bash
# Lines before match
Grep --pattern "error" -B 2

# Lines after match
Grep --pattern "function" -A 5

# Both before and after
Grep --pattern "class" -C 3

# Limit output
Grep --pattern "import" --head_limit 10
```

## Multiline Patterns

```bash
# Enable multiline mode for patterns spanning lines
Grep --pattern "struct\\s+\\{[\\s\\S]*?field" --multiline true

# Match across line boundaries
Grep --pattern "function.*\\n.*\\{" --multiline true
```

## Common Search Patterns

### Development Markers

```bash
# Find all TODOs
Grep --pattern "TODO:?" -i

# Find debug statements
Grep --pattern "console\\.(log|debug|warn|error)"

# Find comments
Grep --pattern "//.*|/\\*.*\\*/"
```

### Code Patterns

```bash
# Find async functions
Grep --pattern "async\\s+function"

# Find React hooks
Grep --pattern "use[A-Z]\\w+\\("

# Find test files
Grep --glob "*.test.js" --output_mode "files_with_matches"
```

### Configuration

```bash
# Find environment variables
Grep --pattern "process\\.env\\."

# Find API endpoints
Grep --pattern "['\"]/(api|v[0-9])/"

# Find port numbers
Grep --pattern "port.*[0-9]{4}"
```

## Performance Tips

1. **Use glob filters** to limit search scope
2. **Use file type** parameter for common extensions
3. **Limit output** with head_limit for large results
4. **Be specific** with patterns to reduce false positives
5. **Use output modes** wisely:
   - `files_with_matches` for discovery
   - `content` for investigation
   - `count` for statistics

## Glob Patterns for File Finding

```bash
# Find all test files
Glob --pattern "**/*.test.js"

# Find components
Glob --pattern "**/components/**/*.tsx"

# Find config files
Glob --pattern "**/*config*"

# Exclude node_modules
Glob --pattern "**/*.js" --path "src"
```

## Error Handling

### No Results Found
- Check pattern syntax (escape special chars)
- Broaden search scope
- Verify file paths
- Try case-insensitive search

### Too Many Results
- Add more specific patterns
- Use glob to filter files
- Apply head_limit
- Use file type filters

## Integration with Other Tools

### Grep + Serena Workflow

1. Use Grep to find text occurrences
2. Use Serena to understand code context
3. Use Edit to make changes

### Grep + Task Tool

For complex searches:
1. Start with Grep for initial discovery
2. Deploy Task tool for deep analysis
3. Use specialist for pattern recognition

## Best Practices

1. **Start broad, then narrow** - Cast wide net first
2. **Use appropriate output mode** - Don't fetch content if you only need files
3. **Escape regex properly** - Double backslash in patterns
4. **Combine with glob** - Filter files before searching
5. **Check multiline needs** - Enable for cross-line patterns
6. **Prefer Serena for code** - Use Grep for text only

## Common Mistakes to Avoid

❌ Using bash grep instead of Grep tool
❌ Using Grep for semantic code search (use Serena)
❌ Forgetting to escape regex special characters
❌ Not using glob to filter large codebases
❌ Using content mode when files_with_matches suffices

## Quick Reference

| Task | Command |
|------|--------|
| Find TODO comments | `Grep --pattern "TODO"` |
| Find in JavaScript only | `Grep --pattern "pattern" --type "js"` |
| Find with context | `Grep --pattern "error" -C 3` |
| Count occurrences | `Grep --pattern "import" --output_mode "count"` |
| Find files with pattern | `Grep --pattern "test" --output_mode "files_with_matches"` |
| Case insensitive | `Grep --pattern "error" -i` |
| Multiline pattern | `Grep --pattern "pattern" --multiline true` |
| Limit results | `Grep --pattern "log" --head_limit 20` |