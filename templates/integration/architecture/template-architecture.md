---
id: template-architecture
type: integration-guide
category: architecture
title: Template System Design
audience: architect
complexity: advanced
dependencies:
  - system-architecture
  - handler-architecture
prerequisites:
  - Understanding of template systems
  - Knowledge of modular architecture
  - Familiarity with the evolution from monolithic to modular
version: 1.0.0
status: stable
---

# Template System Design

## Overview

This document describes the architecture of the template system, including its modular structure, template types, navigation patterns, and the evolution from monolithic to modular design.

## Prerequisites

- Understanding of template-based systems
- Knowledge of modular architecture principles
- Familiarity with the system's evolution history
- Understanding of markdown and YAML

## Template System Evolution

### From Monolithic to Modular

```markdown
## Evolution Timeline

### Phase 1: Monolithic (Original)
- Single CLAUDE.md file
- 1400+ lines
- Everything in one place
- Hard to navigate
- Difficult to maintain

### Phase 2: Initial Split
- Separated into multiple files
- REGISTRY, WORKFLOWS, TOOLS, etc.
- Better organization
- Still had embedded handlers

### Phase 3: Handler Extraction
- Handlers moved to folders
- Three-role model introduced
- Domain-based organization
- Improved discoverability

### Phase 4: Full Modularization (Current)
- Complete modular structure
- Engine separation
- Integration guides extracted
- Clear architectural layers
```

## Current Template Architecture

### Directory Structure

```
templates/
├── engine/              # Execution engine modules
│   ├── activation/     # Context-aware activation
│   ├── core/           # ULTRATHINK protocol
│   ├── enforcement/    # Behavioral constraints
│   ├── execution/      # SWHE format
│   ├── navigation/     # Template routing
│   ├── fallbacks/      # Error handling
│   ├── debugging/      # System debugging
│   ├── structure/      # Template structure
│   └── examples/       # Practical examples
│
├── handlers/            # Handler library
│   ├── triggers/       # User-activated handlers
│   │   ├── development/
│   │   ├── git/
│   │   ├── search/
│   │   ├── debug/
│   │   ├── test/
│   │   ├── docs/
│   │   └── workflow/
│   ├── orchestrators/  # Coordination handlers
│   └── operators/      # Technical handlers
│       ├── development/
│       ├── git/
│       └── [domains...]
│
├── integration/         # Extension and integration
│   ├── guides/         # How-to guides
│   ├── cross-system/   # System integration
│   ├── composition/    # Pattern composition
│   ├── best-practices/ # Guidelines
│   └── architecture/   # System design
│
└── *.md                 # Core template files
    ├── REGISTRY.md      # Handler index
    ├── templates/workflows/     # Workflow patterns
    ├── templates/conventions/   # Standards
    ├── USER-GUIDE.md    # User documentation
    └── templates/integration/ # System extension (index)
```

## Template Types

### Core Templates

```yaml
core_templates:
  REGISTRY.md:
    type: index
    purpose: Central handler registry
    content:
      - Handler listings
      - Keywords for discovery
      - Cross-references
    update_frequency: On handler changes
  
  Domain workflows:
    type: workflows
    purpose: Modular workflow definitions
    content:
      - templates/workflows/domain/*
      - Session/testing/docs/development workflows
      - Examples under templates/workflows/examples/
    update_frequency: On new workflows
  
  CONVENTIONS.md:
    type: standards
    purpose: Coding and naming standards
    content:
      - Naming conventions
      - Code standards
      - Best practices
    update_frequency: On standard changes
  
  USER-GUIDE.md:
    type: documentation
    purpose: End-user guidance
    content:
      - Quick reference
      - Common patterns
      - Troubleshooting
    update_frequency: On feature changes
  
  System improvement:
    type: orchestrator docs
    purpose: System extension guidance
    content:
      - templates/handlers/orchestrators/system-improvement.md
      - Related improvement workflows
    update_frequency: On improvement initiatives
```

### Engine Templates

```yaml
engine_templates:
  activation:
    purpose: Context-aware system activation
    modules:
      - context-aware.md
  
  core:
    purpose: Core execution protocols
    modules:
      - ultrathink-protocol.md
      - pre-ultrathink.md
      - enforcement-check.md
  
  execution:
    purpose: Request execution
    modules:
      - swhe-format.md
  
  navigation:
    purpose: Template navigation
    modules:
      - template-protocol.md
      - common-flows.md
```

### Integration Templates

```yaml
integration_templates:
  guides:
    purpose: How-to documentation
    templates:
      - creating-handlers.md
      - extending-templates.md
      - adding-agents.md
      - system-integration.md
  
  cross_system:
    purpose: External integration
    templates:
      - mcp-integration.md
      - tool-integration.md
      - agent-coordination.md
  
  composition:
    purpose: Pattern composition
    templates:
      - workflow-composition.md
      - handler-chaining.md
      - pattern-composition.md
  
  best_practices:
    purpose: Design guidelines
    templates:
      - handler-design.md
      - template-design.md
      - integration-patterns.md
  
  architecture:
    purpose: System design docs
    templates:
      - system-architecture.md
      - handler-architecture.md
      - template-architecture.md
```

## Template Metadata

### YAML Frontmatter Standard

```yaml
---
id: unique-identifier          # Required
type: template-type            # Required
category: template-category    # Required
title: Human Readable Title    # Required
audience: target-audience      # Optional
complexity: difficulty-level   # Optional
dependencies:                  # Optional
  - dependency-1
  - dependency-2
prerequisites:                 # Optional
  - prerequisite-1
version: 1.0.0                # Required
status: stable|beta|experimental|deprecated  # Required
---
```

### Metadata Types

```yaml
metadata_types:
  type:
    values:
      - template: Core template file
      - handler: Handler definition
      - guide: How-to guide
      - reference: Reference documentation
      - integration-guide: Integration documentation
  
  status:
    values:
      - stable: Production ready
      - beta: Testing phase
      - experimental: Proof of concept
      - deprecated: Being phased out
  
  complexity:
    values:
      - beginner: New users
      - intermediate: Regular users
      - advanced: Power users
      - expert: System developers
```

## Navigation Patterns

### Navigation Hierarchy

```markdown
## Navigation Levels

### Level 1: Entry Points
- USER-GUIDE.md (for users)
- REGISTRY.md (for discovery)
- templates/integration/ (for developers)

### Level 2: Category Pages
- templates/workflows/ (workflows)
- templates/conventions/ (standards)
- integration/ (extension)

### Level 3: Specific Content
- Individual handlers
- Specific guides
- Detailed documentation
```

### Cross-Reference Network

```yaml
cross_references:
  types:
    - direct_link: [[Handler: handler-name]]
    - see_also: "See also: [related-topic](path)"
    - prerequisite: "Requires: [prerequisite](path)"
    - next_step: "Next: [next-topic](path)"
  
  patterns:
    - hub_and_spoke: Central index with links
    - sequential: Step-by-step progression
    - web: Interconnected references
    - hierarchical: Tree structure
```

### Discovery Mechanisms

```yaml
discovery:
  search:
    - Full-text search
    - Keyword matching
    - Tag-based search
  
  navigation:
    - Table of contents
    - Breadcrumbs
    - Related links
  
  indexes:
    - REGISTRY.md for handlers
    - Topic indexes
    - Alphabetical lists
```

## Template Processing

### Loading Strategy

```yaml
loading:
  strategy: lazy
  process:
    1. Load core templates on start
    2. Parse frontmatter metadata
    3. Build navigation index
    4. Load handlers on demand
    5. Cache frequently used
  
  optimization:
    - Preload common templates
    - Index for fast search
    - Cache parsed content
    - Stream large files
```

### Template Parsing

```python
# Conceptual template parser
class TemplateParser:
    def parse(self, template_path):
        # 1. Read file
        content = read_file(template_path)
        
        # 2. Parse frontmatter
        metadata = parse_yaml_frontmatter(content)
        
        # 3. Parse content
        sections = parse_markdown_sections(content)
        
        # 4. Extract handlers (if any)
        handlers = extract_handlers(sections)
        
        # 5. Build template object
        return Template(
            metadata=metadata,
            sections=sections,
            handlers=handlers
        )
```

## Template Relationships

### Dependency Graph

```yaml
dependencies:
  USER-GUIDE.md:
    depends_on:
      - REGISTRY.md
      - templates/workflows/
    referenced_by:
      - README.md
  
  REGISTRY.md:
    depends_on:
      - handlers/**/*.md
    referenced_by:
      - All templates
  
  handlers/**/*.md:
    depends_on:
      - tools
      - other handlers
    referenced_by:
      - REGISTRY.md
      - templates/workflows/
```

### Template Composition

```yaml
composition:
  includes:
    description: Template includes another
    example: WORKFLOWS includes handler refs
  
  extends:
    description: Template extends another
    example: Custom workflow extends base
  
  references:
    description: Template references another
    example: Guide references handlers
  
  aggregates:
    description: Template aggregates others
    example: REGISTRY aggregates all handlers
```

## Performance Considerations

### Optimization Strategies

```yaml
optimizations:
  caching:
    - Cache parsed templates
    - Cache navigation structure
    - Cache search indexes
    ttl: 3600 seconds
  
  indexing:
    - Build search index
    - Maintain cross-references
    - Update incrementally
  
  lazy_loading:
    - Load templates on demand
    - Defer parsing until needed
    - Stream large content
  
  preloading:
    - Preload core templates
    - Preload common handlers
    - Warm cache on start
```

## Template Versioning

### Version Management

```yaml
versioning:
  strategy: semantic
  format: MAJOR.MINOR.PATCH
  
  compatibility:
    - Major: Breaking changes
    - Minor: New features
    - Patch: Bug fixes
  
  migration:
    - Provide migration guides
    - Support grace period
    - Automated migration tools
```

## Template Testing

### Test Categories

```yaml
testing:
  structural:
    - Valid YAML frontmatter
    - Correct markdown syntax
    - Working links
    - Proper sections
  
  content:
    - Examples work
    - Code blocks valid
    - Instructions clear
    - Complete information
  
  integration:
    - Cross-references work
    - Dependencies exist
    - Navigation intact
    - Discovery functional
```

## Security Model

### Template Security

```yaml
security:
  access_control:
    - Read permissions
    - Write restrictions
    - Execution limits
  
  content_validation:
    - Sanitize inputs
    - Validate structure
    - Check for malicious content
  
  sandboxing:
    - Isolate execution
    - Limit resource access
    - Prevent side effects
```

## Future Architecture

### Planned Improvements

```yaml
future:
  dynamic_templates:
    - Runtime template generation
    - Conditional content
    - User-specific views
  
  template_inheritance:
    - Base templates
    - Template extension
    - Override mechanisms
  
  smart_navigation:
    - AI-powered discovery
    - Contextual suggestions
    - Learning from usage
  
  distributed_templates:
    - Remote template loading
    - Template marketplace
    - Version synchronization
```

## Best Practices

### Design Principles

1. **Modularity**: Independent, focused templates
2. **Discoverability**: Easy to find and navigate
3. **Consistency**: Uniform structure and style
4. **Maintainability**: Simple to update and extend
5. **Performance**: Optimized for common use
6. **Accessibility**: Clear for all skill levels
7. **Extensibility**: Easy to add new templates

### Anti-Patterns

1. **Monolithic Templates**: Everything in one file
2. **Circular Dependencies**: Templates requiring each other
3. **Hidden Content**: Important info buried deep
4. **Inconsistent Structure**: Different formats
5. **Missing Metadata**: No frontmatter or version
6. **Broken Links**: References to non-existent content
7. **Outdated Information**: Not maintained regularly

## Related Resources

- [System Architecture](system-architecture.md)
- [Handler Architecture](handler-architecture.md)
- [Template Design](../best-practices/template-design.md)
- [Extending Templates](../guides/extending-templates.md)
- Current templates in `templates/`