---
trigger: About to use Write on non-existent file
title: Before Creating New Files
action: Check if similar file exists that should be edited instead
blocks: Cannot create without justification
category: file-operations
type: behavior
enforcement: mandatory
status: stable
version: 1.0.0
---

# Before Creating New Files

## Trigger Condition
This behavior fires whenever:
- About to use Write tool on a non-existent path
- Planning to create a new file
- Suggesting new file creation
- Initializing new components or modules

## Required Action
```
1. Check if a similar file already exists:
   - Use Glob to find files with similar names
   - Search for files in the same directory
   - Look for files with similar purpose
   
2. Verify the need for a new file:
   - Is there an existing file that could be edited?
   - Would adding to an existing file be better?
   - Is this file explicitly requested by user?
   
3. Check naming conventions:
   mcp__serena__search_for_pattern --substring_pattern "File Creation Rules" --relative_path "templates/conventions/"
   
4. Only create if:
   - No suitable existing file found
   - New file is explicitly needed
   - Follows naming conventions
```

## Blocking Gate
**CANNOT PROCEED** with file creation until:
- Existing files have been checked
- Creation is justified (not just convenient)
- User explicitly requested OR truly necessary
- Naming conventions are followed

## Satisfaction Criteria
✓ Searched for similar existing files
✓ Confirmed no suitable file to edit instead
✓ Creation is justified and necessary
✓ File name follows conventions
✓ Location is appropriate

## Core Principle
**ALWAYS prefer editing existing files over creating new ones**

This principle prevents:
- Unnecessary file proliferation
- Duplicate functionality
- Scattered documentation
- Maintenance burden

## Example Workflows

### ❌ Wrong Approach
```
User: "Add error handling"
AI: Creates new error-handler.js file
Problem: Could have added to existing utils.js
```

### ✅ Correct Approach
```
User: "Add error handling"
AI: 
1. Searches for existing error handling files
2. Finds utils.js with some error utilities
3. Edits utils.js to add new error handling
```

### When Creation IS Justified
```
User: "Create a new component for user profile"
AI:
1. Checks components/ directory
2. No UserProfile component exists
3. Creation justified → proceeds with new file
```

## Special Cases

### Documentation Files
- **NEVER** proactively create README.md or docs
- Only create if explicitly requested
- Check if docs can be added to existing files

### Test Files
- Test files follow source file naming
- Usually justified when source file exists
- Follow test file conventions

### Work Tracking
- Work folders require specific 7-file structure
- These are always justified when starting work
- Must follow ALL CAPS naming convention

## Cross-References
- [CONVENTIONS.md#file-creation-rules](../../conventions) - Creation rules
- [templates/behaviors/file-operations/before-edit.md](before-edit.md) - Editing existing files
- [work-tracking/update-tracker.md](../work-tracking/update-tracker.md) - Work file creation

## Error Cases
- **User insists on new file**: Create but note preference for editing
- **Ambiguous need**: Ask user to clarify
- **Convention conflict**: Follow most specific rule

## Exceptions
These files can be created without extensive justification:
- Temporary files (will be deleted)
- Cache files (generated)
- Work tracking structure (required format)
- Test files (when source exists)
- Config files (when explicitly needed)

## Why This Gate Exists
- Reduces file sprawl
- Maintains organized codebase
- Prevents duplicate code
- Simplifies maintenance
- Follows "prefer editing" principle

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/file-operations/before-create.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
