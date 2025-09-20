---
id: multi-edit
type: tool-guide
category: file
title: Multi-Edit Batch Operations Guide
version: 1.0.0
description: Efficient batch editing for multiple changes in single files
status: stable
tools: [MultiEdit]
---

# Multi-Edit Batch Operations Guide

## Overview

MultiEdit is a powerful tool for making multiple changes to a single file in one atomic operation. All edits succeed or none are applied, ensuring file consistency.

## When to Use MultiEdit

### Perfect For:
- Multiple related changes in one file
- Renaming variables/functions throughout
- Updating multiple config values
- Batch import additions
- Series of bug fixes
- Refactoring patterns

### Not For:
- Changes across multiple files (use separate operations)
- Complete file rewrites (use Write)
- Single change (use Edit)

## Basic MultiEdit Structure

```python
MultiEdit(
  file_path="/absolute/path/to/file",
  edits=[
    {"old_string": "find1", "new_string": "replace1"},
    {"old_string": "find2", "new_string": "replace2"},
    {"old_string": "find3", "new_string": "replace3", "replace_all": true}
  ]
)
```

## Key Concepts

### Sequential Processing

Edits are applied in order:

```python
# Edit 1 applies first
{"old_string": "var x = 1;", "new_string": "let x = 1;"}
# Edit 2 works on result of Edit 1
{"old_string": "let x = 1;", "new_string": "let x = 2;"}
# Final result: let x = 2;
```

### Atomic Operations

```yaml
All edits must succeed:
  - If any edit fails → No changes applied
  - File remains in original state
  - Error indicates which edit failed
```

### Replace All Option

```python
# Replace all occurrences
{"old_string": "oldVar", "new_string": "newVar", "replace_all": true}

# Replace only first occurrence (default)
{"old_string": "TODO", "new_string": "DONE"}  # replace_all: false by default
```

## Common Patterns

### Pattern 1: Variable Renaming

```python
MultiEdit(
  file_path="/src/auth.js",
  edits=[
    {"old_string": "userId", "new_string": "userID", "replace_all": true},
    {"old_string": "getUserId", "new_string": "getUserID", "replace_all": true},
    {"old_string": "setUserId", "new_string": "setUserID", "replace_all": true}
  ]
)
```

### Pattern 2: Adding Multiple Imports

```python
MultiEdit(
  file_path="/src/component.tsx",
  edits=[
    {
      "old_string": "import React from 'react';",
      "new_string": "import React from 'react';\nimport { useState } from 'react';"
    },
    {
      "old_string": "import { useState } from 'react';",
      "new_string": "import { useState, useEffect } from 'react';"
    },
    {
      "old_string": "import { useState, useEffect } from 'react';",
      "new_string": "import { useState, useEffect, useCallback } from 'react';"
    }
  ]
)
```

### Pattern 3: Config Updates

```python
MultiEdit(
  file_path="/config/app.json",
  edits=[
    {"old_string": '"port": 3000', "new_string": '"port": 8080'},
    {"old_string": '"debug": true', "new_string": '"debug": false'},
    {"old_string": '"version": "1.0.0"', "new_string": '"version": "1.1.0"'}
  ]
)
```

### Pattern 4: Method Updates

```python
MultiEdit(
  file_path="/src/service.js",
  edits=[
    {
      "old_string": "async fetchData() {",
      "new_string": "async fetchData(options = {}) {"
    },
    {
      "old_string": "const response = await fetch(url);",
      "new_string": "const response = await fetch(url, options);"
    },
    {
      "old_string": "return response.json();",
      "new_string": "return response.ok ? response.json() : null;"
    }
  ]
)
```

### Pattern 5: Comment Updates

```python
MultiEdit(
  file_path="/src/utils.js",
  edits=[
    {"old_string": "// TODO:", "new_string": "// DONE:", "replace_all": true},
    {"old_string": "// FIXME:", "new_string": "// FIXED:", "replace_all": true},
    {"old_string": "/* Old comment */", "new_string": "/* Updated comment */"}
  ]
)
```

## Advanced Techniques

### Chained Transformations

```python
# Transform code style progressively
MultiEdit(
  file_path="/legacy/code.js",
  edits=[
    # Step 1: var to let
    {"old_string": "var ", "new_string": "let ", "replace_all": true},
    # Step 2: specific let to const
    {"old_string": "let CONFIG", "new_string": "const CONFIG"},
    # Step 3: update specific values
    {"old_string": "= null;", "new_string": "= undefined;", "replace_all": true}
  ]
)
```

### Conditional Replacements

```python
# Different replacements based on context
MultiEdit(
  file_path="/src/api.js",
  edits=[
    # In function context
    {"old_string": "function api() {\n  return fetch", 
     "new_string": "async function api() {\n  return await fetch"},
    # In different context
    {"old_string": "exports.api", "new_string": "module.exports.api"}
  ]
)
```

## Error Handling

### Common Errors

1. **Text Not Found**
   ```python
   # Error: old_string not found in file
   Solution: Read file first, verify exact text
   ```

2. **Sequential Conflict**
   ```python
   # Edit 2 can't find text modified by Edit 1
   Solution: Account for previous changes
   ```

3. **Duplicate Edits**
   ```python
   # Same old_string in multiple edits
   Solution: Use replace_all or unique contexts
   ```

### Planning for Success

```yaml
Before MultiEdit:
  1. Read the file completely
  2. List all changes needed
  3. Order edits logically
  4. Consider edit interactions
  5. Test with small batch first
```

## Best Practices

### DO:
✓ Read file first to verify content
✓ Order edits from most specific to general
✓ Use replace_all for consistent renaming
✓ Include enough context for uniqueness
✓ Test with preview if uncertain

### DON'T:
❌ Apply conflicting edits
❌ Assume order doesn't matter
❌ Use for cross-file changes
❌ Make edits without reading first
❌ Overlap edit regions

## Performance Considerations

```yaml
Optimal Usage:
  - Batch size: 5-20 edits per operation
  - File size: Works best under 10,000 lines
  - Complexity: Simple replacements fastest
  
For Large Operations:
  - Split into multiple MultiEdit calls
  - Group related changes
  - Verify after each batch
```

## Integration Examples

### With Read Tool

```python
# 1. Read to understand
Read --file_path "/src/component.tsx"

# 2. Plan edits based on content
# 3. Execute MultiEdit
MultiEdit(file_path="/src/component.tsx", edits=[...])

# 4. Read again to verify
Read --file_path "/src/component.tsx"
```

### With Grep Tool

```python
# 1. Find all occurrences
Grep --pattern "oldPattern"

# 2. Build edit list from results
# 3. Apply with MultiEdit
MultiEdit(file_path="...", edits=[...], replace_all=true)
```

## Quick Reference

| Use Case | Example |
|----------|---------||
| Rename all | `{"old": "x", "new": "y", "replace_all": true}` |
| Add imports | Sequential import additions |
| Fix typos | Multiple corrections in order |
| Update configs | Batch value changes |
| Refactor patterns | Progressive transformations |
| Remove code | Replace with empty string |
| Add comments | Insert before/after markers |