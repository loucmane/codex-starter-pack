---
id: ultrathink-reference
type: workflow-component
category: core
title: ULTRATHINK System Reference
dependencies:
  - ../../shared/patterns/ultrathink-format.md
related:
  - ../protocols/universal-flight.md
version: 1.0.0
status: stable
---

# ULTRATHINK System Reference

**CRITICAL: The ULTRATHINK system is the foundation of all workflows.**

## Core Pattern

The complete ULTRATHINK format and enforcement mechanisms are defined in:
**[templates/shared/patterns/ultrathink-format.md](../../shared/patterns/ultrathink-format.md)**

## Quick Reference

### Format
```
Let me ultrathink about this... [S:X|W:Y|H:Z|E:steps/"criteria"]
```

### Field Meanings
- **S**: Session ID from sessions/
- **W**: Work context from active/ folders
- **H**: Handler matching the request
- **E**: Evidence of handler execution

## VOID Resolution for Workflows

When W (Work context) is VOID in workflows:

### Handler: resolve-work-void

**Triggers**: "W = VOID", "no work context", "work unclear", "VOID→workflows"
**Target Pattern**: Missing work context in ULTRATHINK

**Process**:
1. Analyze user request to determine domain:
   - Implementation/feature → Development work
   - Bug/fix/error → Problem solving
   - Search/find/explore → Investigation
   - Review/check → Review work
   - Plan/design → Planning work

2. Check active work folders:
   - List all folders in work-tracking/active/
   - Match request domain to folder names
   - If direct match → W = folder-name

3. Handle special states:
   - Search/analysis requests → W = "investigating"
   - Code/PR reviews → W = "reviewing"
   - Architecture/design → W = "planning"

4. If no match found:
   - Output: "No active work context for this request"
   - Route to appropriate handler:
     - New feature → start-new-work
     - Bug fix → start-new-work with bug context
     - General question → W = "investigating"

5. Return valid W value

**Success**: Valid work context obtained
**Failure**: Cannot determine context

**Examples**:
- "Fix login bug" with no bug folder → Routes to start-new-work
- "Find all getUserData calls" → W = "investigating"
- "Plan caching strategy" → W = "planning"
- "Continue with tests" + test folder exists → W = "test-implementation"

## Integration Points

### With Other VOID Resolvers
- **S = VOID** → See [resolve-session-void](../../conventions/#resolve-session-void)
- **W = VOID** → See above resolver
- **H = VOID** → See [resolve-handler-void](../../REGISTRY.md#resolve-handler-void)

### Handler Requirements
All workflow handlers expect valid [S:W:H] context before execution. Any handler called with VOID values must resolve them first using the appropriate resolver.

## Why This Matters for Workflows

1. **Forces context awareness** before any action
2. **Prevents stale references** to old sessions
3. **Ensures proper organization** of work
4. **Makes handler selection explicit**
5. **Creates audit trail** via [S:W:H:E]
6. **Auto-resolves** VOID states

## See Also

- **[Shared ULTRATHINK Pattern](../../shared/patterns/ultrathink-format.md)** - Complete format definition
- **[CONVENTIONS.md](../../conventions/)** - Session VOID resolver
- **[REGISTRY.md](../../REGISTRY.md)** - Handler VOID resolver
- **[Universal Flight Protocol](../protocols/universal-flight.md)** - Pre-flight integration