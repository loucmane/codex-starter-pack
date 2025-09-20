---
id: handler-design
type: integration-guide
category: best-practices
title: Handler Design Best Practices
audience: developer
complexity: intermediate
dependencies:
  - creating-handlers
  - handler-chaining
prerequisites:
  - Understanding of handler system
  - Experience creating handlers
  - Knowledge of common patterns
version: 1.0.0
status: stable
---

# Handler Design Best Practices

## Overview

This guide provides best practices for designing effective, maintainable, and performant handlers in the Claude Template System.

## Prerequisites

- Understanding of handler roles and responsibilities
- Experience creating and using handlers
- Knowledge of common design patterns
- Familiarity with error handling

## Core Design Principles

### 1. Single Responsibility Principle

```markdown
## Good: Focused Handler
```yaml
handler: validate-email
purpose: Validate email format only
process:
  - Check email format
  - Return valid/invalid
```

## Bad: Multi-Purpose Handler
```yaml
handler: process-user
purpose: Everything user-related  # Too broad!
process:
  - Validate email
  - Hash password
  - Save to database
  - Send welcome email
  - Log activity
```

**Why it matters**:
- Easier to test
- Simpler to understand
- More reusable
- Easier to maintain
```

### 2. Clear Naming Conventions

```markdown
## Naming Patterns

### Action-Object Format
✅ Good:
- `implement-feature`
- `validate-input`
- `deploy-application`
- `analyze-code`

❌ Bad:
- `handler1`
- `process`
- `do-stuff`
- `main`

### Role-Specific Prefixes
- Triggers: `handle-`, `process-`, `respond-to-`
- Orchestrators: `coordinate-`, `manage-`, `orchestrate-`
- Operators: `execute-`, `perform-`, `run-`
```

### 3. Explicit Dependencies

```yaml
# Good: Clear dependencies
handler: deploy-application
dependencies:
  - build-application
  - run-tests
  - check-environment
tools:
  - Write
  - MultiEdit
  - Grep

# Bad: Hidden dependencies
handler: deploy-application
# Dependencies not documented
# Tools assumed to exist
```

## Handler Structure Best Practices

### Input Validation

```markdown
## Always Validate Inputs

```yaml
handler: create-component
process:
  # FIRST: Validate
  1. Validate component name format
  2. Check name uniqueness
  3. Verify template exists
  # THEN: Execute
  4. Create component files
  5. Update index
```

**Validation Checklist**:
- ☑️ Required fields present
- ☑️ Data types correct
- ☑️ Values within valid ranges
- ☑️ Format constraints met
- ☑️ Business rules satisfied
```

### Error Handling

```markdown
## Comprehensive Error Handling

```yaml
handler: fetch-data
error_handling:
  - type: network_error
    action: retry_with_backoff
    max_attempts: 3
  
  - type: timeout
    action: use_cache
    fallback: return_default
  
  - type: invalid_response
    action: log_and_fail
    message: "Invalid data format received"
  
  - type: unknown
    action: log_and_escalate
    preserve_context: true
```

**Error Response Format**:
```yaml
error:
  code: ERROR_CODE
  message: User-friendly message
  details: Technical details
  recovery: Suggested action
  context: Relevant state
```
```

### Process Documentation

```markdown
## Clear Process Steps

```yaml
handler: migrate-database
process:
  # Setup Phase
  1. Backup current database
  2. Validate migration scripts
  3. Check disk space
  
  # Execution Phase
  4. Apply migrations in order
  5. Verify each migration
  6. Update migration log
  
  # Validation Phase
  7. Run integrity checks
  8. Verify data consistency
  9. Test critical queries
  
  # Cleanup Phase
  10. Remove temporary files
  11. Update documentation
  12. Notify completion
```

Each step should be:
- Atomic (complete unit of work)
- Verifiable (can check success)
- Reversible (when possible)
```

## Performance Considerations

### Optimize for Common Case

```yaml
handler: search-codebase
optimizations:
  - Check cache first (90% hit rate)
  - Use indexed search for common patterns
  - Full scan only when necessary
  - Stream large results
```

### Resource Management

```markdown
## Efficient Resource Use

```yaml
handler: process-files
resource_management:
  - batch_size: 100  # Process in batches
  - max_memory: 512MB  # Limit memory use
  - timeout: 30s  # Prevent hanging
  - cleanup: always  # Clean up resources
```

**Resource Checklist**:
- ☑️ Close files after use
- ☑️ Release locks
- ☑️ Clear large variables
- ☑️ Cancel timers
- ☑️ Disconnect connections
```

### Caching Strategy

```yaml
handler: expensive-analysis
caching:
  key: "${file_path}_${hash}_${version}"
  ttl: 3600  # 1 hour
  invalidate_on:
    - file_change
    - config_change
  storage: memory  # or disk
  max_size: 100MB
```

## Testability

### Design for Testing

```markdown
## Testable Handler Design

```yaml
handler: data-processor
testability:
  - Pure functions where possible
  - Injected dependencies
  - Mockable external calls
  - Deterministic behavior
  - Observable side effects
```

**Test Scenarios**:
1. Happy path
2. Edge cases
3. Error conditions
4. Resource limits
5. Concurrent execution
```

### Test Coverage Requirements

```yaml
test_coverage:
  unit_tests:
    - Input validation
    - Core logic
    - Error handling
    - Edge cases
  
  integration_tests:
    - Handler chains
    - Tool interactions
    - State management
  
  e2e_tests:
    - Complete workflows
    - Real-world scenarios
    - Performance benchmarks
```

## Maintainability

### Version Management

```yaml
handler: api-client
version: 2.0.0
changelog:
  2.0.0:
    - Breaking: Changed input format
    - Added: Retry logic
    - Fixed: Memory leak
  1.1.0:
    - Added: Cache support
    - Improved: Error messages
backward_compatible: false
migration_guide: See MIGRATION.md
```

### Documentation Standards

```markdown
## Handler Documentation

Every handler MUST include:

1. **Purpose**: Clear, single sentence
2. **Triggers**: Exact activation phrases
3. **Inputs**: Required and optional parameters
4. **Outputs**: Return value structure
5. **Side Effects**: Files created, state changed
6. **Examples**: Real-world usage
7. **Error Cases**: Possible failures
8. **Performance**: Time/space complexity
```

### Deprecation Strategy

```yaml
handler: old-processor
deprecated: true
deprecation_date: 2024-01-01
replacement: new-processor
migration_path:
  - Update input format
  - Change handler reference
  - Test thoroughly
removal_date: 2024-06-01
```

## Security Considerations

### Input Sanitization

```markdown
## Sanitize All Inputs

```yaml
handler: execute-command
security:
  input_validation:
    - Escape special characters
    - Validate against whitelist
    - Check path traversal
    - Limit input size
    - Timeout long operations
```

**Never Trust User Input**:
- Validate format
- Check boundaries
- Sanitize content
- Escape for context
```

### Permission Checks

```yaml
handler: modify-system-file
permissions:
  required: admin
  check_before: execution
  audit: true
  fail_message: "Insufficient permissions"
```

## Common Anti-Patterns

### Anti-Pattern: God Handler

```markdown
## Problem: Handler Does Everything

❌ **Bad**:
```yaml
handler: do-everything
process:
  - 50+ steps
  - Multiple responsibilities
  - Complex branching
  - Unclear purpose
```

✅ **Good**:
Break into multiple focused handlers:
- `prepare-environment`
- `execute-task`
- `validate-results`
- `cleanup-resources`
```

### Anti-Pattern: Hidden State

```markdown
## Problem: Implicit State Dependencies

❌ **Bad**:
```yaml
handler: process-data
# Assumes previous handler set global state
# Fails mysteriously if state missing
```

✅ **Good**:
```yaml
handler: process-data
input:
  required_state: ${previous.output}
  validates: state_schema
```
```

### Anti-Pattern: Swallowed Errors

```markdown
## Problem: Hiding Failures

❌ **Bad**:
```yaml
handler: risky-operation
process:
  - Try operation
  - If fails, continue silently  # Bad!
```

✅ **Good**:
```yaml
handler: risky-operation
process:
  - Try operation
  - If fails, log error
  - Return error status
  - Let caller decide
```
```

## Handler Composition Guidelines

### Composable Design

```yaml
# Good: Composable handlers
handlers:
  - read-config:  # Atomic
      output: config_data
  
  - validate-config:  # Atomic
      input: config_data
      output: validation_result
  
  - apply-config:  # Atomic
      input: config_data
      requires: validation_result.valid

# Can be composed into:
workflow: configure-system
chain: [read-config, validate-config, apply-config]
```

### Interface Contracts

```yaml
contract: data-processor
input_schema:
  type: object
  required: [data, format]
  properties:
    data: array
    format: enum[json, xml, csv]

output_schema:
  type: object
  required: [processed_data, metadata]
  properties:
    processed_data: array
    metadata:
      count: integer
      errors: array
```

## Examples of Well-Designed Handlers

### Example: Feature Implementation Handler

```yaml
---
id: implement-user-feature
name: Implement User Feature
role: trigger
domain: development
stability: stable
version: 1.0.0
---

#### Handler: implement-user-feature
**Purpose**: Implement a complete user feature with tests
**Triggers**: "implement feature", "build feature", "create feature"
**Inputs**:
  - feature_spec: Feature requirements
  - priority: high|medium|low
**Process**:
  1. Validate feature specification
  2. Break down into tasks
  3. Create implementation plan
  4. Generate tests first (TDD)
  5. Implement incrementally
  6. Validate each component
  7. Integration testing
  8. Documentation update
**Success**: Feature implemented, tested, documented
**Failure**: Clear error with rollback instructions
**Performance**: O(n) where n = feature complexity
**Side Effects**: 
  - Creates new files
  - Updates existing modules
  - Modifies test suites
```

## Checklist for Handler Design

### Pre-Implementation
- [ ] Clear single purpose defined
- [ ] No existing handler does this
- [ ] Dependencies identified
- [ ] Error cases considered
- [ ] Performance impact assessed

### Implementation
- [ ] Input validation implemented
- [ ] Error handling complete
- [ ] Resource cleanup guaranteed
- [ ] Logging added
- [ ] Tests written

### Post-Implementation
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Integration tested
- [ ] Performance validated
- [ ] Security reviewed

## Related Resources

- [Creating Handlers](../guides/creating-handlers.md)
- [Handler Chaining](../composition/handler-chaining.md)
- [Template Design](template-design.md)
- [Integration Patterns](integration-patterns.md)
- [Handler Architecture](../architecture/handler-architecture.md)