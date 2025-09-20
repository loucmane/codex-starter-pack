# Error Handling & Fallbacks

## Overview
Comprehensive error handling and fallback strategies for template system failures and edge cases.

## Handler Discovery Failures

### When No Handler Found
```
If REGISTRY search returns nothing:
1. Try broader search terms in REGISTRY
2. Search templates/patterns/ for meta-routing
3. Check ambiguous-request pattern
4. Ask user for clarification
```

#### Progressive Search Strategy
1. **Exact match** → "implement-feature"
2. **Partial match** → "implement"
3. **Category match** → "development"
4. **Meta-pattern** → Check templates/patterns/
5. **User clarification** → "What specifically would you like me to do?"

### When Handler Has Gaps
```
If handler missing steps or unclear:
1. Search for similar handlers
2. Check conventions for related rules
3. Use general principles from KEY OPERATING PRINCIPLES
4. Document the gap for future improvement
```

#### Gap Mitigation
- **Similar handler**: Use as template
- **Conventions**: Apply relevant rules
- **Principles**: Follow core operating guidelines
- **Documentation**: Record gap in work tracking

## Fallback Decision Tree

### Primary Decision Flow
```
No handler match?
├─ Is it development work? → Use start-new-work as default
├─ Is it a search? → Check tool selection matrix in templates/matrices/
├─ Is it file operation? → Check special files rules
├─ Is it unclear? → Ask: "What specifically would you like me to do?"
└─ Still stuck? → Check Error → Recovery Matrix in templates/matrices/
```

### Default Handlers by Category
- **Development**: start-new-work
- **Search**: search-code or find-files
- **Debugging**: investigate-problem
- **Documentation**: update-docs
- **Git**: commit-changes

## Creating Missing Handlers

### When to Create New Handlers
```
When encountering repeated gaps:
1. Document pattern in work tracking
2. Suggest handler addition to templates
3. Follow existing handler format
4. Update REGISTRY when added
```

### Handler Creation Protocol
1. **Identify Gap**: Document missing functionality
2. **Find Pattern**: Look for repeated requests
3. **Draft Handler**: Use standard format
4. **Test Handler**: Verify with real use case
5. **Register**: Add to REGISTRY.md

## Error Categories

### Search Errors
- **Empty results**: Broaden search terms
- **Too many results**: Narrow with filters
- **Wrong domain**: Check correct template file
- **Timeout**: Retry with smaller scope

### Loading Errors
- **File not found**: Verify path structure
- **Permission denied**: Check file access
- **Corrupted content**: Use backup or recreate
- **Network issues**: Retry with delay

### Execution Errors
- **Missing tool**: Check tool availability
- **Invalid parameters**: Verify parameter format
- **Dependency failure**: Check prerequisites
- **State conflicts**: Reset and retry

## Recovery Strategies

### Immediate Recovery
1. **Retry**: Simple retry for transient failures
2. **Fallback**: Use alternative approach
3. **Degrade**: Provide partial functionality
4. **Abort**: Stop with clear error message

### Progressive Recovery
```
Level 1: Retry same operation
Level 2: Try alternative method
Level 3: Use simplified approach
Level 4: Ask for user guidance
Level 5: Document failure and stop
```

## Error Reporting

### User-Facing Messages
```
❌ Error: [Brief description]
   Attempted: [What was tried]
   Issue: [What went wrong]
   Next steps: [What user can do]
```

### Internal Logging
```
ERROR: [Timestamp] [Component] [Operation]
  Details: [Full error information]
  Context: [S:W:H:E values]
  Stack: [If applicable]
  Recovery: [What was attempted]
```

## Common Issues & Solutions

### Quick Reference
- **"Can't find handler"** → Search variations, check templates/patterns/
- **"Handler incomplete"** → Use similar handler as template
- **"Wrong tool used"** → Always check tool matrix first
- **"Convention violated"** → Stop and check templates/conventions/
- **"Not sure what to do"** → Ask user for specific guidance

### Pattern-Based Solutions
| Problem | Solution | Fallback |
|---------|----------|----------|
| No handler match | Search REGISTRY | Use default handler |
| Tool unavailable | Check alternatives | Manual approach |
| File locked | Wait and retry | Work on copy |
| Invalid format | Check conventions | Ask for example |
| Ambiguous request | Clarify intent | Show options |

## Prevention Strategies

### Proactive Checks
- Validate handler exists before use
- Verify tool availability upfront
- Check file permissions early
- Confirm conventions before edits

### Defensive Practices
- Always have fallback plan
- Document assumptions
- Test edge cases
- Keep recovery simple

## Integration Points
- **templates/patterns/**: Meta-routing for complex cases
- **templates/matrices/**: Decision matrices for common patterns
- **templates/conventions/**: Rules to prevent errors
- **Work tracking**: Document recurring issues