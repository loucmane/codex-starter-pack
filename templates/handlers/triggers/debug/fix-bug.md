---
id: fix-bug
name: Fix Code Bug
role: trigger  
domain: debug
stability: stable
triggers: ['fix bug', 'bug in', 'fix the bug', 'bugfix', 'fix issue']
dependencies: ['gather-evidence', 'check-conventions-first']
tools: [mcp__serena__search_for_pattern, Read, Edit, Bash, mcp__serena__find_symbol]
version: 1.0.0
---

# Fix Code Bug Handler

## Purpose
Systematically identify, analyze, and resolve bugs in code through evidence-based debugging and minimal targeted fixes.

## Target Pattern
Extract bug description and context from user request to understand the specific issue.

## Pre-conditions
- Bug is described or identifiable
- Code is accessible for analysis
- Development environment is available

## Process

1. **Gather Evidence**
   - Search for error patterns using `mcp__serena__search_for_pattern`
   - Read relevant code sections with `Read`
   - Check recent changes with git history
   - Review error logs if available
   
2. **Analyze Root Cause**
   - Trace execution flow through the code
   - Identify failing conditions and edge cases
   - Check assumptions and dependencies
   - Verify expected vs actual behavior
   
3. **Implement Fix**
   - Make minimal necessary changes using `Edit`
   - Follow existing code patterns and conventions
   - Add error handling if needed
   - Preserve code structure and style
   
4. **Validate Solution**
   - Run tests using `Bash` if available
   - Check for regressions in related functionality
   - Verify fix addresses root cause, not just symptoms
   - Document solution if complex or non-obvious

## Success Criteria
- Bug fixed with evidence of resolution
- Tests passing (if applicable)
- No regressions introduced
- Root cause addressed, not just symptoms

## Failure Modes
- **Insufficient evidence**: Gather more debugging data
- **Complex interdependencies**: Break down into smaller fixes
- **Test failures**: Revert and try alternative approach
- **Unclear root cause**: Add logging and reproduce issue

## Examples

### Example 1: JavaScript Error
**Input**: "fix bug in user authentication"
**Process**:
1. Search for auth-related errors: `mcp__serena__search_for_pattern`
2. Read authentication code: `Read`
3. Identify issue (e.g., missing null check)
4. Fix with minimal change: `Edit`
5. Test authentication flow

### Example 2: Logic Error
**Input**: "bug in calculation function"
**Process**:
1. Read calculation function
2. Trace through logic with test cases
3. Identify incorrect formula or condition
4. Fix logic error
5. Verify with edge cases

### Example 3: Rendering Issue
**Input**: "fix the bug where page doesn't load"
**Process**:
1. Search for loading/rendering patterns
2. Check console for errors
3. Identify missing dependency or race condition
4. Fix timing or dependency issue
5. Test page loading

## Integration Points

### With gather-evidence
- Uses evidence gathering before making assumptions
- Requires proof of bug location and cause

### With check-conventions-first  
- Follows coding conventions in fix implementation
- Maintains code quality standards

### Related Handlers
- `debug-issue` - For more complex debugging workflows
- `run-tests` - For validation after fixes
- `analyze-code` - For understanding complex codebases

## Best Practices
- Always reproduce the bug first
- Gather evidence before theorizing
- Make minimal, targeted changes
- Test thoroughly before considering complete
- Document complex fixes for future reference
- Consider edge cases and error handling

## Output
- Bug fixed with evidence of resolution
- Tests passing
- No regressions introduced