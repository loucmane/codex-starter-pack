---
id: ultrathink-format
type: shared-pattern
category: core
version: 1.0.0
description: Universal ULTRATHINK format and enforcement mechanisms for development mode
stability: stable
last-updated: 2025-01-30
dependencies: []
---

# ULTRATHINK Format Pattern

## Core Format Definition

### S:W:H:E Format
```
Let me ultrathink about this... [S:X|W:Y|H:Z|E:steps/"criteria"]
```

### Field Definitions
- **S**: Session ID via session-resolver (sessions/ only)
  - Auto-detects format: `current`, `YYYY-MM-DD-NNN`, `YYYYMMDD`, or `VOID`
  - Resolves from `sessions/current` symlink and `sessions/YYYY/MM/`
  - See: `templates/engine/core/session-resolver.md`
- **W**: Work context from active/ (or VOID→workflows for optimal work)
  - Can be: folder name, "investigating", "reviewing", "planning", "implementation", "debugging", "refactoring"
  - Changes with task focus
  - Always required in work folders (/work-tracking/active/*)
- **H**: Handler matching request (or VOID→registry for best practice)
  - Must be actual handler name from templates/registry
  - Use "searching" during initial search phase
  - Use VOID→registry when no handler found
- **E**: Evidence proving handler comprehension
  - Format: steps/"success criteria" OR steps/key:"most critical step"
  - Shows handler was actually read and understood
  - Special values detailed below

## Pre-ULTRATHINK Protocol

**CRITICAL**: Prevents false compliance by enforcing actual handler comprehension

### Required Sequence
1. **First output**: "Searching for appropriate handler for [request type]..."
2. **Show search**: Display actual search command + 1-2 results
3. **Handler comprehension**: "Reading handler: [name]" then "Key steps: [list 2-3 critical steps from Process]"
4. **Initial ULTRATHINK**: `Let me ultrathink about this... [S:X|W:Y|H:searching|E:pending]`
5. **Final ULTRATHINK**: `Let me ultrathink about this... [S:X|W:Y|H:found-handler|E:n/key:"most critical step"]`

### Why This Protocol Exists
- Comprehension check forces actual handler reading
- Can't list steps without reading them
- Wrong step count, missing key steps, or generic descriptions = didn't read handler
- Creates verifiable evidence of handler understanding

## Handler Search Protocol

When H is unknown, MUST follow this sequence:

1. **State search intent**: "Searching for handler..."
2. **Show search command and results**
3. **Use H:searching|E:pending** if unsure
4. **Demonstrate comprehension** before proceeding

### Handler Validation Required
Never use a handler name without finding it first:
- Unsure: Use `H:searching|E:pending`
- Not found: Use `H:VOID→registry|E:searching`
- Always show: "Found: [handler] ([template]#[anchor])"
- Execute with real handler in new ULTRATHINK

## Evidence Field Values

### Standard Values
- `E:pending` - During handler search only
- `E:steps/None` - No success criteria defined
- `E:steps/"varies"` - Conditional success based on context
- `E:steps/redirect` - Routing handlers that redirect to others
- `E:steps/"interactive"` - User input required for completion
- `E:n/"criteria"` - n steps with specific success criteria
- `E:n/key:"step"` - n steps with most critical step identified

### Evidence-Based Execution
After ULTRATHINK, execute with inline evidence:
- File paths for all changes
- Line numbers for edits
- Operation summaries for commands
- Error messages if encountered

## Enforcement Mechanisms

### Before ANY Development Request
```
TRIGGER: Any development signal detected
ACTION: Output ULTRATHINK format
BLOCKS: Cannot proceed without valid [S:W:H:E]
PROCESS:
1. First line MUST be: "Let me ultrathink about this... [S:X|W:Y|H:Z|E:steps/"criteria"]"
2. Determine each value:
   - S: Auto-resolved from sessions/ or sessions/ via session-resolver
   - W: Analyze request and active folders
   - H: Find matching handler
   - E: Count handler steps and find success criteria
3. If any value is VOID:
   - MUST resolve using appropriate handler
   - Cannot continue until resolved
4. Only after all valid → Continue to action
ERROR: Development request without ULTRATHINK
```

### Common ULTRATHINK Violations
1. **Missing ULTRATHINK** → Stop immediately and add
2. **Old session ID** → S = VOID → resolve-session-void
3. **No work context** → W = VOID → resolve-work-void  
4. **Vague handler** → H = VOID → resolve-handler-void
5. **Skipping to action** → Return to ULTRATHINK first

### Why This Gate Exists
- Forces context awareness before action
- Prevents stale session references
- Ensures proper work organization
- Makes handler selection explicit
- Creates audit trail via [S:W:H:E]
- VOID states auto-resolve via template handlers

## Completion Status Indicators

After handler execution, report status:

- `✓ Completed: [handler] ([X] steps)` - Full success
- `⚠️ Interrupted: [handler] ([Y] of [X] steps)` - Partial completion
- `❌ Failed: [handler] (error at step [Y])` - Execution failure

## Usage Examples

### Development Request
```
Let me ultrathink about this... [S:20250130|W:implementation|H:searching|E:pending]
[Search for handler...]
Let me ultrathink about this... [S:20250130|W:implementation|H:implement-feature|E:7/"Tests passing"]
```

### Investigation Request
```
Let me ultrathink about this... [S:20250130|W:investigating|H:searching|E:pending]
[Search and comprehension...]
Let me ultrathink about this... [S:20250130|W:investigating|H:debug-issue|E:5/key:"Identify root cause"]
```

### VOID Resolution
```
Let me ultrathink about this... [S:VOID|W:VOID|H:VOID|E:pending]
[Resolve each VOID state...]
Let me ultrathink about this... [S:20250130|W:active-work|H:found-handler|E:4/"Success"]
```

## Integration Points

- Triggers [execute-ultrathink] handler in templates/patterns/
- Integrates with hook system (pre_tool_use.py)
- Tracked in logs/state.json
- Enforced by BEHAVIORS.md behavioral gates
- Referenced by all agent specifications

## Reference Implementation

This pattern is the authoritative source for ULTRATHINK format.
Other files should reference this pattern rather than duplicating it:

```markdown
<!-- In other files -->
See: templates/shared/patterns/ultrathink-format.md
```

## Version History

- 1.0.0 (2025-01-30): Initial extraction and consolidation from 17+ files