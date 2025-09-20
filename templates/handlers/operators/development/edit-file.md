---
id: edit-file
name: Edit File
role: operator
domain: development
stability: stable
triggers:
  - "change X to Y"
  - "update Z"
  - "modify file"
  - "edit"
  - "replace"
  - "update file"
dependencies: []
tools:
  - Read
  - Edit
  - MultiEdit
  - Write
  - mcp__serena__find_symbol
  - mcp__serena__get_symbols_overview
version: 1.0.0
---

# edit-file

## Purpose
Modify existing files with specific changes while maintaining code integrity and conventions.

## Triggers
- "change X to Y"
- "update Z" 
- "modify file"
- Direct file path with change request

## Target Pattern
File and changes specified

## Pre-conditions
- File exists and readable
- Clear change description
- Valid file path

## Process

1. **Read file first (mandatory)**
   - Always use Read tool to understand current state
   - Never edit without reading first

2. **ALWAYS use Edit/Write for modifications**:
   - Creating files → `Write`
   - Editing files → `Edit` or `MultiEdit`
   - NEVER use Serena for file modifications

3. **Use Serena ONLY for understanding before edit**:
   - Find symbol location → `mcp__serena__find_symbol`
   - Understand structure → `mcp__serena__get_symbols_overview`
   - Then use Edit/Write for actual changes
   - Multiple changes → `MultiEdit`

4. **Verify changes**
   - Re-read file after edit
   - Confirm changes applied correctly
   - Check for unintended modifications

## Success Criteria
- Changes applied correctly
- File remains syntactically valid
- No unintended modifications
- Conventions maintained

## Failure Modes
- Can't locate text to replace
- File conflicts or locks
- Invalid syntax after edit
- Pattern too ambiguous

## Examples
- "change function body" → Find with Serena, edit with Edit
- "update config value" → Direct Edit tool
- "modify all imports" → MultiEdit for batch changes
- "replace class name everywhere" → MultiEdit with replace_all

## Best Practices
- Always read before editing
- Use exact string matching
- Preserve indentation and formatting
- Verify changes after application
- Use MultiEdit for multiple changes
- Check conventions before editing