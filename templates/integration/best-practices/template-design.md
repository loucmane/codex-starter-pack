---
id: template-design
type: integration-guide
category: best-practices
title: Template Design Principles
audience: architect
complexity: intermediate
dependencies:
  - template-architecture
  - handler-design
prerequisites:
  - Understanding of template system
  - Knowledge of modular design
  - Familiarity with YAML frontmatter
version: 1.0.0
status: stable
---

# Template Design Principles

## Overview

This guide covers best practices and principles for designing effective templates in the Claude Template System, from individual templates to system-wide architecture.

## Prerequisites

- Understanding of the template system structure
- Knowledge of modular design principles
- Familiarity with YAML frontmatter
- Experience with markdown formatting

## Core Design Principles

### 1. Modularity

```markdown
## Modular Structure

✅ **Good: Modular Design**
```
templates/
├── engine/          # Core execution
├── handlers/        # Atomic handlers
├── integration/     # Extension guides
└── *.md            # Core templates
```

Each module has:
- Single responsibility
- Clear boundaries
- Explicit dependencies
- Standalone documentation

❌ **Bad: Monolithic Design**
```
.claude/
└── EVERYTHING.md  # 5000+ lines!
```
```

### 2. Discoverability

```markdown
## Make Templates Discoverable

### Good Practices:
- Clear, descriptive names
- Comprehensive indexes
- Cross-references
- Search-friendly keywords
- Navigation aids

### Template Naming:
✅ `implement-feature.md`
✅ `debug-error.md`
✅ `optimize-performance.md`

❌ `template1.md`
❌ `misc.md`
❌ `stuff.md`
```

### 3. Progressive Disclosure

```markdown
## Information Hierarchy

```yaml
template_structure:
  - quick_start:     # Immediate value
      lines: 10-20
      purpose: Get user started fast
  
  - core_content:    # Main information
      lines: 50-200
      purpose: Complete functionality
  
  - advanced:        # Deep details
      lines: 50-100
      purpose: Power users
  
  - reference:       # Lookup material
      lines: variable
      purpose: Comprehensive reference
```

Users find what they need at their level.
```

## Template Structure Best Practices

### YAML Frontmatter Standards

```yaml
---
id: unique-template-id        # Required: Unique identifier
type: template-type           # Required: template|handler|guide
category: template-category   # Required: Category for organization
title: Human Readable Title   # Required: Display title
audience: target-audience     # Optional: developer|user|architect
complexity: level            # Optional: beginner|intermediate|advanced
dependencies:                # Optional: Other templates needed
  - dependency-1
  - dependency-2
prerequisites:               # Optional: Knowledge required
  - prerequisite-1
  - prerequisite-2
version: 1.0.0               # Required: Semantic version
status: stable               # Required: stable|beta|experimental|deprecated
---
```

### Content Organization

```markdown
# Template Title

## Overview
[Brief description - 2-3 sentences]

## Prerequisites
[What user needs to know/have]

## Quick Start
[Immediate value - get going fast]

## Main Content
[Core functionality and details]

### Subsection 1
[Organized by logic/workflow]

### Subsection 2
[Clear progression]

## Examples
[Real-world usage examples]

## Common Issues
[Troubleshooting guide]

## Related Resources
[Links to related templates]
```

### Navigation Aids

```markdown
## Navigation Elements

### Table of Contents
```markdown
## Quick Navigation
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)
```

### Cross-References
```markdown
For more details, see:
- [Handler Creation](../guides/creating-handlers.md)
- [System Architecture](../architecture/system-architecture.md)
```

### Breadcrumbs
```markdown
[Templates](../) > [Integration](.) > Template Design
```
```

## Writing Style Guidelines

### Clarity and Conciseness

```markdown
## Good Writing Practices

✅ **Clear and Direct**:
"This handler processes user input and returns validated data."

❌ **Vague and Wordy**:
"This particular handler has the capability to potentially process various forms of user input that might be submitted and, after processing, it generally tends to return data that has been validated."

### Use:
- Active voice
- Present tense
- Simple sentences
- Concrete examples
- Consistent terminology
```

### Code Examples

```markdown
## Effective Code Examples

### DO:
- Show complete, working examples
- Include context and setup
- Highlight important parts
- Explain non-obvious code
- Test examples before including

### Example:
```yaml
# Complete working example
handler: process-data
input:
  data: [1, 2, 3]  # Input array
  format: json     # Specify format
process:
  1. Validate input format
  2. Transform data
  3. Return processed result
output:
  result: [2, 4, 6]  # Transformed data
  metadata: {...}    # Additional info
```
```

### Visual Hierarchy

```markdown
## Use Formatting for Clarity

# Level 1: Major Sections
## Level 2: Subsections
### Level 3: Topics
#### Level 4: Subtopics (sparingly)

**Bold** for emphasis
*Italic* for terms
`Code` for inline code
> Blockquotes for important notes

- Bullets for lists
1. Numbers for sequences

✅ Do this
❌ Don't do this
⚠️ Warning
💡 Tip
```

## Template Categories

### Core Templates

```yaml
core_templates:
  - REGISTRY.md:     # Handler index
      purpose: Central handler registry
      update: When handlers added/removed
  
  - templates/workflows/:    # Workflow definitions
      purpose: Complex workflow patterns
      update: New workflows added
  
  - templates/conventions/:  # Standards
      purpose: Coding and naming standards
      update: Standards change
  
  - USER-GUIDE.md:   # User documentation
      purpose: End-user guidance
      update: New features/changes
```

### Handler Templates

```yaml
handler_structure:
  triggers/:         # User-activated
    - development/   # By domain
    - git/
    - search/
  
  orchestrators/:    # Coordination
    - No subfolders  # Cross-domain
  
  operators/:        # Technical tasks
    - development/   # By domain
    - git/
    - search/
```

### Integration Templates

```yaml
integration_structure:
  guides/:           # How-to guides
    - creating-handlers.md
    - extending-templates.md
  
  cross-system/:     # System integration
    - mcp-integration.md
    - tool-integration.md
  
  composition/:      # Pattern composition
    - workflow-composition.md
    - handler-chaining.md
  
  best-practices/:   # Guidelines
    - handler-design.md
    - template-design.md
  
  architecture/:     # System design
    - system-architecture.md
    - handler-architecture.md
```

## Version Management

### Semantic Versioning

```yaml
version: MAJOR.MINOR.PATCH

MAJOR: Breaking changes
MINOR: New features, backward compatible
PATCH: Bug fixes, minor improvements

Examples:
  1.0.0: Initial stable release
  1.1.0: Added new handlers
  1.1.1: Fixed typos
  2.0.0: Restructured template format
```

### Change Documentation

```markdown
## Changelog Format

### Version 2.0.0 - 2024-01-20
#### Breaking Changes
- Changed handler format to YAML frontmatter
- Moved handlers to folder structure

#### Added
- New orchestrator handlers
- Integration test suite

#### Fixed
- Handler discovery issues
- Performance bottlenecks

#### Deprecated
- Old handler format (remove in 3.0.0)
```

## Testing Templates

### Template Validation

```yaml
validation_checklist:
  structure:
    - Valid YAML frontmatter
    - Required fields present
    - Consistent formatting
    - Working anchor links
  
  content:
    - Examples work
    - Code blocks valid
    - Cross-references exist
    - No broken links
  
  usability:
    - Easy to navigate
    - Clear instructions
    - Logical flow
    - Complete information
```

### User Testing

```markdown
## Template User Testing

1. **Task-Based Testing**
   - Give users specific tasks
   - Observe template usage
   - Note confusion points
   - Measure completion time

2. **Feedback Collection**
   - What was helpful?
   - What was confusing?
   - What was missing?
   - Suggestions for improvement

3. **Iteration**
   - Update based on feedback
   - Test changes
   - Document improvements
```

## Common Anti-Patterns

### Anti-Pattern: Wall of Text

```markdown
❌ **Bad: No Structure**
This template does everything you need for handling user input validation and processing with automatic error handling and recovery mechanisms built in for resilience and it also provides logging and monitoring capabilities with real-time alerting...

✅ **Good: Structured Content**
## Purpose
Handles user input validation and processing.

## Features
- Automatic error handling
- Recovery mechanisms
- Built-in resilience

## Monitoring
- Comprehensive logging
- Real-time alerts
```

### Anti-Pattern: Assumption of Knowledge

```markdown
❌ **Bad: Assumes Too Much**
"Just use the standard MVC pattern with DI and IoC."

✅ **Good: Explains Concepts**
"Use the Model-View-Controller (MVC) pattern:
- Model: Data and business logic
- View: User interface
- Controller: Coordinates Model and View

With Dependency Injection (DI) for loose coupling."
```

### Anti-Pattern: No Examples

```markdown
❌ **Bad: Abstract Only**
"The handler processes data according to rules."

✅ **Good: Concrete Examples**
"The handler processes data according to rules:

```yaml
input: {name: "John", age: 30}
rules: 
  - Capitalize name
  - Validate age > 0
output: {name: "JOHN", age: 30, valid: true}
```"
```

## Template Maintenance

### Regular Review Schedule

```yaml
maintenance_schedule:
  weekly:
    - Check for broken links
    - Update handler counts
    - Fix reported issues
  
  monthly:
    - Review user feedback
    - Update examples
    - Improve unclear sections
  
  quarterly:
    - Major structure review
    - Version updates
    - Deprecation notices
  
  yearly:
    - Complete overhaul
    - Architecture review
    - User survey
```

### Deprecation Process

```markdown
## Template Deprecation

1. **Mark as Deprecated**
   ```yaml
   status: deprecated
   deprecated_date: 2024-01-01
   replacement: new-template.md
   removal_date: 2024-06-01
   ```

2. **Add Warning Banner**
   > ⚠️ **DEPRECATED**: This template is deprecated.
   > Use [new-template.md](new-template.md) instead.

3. **Provide Migration Path**
   - Clear instructions
   - Automated tools if possible
   - Support period

4. **Remove After Grace Period**
   - Archive old version
   - Update all references
   - Document in changelog
```

## Examples of Well-Designed Templates

### Example: Handler Template

```markdown
---
id: implement-feature
type: handler
category: development
title: Feature Implementation Handler
version: 1.0.0
status: stable
---

# Feature Implementation Handler

## Overview
Implements complete features with tests and documentation.

## Quick Start
```yaml
trigger: "implement user authentication"
result: Complete auth system with tests
```

## Process
1. **Analysis** - Break down requirements
2. **Design** - Create implementation plan  
3. **Implementation** - Code with tests
4. **Validation** - Ensure quality

## Examples
[Real examples with explanations]

## Troubleshooting
[Common issues and solutions]
```

## Checklist for Template Design

### Pre-Design
- [ ] Purpose clearly defined
- [ ] Audience identified
- [ ] Scope determined
- [ ] Dependencies mapped

### Design
- [ ] Structure planned
- [ ] Navigation considered
- [ ] Examples prepared
- [ ] Error cases covered

### Implementation
- [ ] YAML frontmatter complete
- [ ] Sections well-organized
- [ ] Examples tested
- [ ] Links verified

### Review
- [ ] User tested
- [ ] Feedback incorporated
- [ ] Documentation complete
- [ ] Version tagged

## Related Resources

- [Handler Design](handler-design.md)
- [Template Architecture](../architecture/template-architecture.md)
- [System Architecture](../architecture/system-architecture.md)
- [Creating Handlers](../guides/creating-handlers.md)
- [Integration Patterns](integration-patterns.md)