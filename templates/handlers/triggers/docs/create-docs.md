---
id: create-docs
name: Create Documentation
role: trigger
domain: docs
stability: stable
triggers:
  - "document this"
  - "create docs"
  - "write documentation"
  - "add documentation"
dependencies: []
tools:
  - Read
  - Write
  - mcp__serena__get_symbols_overview
  - mcp__serena__find_symbol
version: 1.0.0
---

#### Handler: create-docs {#create-docs}
**Triggers**: "document this", "create docs", "write documentation", "add documentation"
**Target Pattern**: Code or feature to document
**Pre-conditions**: 
- Code exists and is stable
- Understand the audience (users, developers, etc.)
**Process**:
1. **Analyze code structure**
   - Read source files to understand components
   - Use mcp__serena__get_symbols_overview for project overview
   - Use mcp__serena__find_symbol for specific functions/classes
   - Identify public APIs and interfaces
2. **Extract key information**
   - Function signatures and parameters
   - Class structures and inheritance
   - Configuration options
   - Dependencies and relationships
   - Usage patterns and examples
3. **Write clear documentation**
   - Create structured content with headers
   - Include code examples and snippets
   - Add usage instructions and best practices
   - Document error handling and edge cases
   - Provide troubleshooting guidance
4. **Add to appropriate location**
   - Follow project documentation conventions
   - Place in correct directory structure
   - Update existing docs or create new files
   - Ensure consistent formatting and style
**Success**: Clear, helpful documentation created
**Failure**: Documentation without examples
**Examples**:
- "document the API" → API reference docs
- "write README for auth" → Module documentation
- "create user guide" → End-user documentation