---
id: creating-handlers
type: integration-guide
category: guides
title: Creating and Managing Handlers
audience: developer
complexity: intermediate
dependencies:
  - handler-design
  - template-architecture
prerequisites:
  - Understanding of YAML frontmatter
  - Familiarity with template system
  - Knowledge of handler roles (trigger/orchestrator/operator)
version: 1.0.0
status: stable
---

# Creating and Managing Handlers

## Overview

This guide covers the complete process of creating new handlers for the Claude Template System, including documentation standards, validation requirements, and integration procedures.

## Prerequisites

- Understanding of the three handler roles: triggers, orchestrators, and operators
- Familiarity with YAML frontmatter requirements
- Knowledge of the template system's modular structure
- Access to `templates/handlers/` directory

## Handler Documentation Format Standard

Every handler MUST include these 8 sections in this exact order:

```markdown
#### Handler: handler-name {#handler-name}
**Triggers**: Comma-separated list of exact phrases that activate this handler
**Target Pattern**: What the handler extracts or acts upon from user input
**Pre-conditions**: 
- Bulleted list of conditions that must be true
- Before this handler can execute successfully
**Process**:
1. Numbered steps the handler follows
2. Each step should be clear and actionable
3. Include specific tools or templates used
4. Show routing logic if applicable
5. End with concrete outcome
**Success**: What happens when handler completes successfully
**Failure**: What happens when handler cannot complete
**Examples**:
- Input phrase → Expected outcome
- Another example → Another outcome
```

## YAML Frontmatter Requirements

Every handler file MUST have valid YAML frontmatter:

```yaml
---
id: handler-kebab-case-id
name: Human Readable Handler Name
role: trigger|orchestrator|operator
domain: development|git|search|debug|test|docs|workflow
stability: stable|beta|experimental
triggers: ["user phrases that activate this handler"]
dependencies: ["other-handler-ids"]
tools: ["Tool1", "Tool2"]
version: 1.0.0
---
```

### Field Definitions

- **id**: Unique kebab-case identifier matching the filename
- **name**: Human-readable name for the handler
- **role**: One of trigger, orchestrator, or operator
- **domain**: Primary domain the handler operates in
- **stability**: Current stability level
- **triggers**: Array of phrases that activate the handler
- **dependencies**: Other handlers this one depends on
- **tools**: Tools the handler uses (Read, Write, Grep, etc.)
- **version**: Semantic version number

## When to Create a New Handler

Create a new handler when:
- Users repeatedly ask for something with no handler
- A common development task lacks a direct trigger
- Multiple users phrase the same need differently
- A workflow requires a specific entry point
- An existing handler is too complex and needs decomposition

## Step-by-Step Creation Process

### 1. Identify the Need

- Verify no existing handler covers this need
- Search `templates/handlers/` for similar functionality
- Confirm users actually request this functionality
- Ensure it would be used frequently
- Check it's distinct from existing handlers

### 2. Determine Handler Type and Domain

**Handler Role:**
- **Trigger**: Responds to user commands (goes in `triggers/[domain]/`)
- **Orchestrator**: Coordinates multiple handlers (goes in `orchestrators/`)
- **Operator**: Performs specific technical tasks (goes in `operators/[domain]/`)

**Domain Classification:**
- **development**: Code implementation, features, components
- **git**: Version control operations
- **search**: Finding code, files, or patterns
- **debug**: Problem investigation and fixing
- **test**: Testing and validation
- **docs**: Documentation operations
- **workflow**: Process management

### 3. Write the Handler

Follow the standard format exactly:
- Use realistic trigger phrases
- Make process steps actionable
- Include clear success/failure conditions
- Reference actual tools and handlers

### 4. Create the Handler File

Location based on role and domain:
- Triggers: `templates/handlers/triggers/[domain]/[handler-id].md`
- Orchestrators: `templates/handlers/orchestrators/[handler-id].md`
- Operators: `templates/handlers/operators/[domain]/[handler-id].md`

### 5. Test the Handler

- Test discovery via triggers
- Verify YAML frontmatter is valid
- Follow process steps manually
- Confirm success/failure modes
- Check dependencies exist

### 6. Integration Steps

- Update handler registry if one exists
- Add cross-references from related handlers
- Update routing handlers if needed
- Document in migration mapping
- Test with real user scenarios

## Common Handler Patterns

### Feature Implementation Handler

```markdown
---
id: implement-auth-system
name: Implement Authentication System
role: trigger
domain: development
stability: stable
triggers: ["implement auth", "build authentication", "add login system"]
dependencies: ["break-down-feature", "create-todos"]
tools: ["Write", "MultiEdit"]
version: 1.0.0
---

#### Handler: implement-auth-system
**Triggers**: "implement auth", "build authentication", "add login system"
**Target Pattern**: Authentication feature specification
**Pre-conditions**: 
- Requirements are clear
- Work folder exists
- Technology stack decided
**Process**:
1. Break down into authentication components
2. Create todos for each component
3. Route to development workflow
4. Implement sequentially with testing
**Success**: Authentication system implemented and tested
**Failure**: Requirements unclear, needs specification
**Examples**:
- "implement JWT auth" → Creates JWT authentication system
- "add OAuth login" → Implements OAuth provider integration
```

### Tool Usage Handler

```markdown
---
id: search-codebase
name: Search Codebase for Patterns
role: operator
domain: search
stability: stable
triggers: ["search for", "find in code", "grep for"]
dependencies: []
tools: ["Grep", "Glob"]
version: 1.0.0
---

#### Handler: search-codebase
**Triggers**: "search for X", "find Y in code", "grep for Z"
**Target Pattern**: Search term and scope
**Pre-conditions**: 
- Search pattern is clear
- Scope is defined or defaults to project
**Process**:
1. Extract search pattern
2. Determine file scope
3. Execute Grep with appropriate flags
4. Process and format results
**Success**: Search results found and displayed
**Failure**: No matches or invalid pattern
**Examples**:
- "search for TODO comments" → Finds all TODOs
- "find useState in components" → Locates React hooks
```

## Documentation Best Practices

### DO:
- ✅ Keep triggers realistic - what users actually say
- ✅ Make process steps concrete and actionable
- ✅ Include tool names when tools are used
- ✅ Show routing to templates/other handlers
- ✅ Make examples diverse to show handler range
- ✅ Use consistent formatting throughout
- ✅ Include YAML frontmatter for every handler
- ✅ Test handlers with real scenarios

### DON'T:
- ❌ Make triggers too abstract or technical
- ❌ Write vague process steps like "analyze the code"
- ❌ Skip pre-conditions - use "None" if none exist
- ❌ Write multi-line success/failure descriptions
- ❌ Use different formatting styles
- ❌ Create handlers without clear use cases
- ❌ Duplicate existing handler functionality

## Validation Checklist

Before committing your handler:
- [ ] YAML frontmatter is valid and complete
- [ ] Handler ID matches filename
- [ ] Role and domain are correctly set
- [ ] Triggers are phrases users actually say
- [ ] Target pattern is clear
- [ ] Pre-conditions are verifiable
- [ ] Process steps are concrete
- [ ] Success/failure are single lines
- [ ] Examples show real usage
- [ ] Dependencies exist in handlers directory
- [ ] Tools listed are actual available tools
- [ ] No overlap with existing handlers
- [ ] File is in correct directory structure

## Enhanced Keywords Guide

Keywords are critical for handler discovery. When documenting handlers:

### Think Like a User
- What words would they use?
- Include common misspellings
- Add domain-specific terms
- Consider synonyms

### Keyword Categories
- **Action words**: create, build, make, implement
- **Problem words**: bug, error, issue, broken
- **Technical terms**: component, service, API, hook
- **Emotional words**: stuck, confused, help, frustrated

### Keyword Density
- Aim for 5-10 keywords per handler
- Balance specific and general terms
- Include both technical and natural language

### Testing Keywords
- Search handlers directory with each keyword
- Verify handler appears in results
- Check for keyword conflicts
- Update if discovery fails

Remember: Handlers are only useful if users can find them!

## Examples

### Real Handler from System

Here's an actual handler from `templates/handlers/triggers/development/implement-feature.md`:

```markdown
---
id: implement-feature
name: Implement Feature Development
role: trigger
domain: development
stability: stable
triggers: ["implement", "build feature", "create functionality"]
dependencies: ["break-down-tasks", "sequential-implementation"]
tools: ["Write", "MultiEdit", "Read"]
version: 1.0.0
---

#### Handler: implement-feature
**Triggers**: "implement X", "build Y feature", "add Z functionality"
**Target Pattern**: Feature name and requirements
**Pre-conditions**:
- Feature requirements are clear
- Work tracking folder exists
- Technical approach decided
**Process**:
1. Break feature into components
2. Create implementation todos
3. Execute sequential implementation
4. Test each component
5. Integrate and validate
**Success**: Feature implemented and working
**Failure**: Requirements unclear or blockers found
**Examples**:
- "implement user dashboard" → Creates dashboard feature
- "build search functionality" → Implements search system
```

## Common Pitfalls

### Handler Too Broad
**Problem**: Handler tries to do too much
**Solution**: Break into smaller, focused handlers

### Missing Dependencies
**Problem**: Handler references non-existent handlers
**Solution**: Verify all dependencies exist before creation

### Vague Process Steps
**Problem**: Steps like "analyze and implement"
**Solution**: Break into concrete, actionable steps

### Wrong Role Classification
**Problem**: Trigger handler doing orchestration work
**Solution**: Understand role distinctions clearly

## Testing Your Implementation

1. **Syntax Validation**
   - YAML frontmatter parses correctly
   - Markdown formatting is valid
   - File naming matches ID

2. **Functional Testing**
   - Triggers activate handler
   - Process steps execute
   - Dependencies resolve
   - Tools are available

3. **Integration Testing**
   - Handler works with system
   - Cross-references work
   - No conflicts with existing handlers

## Related Resources

- [Handler Design Best Practices](../best-practices/handler-design.md)
- [Template Architecture](../architecture/template-architecture.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- [System Integration Guide](system-integration.md)
- Existing handlers in `templates/handlers/` for examples