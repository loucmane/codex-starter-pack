---
id: code-review
name: Review Code
role: trigger
domain: analysis
stability: stable
triggers:
  - "review this code"
  - "code review"
  - "check for issues"
  - "review my code"
dependencies: []
tools:
  - Read
  - mcp__serena__search_for_pattern
  - mcp__serena__find_symbol
version: 1.0.0
---

# Review Code Handler

## Purpose
Perform comprehensive code review by analyzing code for bugs, quality issues, security concerns, and providing actionable feedback to improve code quality and maintainability.

## Target Pattern
User provides code to review either through file paths, code snippets, or requests to review recent changes.

## Pre-conditions
- Code is accessible via file paths or provided directly
- User has specified what code needs to be reviewed
- Code is in a readable format

## Process

1. **Read code thoroughly**
   - Use Read tool to access files if paths provided
   - Use mcp__serena__search_for_pattern to find related code patterns
   - Use mcp__serena__find_symbol to understand code structure and dependencies
   - Analyze code context and surrounding implementation

2. **Check for bugs/issues**
   - Identify logic errors and potential runtime issues
   - Check for null/undefined handling
   - Verify error handling and edge cases
   - Look for potential race conditions or concurrency issues
   - Validate data flow and state management

3. **Assess code quality**
   - Evaluate code structure and organization
   - Check naming conventions and readability
   - Assess function/class complexity and single responsibility
   - Review code duplication and reusability
   - Validate documentation and comments
   - Check for consistent coding patterns

4. **Provide feedback**
   - Summarize findings with priority levels (Critical, High, Medium, Low)
   - Provide specific line references where applicable
   - Offer concrete suggestions for improvements
   - Include code examples for recommended changes
   - Highlight positive aspects and good practices found

## Success Criteria
- Complete analysis of provided code
- Clear categorization of issues by severity
- Specific, actionable feedback with examples
- Balanced review highlighting both issues and strengths

## Failure Modes
- **Code not accessible**: Request correct file paths or code snippets
- **Unclear scope**: Ask user to specify which files/functions to review
- **No issues found**: Still provide feedback on code quality and potential improvements
- **Complex codebase**: Break down review into manageable sections

## Examples

### Example 1: File Review
**Input**: "review this code: src/components/UserAuth.jsx"
**Process**: 
- Read UserAuth.jsx file
- Check for security issues in authentication logic
- Assess React component structure and hooks usage
- Provide specific feedback on improvements

### Example 2: Code Snippet Review
**Input**: "code review" (with code pasted)
**Process**:
- Analyze provided code snippet
- Check for syntax issues and logic errors
- Suggest improvements for readability and performance
- Provide enhanced version if needed

### Example 3: Recent Changes Review
**Input**: "review my code changes"
**Process**:
- Use search tools to identify recently modified files
- Focus review on changed sections
- Check impact on existing functionality
- Validate integration with existing codebase

## Integration Points

### With Development Workflow
- Can be triggered during development process
- Integrates with file editing and creation handlers
- Supports iterative code improvement

### With Testing Handlers
- Recommends test coverage improvements  
- Identifies areas needing additional testing
- Suggests test scenarios for edge cases

### With Documentation Handlers
- Recommends documentation improvements
- Identifies undocumented public APIs
- Suggests inline comment additions

## Best Practices
- Always read the full context before reviewing
- Provide constructive, specific feedback
- Balance criticism with recognition of good practices
- Include examples in suggestions when possible
- Consider the broader codebase architecture
- Prioritize security and performance issues
- Suggest incremental improvements for large issues