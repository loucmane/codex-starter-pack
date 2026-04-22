---
id: swhe-format
title: Development Mode Execution S:W:H:E Format
type: engine-component
status: stable
---

# Development Mode Execution - S:W:H:E Format

## Overview
When development mode is triggered, execution follows the S:W:H:E format for structured processing.

## S:W:H:E Format Specification

### Format Template
```
Let me ultrathink about this... [S:20250127|W:work-tracking|H:update-tracker|E:5/"Progress recorded"]
```

### Field Definitions

#### S - Session ID
- Primary: Session ID via session-resolver (`templates/engine/core/session-resolver.md`)
- Sources: sessions/current, sessions/YYYY/MM/
- Fallback: VOID→session-start (triggers proper creation)
- Formats supported:
  - `current` - Active session from sessions/current symlink
  - `YYYY-MM-DD-NNN` - Specific session ID
  - `YYYYMMDD` - Date format (finds latest for that date)
  - `VOID` - Needs resolution

#### W - Work Context  
- Primary: Active work folder or activity
- Fallback: VOID→workflows (triggers workflow lookup)
- Examples: "work-tracking", "investigating", "reviewing", "planning"
- Changes dynamically with task focus

#### H - Handler Name
- Primary: Specific handler ID from REGISTRY.md
- During search: H:searching
- Not found: H:VOID→registry (triggers registry search)
- Must be validated before use

#### E - Evidence
- Format: steps/"success criteria"
- Examples:
  - E:5/"Progress recorded" - 5 steps with success message
  - E:pending - During handler search only
  - E:steps/None - No success criteria defined
  - E:steps/"varies" - Conditional success
  - E:steps/redirect - For routing handlers
  - E:steps/"interactive" - User input required

## Session Resolution Protocol

### Automatic Session Detection
The S field now auto-detects format and resolves to the correct session:
1. **Import resolver**: Uses session-resolver for all S field processing
2. **Format detection**: Automatically identifies format type
3. **Priority search**: Checks sessions/ only (no sessions/ fallback)
4. **Structured return**: Provides full session metadata

## Handler Validation Protocol

### Never Use Unvalidated Handlers
1. **Unsure**: Use H:searching|E:pending
2. **Not found**: Use H:VOID→registry|E:searching  
3. **Always show**: "Found: [handler] ([template]#[anchor])"
4. **Execute**: Use real handler in new ULTRATHINK

### Validation Steps
```
1. Use Serena to search templates/registry/ for handler
2. Verify handler exists at specified path
3. Load handler and confirm structure
4. Display found confirmation
5. Execute with validated handler
```

## Evidence-Based Execution

### Required Evidence Types
After ULTRATHINK, execute with inline evidence:
- **File paths** for all changes
- **Line numbers** for edits
- **Operation summaries** for commands
- **Error messages** if encountered

### Completion Status Indicators
- ✓ **Completed**: [handler] ([X] steps)
- ⚠️ **Interrupted**: [handler] ([Y] of [X] steps)
- ❌ **Failed**: [handler] (error at step [Y])

## Special E Field Values

### During Search Phase
- **E:pending** - Handler search in progress
- **E:searching** - Registry lookup active

### Success Criteria Variations
- **E:steps/None** - No specific success criteria
- **E:steps/"varies"** - Success depends on conditions
- **E:steps/redirect** - Handler routes to another
- **E:steps/"interactive"** - Requires user input

## Integration with ULTRATHINK
This format is the implementation layer of the ULTRATHINK protocol:
1. ULTRATHINK provides thinking framework
2. S:W:H:E provides execution structure
3. Evidence validates completion
4. Status indicates outcome

## Examples

### Standard Execution
```
Let me ultrathink about this... [S:20250127|W:bug-fix-ACTIVE|H:fix-bug|E:7/"Bug resolved"]
```

### Handler Search Phase
```
Let me ultrathink about this... [S:20250127|W:investigating|H:searching|E:pending]
```

### VOID State Resolution
```
Let me ultrathink about this... [S:VOID→conventions|W:VOID→workflows|H:VOID→registry|E:searching]
```

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/execution/swhe-format.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
