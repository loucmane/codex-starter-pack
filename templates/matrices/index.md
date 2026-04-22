---
id: matrices-index
title: Decision Matrices Index
type: decision-matrix
category: navigation
status: stable
usage: Entry point for all decision matrices
version: 1.0.0
---

# Decision Matrices

This document contains comprehensive decision matrices for quick, accurate routing of requests and actions. Each matrix provides a scannable reference for decision-making.

## 🎯 Quick Navigation

- **[Request → Handler](routing/request-to-handler.md)** - What handler for which request
- **[Context → Mode](routing/context-to-mode.md)** - When to activate which mode
- **[Tool Selection](selection/tool-selection.md)** - Which tool for which task
- **[File → Convention](selection/file-to-convention.md)** - Which rules for which files
- **[Error → Recovery](recovery/error-to-recovery.md)** - What to do when things fail
- **[Trigger → Action](mapping/trigger-to-action.md)** - Behavioral trigger mappings
- **[Keyword → Handler](mapping/keyword-to-handler.md)** - Keyword-based handler lookup

## ULTRATHINK Integration

This file participates in the ULTRATHINK system:

### VOID Resolution
- **S = VOID** → See [resolve-session-void](../templates/conventions/#resolve-session-void)
- **W = VOID** → See [resolve-work-void](../templates/workflows/#resolve-work-void)
- **H = VOID** → See [resolve-handler-void](../templates/registry/index.md#resolve-handler-void)

### Matrix Usage
These matrices provide quick lookups for handler selection. When H = VOID, use the Request → Handler Matrix to find the appropriate handler based on the user's request pattern.

## Matrix Usage Patterns

### Quick Decision Flow
1. Identify request type → Find handler
2. Check file type → Apply conventions
3. Hit problem → Use solution matrix
4. Detect context → Activate mode
5. Encounter error → Follow recovery

### When to Check Matrices
- Before starting any work
- When unsure about approach
- When something fails
- When switching contexts
- When helping others

### Matrix Maintenance
- Update when finding gaps
- Add new patterns discovered
- Remove obsolete entries
- Keep examples current
- Test matrix accuracy

## Integration Points

### With CLAUDE.md
- Matrices inform behavioral hooks
- Support "cannot proceed" gates
- Enable quick decisions
- Reduce lookup time

### With templates/registry
- Registry points to handlers
- Matrices show when to use
- Complementary systems
- Different purposes

### With Templates
- Templates have full details
- Matrices have quick lookup
- Use together effectively
- Matrices first, then templates

## Common Matrix Queries

### "What should I use for..."
1. Check Request Type matrix
2. Find matching pattern
3. Load indicated handler
4. Execute completely

### "What rules apply to..."
1. Check File Type matrix
2. Note special rules
3. Find convention handler
4. Apply all rules

### "How do I fix..."
1. Check Problem Type matrix
2. Try primary solution
3. Use fallback if needed
4. Prevent future occurrence

### "What mode for..."
1. Check Context matrix
2. Identify signals
3. Activate correct mode
4. Behave accordingly

### "What if error..."
1. Check Error matrix
2. Take immediate action
3. Follow recovery path
4. Implement prevention

Remember: Matrices are for quick decisions. For detailed procedures, always load the full handler from the indicated template file.

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/index.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
