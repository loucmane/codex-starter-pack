---
trigger: About to use Edit/Write/MultiEdit on existing file
title: Before Any File Edit
action: Check file-specific conventions before editing
blocks: Cannot edit until conventions checked
category: file-operations
type: behavior
enforcement: mandatory
status: stable
version: 1.0.0
---

# Before Any File Edit

## Trigger Condition
This behavior fires whenever:
- About to use Edit tool on any file
- About to use MultiEdit tool on any file  
- About to use Write tool on existing file (overwrite)
- Planning to modify any tracked file

## Required Action
```
1. Identify the target file name
2. Search for file-specific conventions:
   mcp__serena__search_for_pattern --substring_pattern "[filename] conventions" --relative_path "templates/conventions/"
3. Read and understand the specific rules for that file
4. Verify your edit complies with all conventions
5. Only then proceed with the edit
```

## Blocking Gate
**CANNOT PROCEED** with file edit until:
- File conventions have been checked
- Specific rules for that file are understood
- Edit plan complies with all conventions
- Special requirements (if any) are addressed

## Satisfaction Criteria
✓ Conventions searched for target file
✓ File-specific rules identified (or confirmed none exist)
✓ Edit complies with all found conventions
✓ Any special requirements addressed

## Example Workflow
```
TRIGGER: User requests "update sessions/ with progress"
ACTION: 
1. Search: mcp__serena__search_for_pattern --substring_pattern "sessions/ conventions" --relative_path "templates/conventions/"
2. Find: sessions/ has specific timestamp format, progress log structure
3. Verify: Edit will follow the format
4. Proceed: Edit with correct conventions
```

## Common Files with Conventions
- **sessions/** - Timestamp format, progress structure, section order
- **CHANGELOG.md** - Conventional changelog format
- **package.json** - Version bumping rules
- **README.md** - Section order, badge format
- **.gitignore** - Comment format, section grouping
- **Work tracking files** - ALL CAPS naming, specific formats

## Cross-References
- [CONVENTIONS.md](../../templates/conventions/) - File-specific rules
- [before-create.md](before-create.md) - New file creation
- [timestamps/before-adding.md](../timestamps/before-adding.md) - For timestamp accuracy

## Error Cases
- **No conventions found**: Safe to proceed with general best practices
- **Conflicting conventions**: Use most specific rule
- **Convention unclear**: Ask user for clarification

## Why This Gate Exists
- Maintains consistency across the codebase
- Prevents convention violations
- Ensures special file requirements are met
- Reduces need for correction commits

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/file-operations/before-edit.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
