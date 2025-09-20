---
id: edit-strategies
type: tool-guide
category: file
title: File Edit Strategies Guide
version: 1.0.0
description: Best practices for file editing and modification
status: stable
tools: [Edit, Read, Write]
---

# File Edit Strategies Guide

## Overview

File editing is a critical operation that requires careful planning and execution. This guide covers strategies for safe and effective file modifications.

## Golden Rules of File Editing

1. **ALWAYS Read Before Edit** - Never edit blind
2. **Use the Right Tool** - Edit for changes, Write for new files
3. **Preserve Functionality** - Don't break existing code
4. **Match Style** - Follow existing patterns
5. **Verify Changes** - Check your modifications

## Tool Selection for File Operations

### When to Use Each Tool

| Operation | Tool | When to Use |
|-----------|------|-------------|
| View file | Read | Before any edit, understanding code |
| Create new file | Write | New components, configs, docs |
| Modify existing | Edit | Small to medium changes |
| Multiple changes | MultiEdit | Several edits in same file |
| Replace function | Serena | Complete symbol replacement |
| Add imports | Serena | Precise placement needed |

## Pre-Edit Checklist

```yaml
Before Editing:
  ✓ Read the entire file
  ✓ Understand the context
  ✓ Identify exact change location
  ✓ Check for dependencies
  ✓ Note formatting style
  ✓ Plan the edit precisely
```

## Edit Strategies

### Strategy 1: Surgical Precision

For small, specific changes:

```python
# 1. Read the file
Read --file_path "src/config.js"

# 2. Identify exact text
# Find: port: 3000
# Plan: port: 8080

# 3. Execute precise edit
Edit --old_string "port: 3000" --new_string "port: 8080"
```

### Strategy 2: Context-Aware Editing

For changes requiring context:

```python
# 1. Read with line numbers
Read --file_path "src/auth.js" --line_numbers

# 2. Include enough context to be unique
Edit --old_string "function login(user) {\n  // Old implementation\n  return false;\n}" \
     --new_string "function login(user) {\n  // New secure implementation\n  return validateUser(user);\n}"
```

### Strategy 3: Multi-Line Replacements

For complex multi-line edits:

```python
# Include full context with exact formatting
Edit --old_string "class UserService {\n  constructor() {\n    this.users = [];\n  }" \
     --new_string "class UserService {\n  constructor() {\n    this.users = [];\n    this.sessions = new Map();\n  }"
```

### Strategy 4: Adding New Code

For inserting new functions or sections:

```python
# Find a unique anchor point
Edit --old_string "// End of utility functions\n\nexport {" \
     --new_string "// End of utility functions\n\nfunction newHelper() {\n  return true;\n}\n\nexport {"
```

## Common Edit Patterns

### Adding Imports

```python
# At file start
Edit --old_string "import React from 'react';" \
     --new_string "import React from 'react';\nimport { useState } from 'react';"

# Or use Serena for precise placement
mcp__serena__insert_before_symbol
```

### Modifying Functions

```python
# Small change within function
Edit --old_string "return null;" \
     --new_string "return defaultValue;"

# Complete function replacement - use Serena
mcp__serena__replace_symbol_body
```

### Updating Configuration

```python
# JSON config
Edit --old_string '"version": "1.0.0"' \
     --new_string '"version": "1.1.0"'

# Environment variables
Edit --old_string "NODE_ENV=development" \
     --new_string "NODE_ENV=production"
```

### Fixing Bugs

```python
# Include enough context
Edit --old_string "if (user.role = 'admin')" \
     --new_string "if (user.role === 'admin')"
```

## Error Prevention

### Common Pitfalls

1. **Whitespace Mismatches**
   ```python
   # WRONG - tabs vs spaces
   Edit --old_string "\tfunction" --new_string "  function"
   
   # RIGHT - match exactly
   Edit --old_string "\tfunction" --new_string "\tfunction"
   ```

2. **Partial Matches**
   ```python
   # WRONG - too generic
   Edit --old_string "return" --new_string "return value"
   
   # RIGHT - include context
   Edit --old_string "return;\n}" --new_string "return value;\n}"
   ```

3. **Line Ending Issues**
   ```python
   # Include line endings in multi-line edits
   Edit --old_string "line1\nline2" --new_string "line1\nmodified\nline2"
   ```

## Edit Verification

### Post-Edit Checks

```yaml
After Editing:
  1. Re-read the edited section
  2. Verify the change took effect
  3. Check surrounding code intact
  4. Look for broken dependencies
  5. Test if applicable
```

### Rollback Strategy

```python
# If edit goes wrong
1. Note the bad edit
2. Read current state
3. Plan corrective edit
4. Apply fix
5. Verify restoration
```

## Working with Special Files

### Package.json

```python
# Dependencies - be precise
Edit --old_string '"react": "^17.0.0",' \
     --new_string '"react": "^18.0.0",'
```

### Configuration Files

```python
# YAML - match indentation exactly
Edit --old_string "  port: 3000" \
     --new_string "  port: 8080"

# TOML - preserve structure
Edit --old_string "[server]\nport = 3000" \
     --new_string "[server]\nport = 8080"
```

### Markdown Files

```python
# Preserve formatting
Edit --old_string "## Old Section" \
     --new_string "## New Section"
```

## Integration with Other Tools

### Serena + Edit Workflow

1. Use Serena to understand structure
2. Find exact symbol locations
3. Switch to Edit for modifications
4. Never use Serena for writes

### Read + Edit + Verify

1. Read file completely
2. Plan edit precisely
3. Execute edit
4. Read again to verify

## Best Practices

1. **Batch Related Changes** - Use MultiEdit for multiple changes
2. **Preserve Formatting** - Match existing style exactly
3. **Include Context** - Avoid ambiguous matches
4. **Test After Editing** - Verify functionality preserved
5. **Document Changes** - Update comments if needed
6. **Use Version Control** - Commit before major edits

## Quick Reference

| Scenario | Strategy |
|----------|----------|
| Change single value | Precise edit with context |
| Add new function | Find anchor point, insert |
| Update multiple lines | MultiEdit or Serena replace |
| Fix syntax error | Include surrounding context |
| Add import | Edit at top or Serena insert |
| Rename variable | MultiEdit with replace_all |
| Delete code | Include full block to remove |
| Modify config | Match format exactly |