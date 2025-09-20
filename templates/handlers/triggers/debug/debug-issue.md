---
id: debug-issue
name: Debug Issue
role: trigger
domain: debug
stability: stable
triggers:
  - "debug this"
  - "debug issue"
  - "why is X failing"
  - "debug error"
  - "help debug"
  - "debug X"
  - "find the problem"
  - "what's wrong with X"
dependencies: []
tools:
  - mcp__serena__search_for_pattern
  - Read
  - Grep
  - Bash
version: 1.0.0
---

# Debug Issue Handler

## Purpose
Systematically debug issues by collecting error details, analyzing code flow, and identifying root causes through evidence-based investigation.

## Target Pattern
User reports a problem or error that needs debugging investigation.

## Pre-conditions
- Issue or error has been identified
- Problem is not immediately obvious
- Code or system behavior is not matching expectations

## Process

1. **Collect error details**
   - Ask for specific error messages if not provided
   - Get steps to reproduce the issue
   - Identify when the problem started occurring
   - Note what was expected vs actual behavior

2. **Search for error patterns**
   - Use `mcp__serena__search_for_pattern` to find error messages in code
   - Search for similar patterns in logs or output files
   - Look for recent changes that might be related
   - Check for known issues or patterns with `Grep`

3. **Analyze code flow**
   - Use `Read` to examine relevant files identified in step 2
   - Trace execution path where error occurs
   - Check function calls, variable assignments, and control flow
   - Look for edge cases or boundary conditions

4. **Identify root cause**
   - Compare actual code behavior with expected behavior
   - Check for common issues: null/undefined values, type mismatches, async issues
   - Use `Bash` to run diagnostic commands if needed
   - Verify assumptions about the code's state at error point

## Success Criteria
- Root cause clearly identified and explained
- Evidence gathered to support the diagnosis
- Concrete steps provided to fix the issue
- Understanding of why the error occurred

## Failure Modes
- **Insufficient error information**: Request more specific details
- **Complex multi-layered issue**: Break down into smaller problems
- **Environment-specific problem**: Gather system/environment details
- **Intermittent issue**: Focus on conditions when it occurs vs doesn't

## Examples

### Example 1: JavaScript Error
**Input**: "debug this TypeError: Cannot read property 'name' of undefined"
**Process**:
1. Search for property access patterns with 'name'
2. Find where objects might be undefined
3. Check initialization and data flow
4. Identify missing null checks

### Example 2: Build Failure
**Input**: "help debug - build is failing"
**Process**:
1. Check build logs for specific error messages
2. Search for import/dependency issues
3. Verify file paths and module resolution
4. Test incremental builds to isolate problem

### Example 3: Runtime Behavior
**Input**: "why is X failing - function returns wrong results"
**Process**:
1. Read function implementation
2. Check input validation and processing
3. Trace data transformations step by step
4. Compare expected vs actual logic flow

## Integration Points

### With Error Analysis
- Connects to log analysis when error messages are available
- Routes to performance debugging for slow operations
- Links to dependency checking for import/module issues

### With Code Review
- May identify code quality issues during debugging
- Can surface refactoring opportunities
- Helps validate fix implementations

### With Testing
- Debug process often reveals missing test cases
- Can validate fixes through test execution
- Helps identify edge cases for future testing

## Best Practices
- Always gather complete error information before starting analysis
- Use evidence-based reasoning - don't guess without data
- Check recent changes first as likely culprits
- Test hypotheses systematically
- Document findings for future reference
- Verify fixes don't introduce new issues