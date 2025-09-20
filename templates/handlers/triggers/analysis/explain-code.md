---
id: explain-code
name: Explain Code
role: trigger
domain: analysis
stability: stable
triggers:
  - "explain this code"
  - "how does X work"
  - "what does this do"
  - "explain function"
  - "analyze this code"
  - "walk through this code"
  - "break down this code"
dependencies: []
tools:
  - Read
  - mcp__serena__find_symbol
  - mcp__serena__get_symbols_overview
version: 1.0.0
---

# Explain Code Handler

## Purpose
Analyze and explain code functionality, breaking down complex logic into clear, understandable terms for users.

## Triggers
- "explain this code"
- "how does X work"
- "what does this do"
- "explain function"
- "analyze this code"
- "walk through this code"

## Target Pattern
Code references (file paths, function names, code snippets) requiring explanation.

## Pre-conditions
- Code context is accessible (file path or symbol reference)
- Valid code structure exists
- User has provided specific code to analyze

## Process

1. **Identify code context**
   - Extract file path, function name, or code snippet from request
   - Determine scope of explanation needed (single function, class, file)

2. **Read code context**
   - Use Read tool to access file contents
   - Use mcp__serena__find_symbol for specific symbols
   - Use mcp__serena__get_symbols_overview for broader context

3. **Analyze functionality**
   - Identify main purpose and responsibility
   - Map data flow and control flow
   - Note key algorithms or patterns used
   - Identify dependencies and side effects

4. **Structure explanation**
   - Start with high-level purpose
   - Break into logical sections or steps
   - Explain complex parts in simpler terms
   - Highlight important patterns or decisions

5. **Provide clear explanation**
   - Use plain language for technical concepts
   - Include examples where helpful
   - Point out edge cases or special handling
   - Explain why code is structured as it is

6. **Offer additional context**
   - Suggest related code to understand
   - Mention potential improvements or concerns
   - Link to broader system context if relevant

## Success Criteria
- User understands the code's purpose and functionality
- Complex logic is broken down into digestible parts
- Key patterns and decisions are explained
- User can follow the code flow logically

## Failure Modes
- **Code not found**: Invalid path or symbol name
- **Code too complex**: Break into smaller parts for explanation
- **Insufficient context**: Request more specific area to analyze
- **Ambiguous request**: Ask for clarification on what aspect to explain

## Examples

### Example 1: Function Explanation
**Input**: "explain this authentication function"
**Process**: 
- Find authentication function with mcp__serena__find_symbol
- Read surrounding context
- Explain: purpose, parameters, return value, key steps

### Example 2: File Overview
**Input**: "what does utils/helpers.js do"
**Process**:
- Read entire file
- Get symbols overview
- Explain: main exports, utility functions, overall purpose

### Example 3: Code Snippet
**Input**: "explain this code block" (with pasted code)
**Process**:
- Analyze provided snippet
- Explain: logic flow, purpose, key operations
- Note any missing context or dependencies

## Integration Points

### With mcp__serena__find_symbol
- Locate specific functions, classes, or variables
- Get precise symbol definitions
- Understand symbol relationships

### With mcp__serena__get_symbols_overview
- Understand file structure and organization
- Get context for symbol relationships
- Map out architectural patterns

### With Read Tool
- Access complete file contents
- Read configuration or data files
- Understand implementation details

## Best Practices
- Always start with the "why" before the "how"
- Use concrete examples to illustrate abstract concepts
- Break complex functions into logical steps
- Explain trade-offs and design decisions
- Point out patterns that appear elsewhere in codebase
- Avoid overwhelming detail - focus on key insights
- Ask follow-up questions to ensure understanding