---
id: adding-agents
type: integration-guide
category: guides
title: Adding New Agents to the System
audience: developer
complexity: advanced
dependencies:
  - system-integration
  - agent-coordination
prerequisites:
  - Understanding of agent architecture
  - Knowledge of YAML frontmatter
  - Familiarity with task delegation
version: 1.0.0
status: stable
---

# Adding New Agents to the System

## Overview

This guide covers how to add new specialized agents to the Claude Template System, including agent design, implementation, integration, and coordination with existing agents.

## Prerequisites

- Understanding of the agent system in `.claude/agents/`
- Knowledge of agent roles and responsibilities
- Familiarity with YAML frontmatter for agents
- Understanding of task delegation patterns

## Agent System Architecture

### Current Agent Categories

```
.claude/agents/
├── Core Agents
│   ├── agent-coordinator.md      # Multi-agent orchestration
│   ├── meta-agent.md             # Agent system management
│   └── swhe-enforcer.md          # Format enforcement
├── Template Agents
│   ├── template-scanner.md       # Template analysis
│   ├── template-migrator.md      # Handler migration
│   └── template-optimizer.md     # System optimization
├── Development Agents
│   ├── handler-creator.md        # Handler generation
│   ├── pattern-extractor.md      # Pattern identification
│   └── integration-tester.md     # Testing automation
└── Specialized Agents
    ├── security-validator.md      # Security checks
    ├── performance-analyzer.md    # Performance analysis
    └── version-controller.md      # Version management
```

## Agent Definition Format

Every agent MUST follow this structure:

```markdown
---
id: agent-kebab-case-id
name: Human Readable Agent Name
type: specialist|coordinator|analyzer|validator
domain: development|templates|testing|security|performance
capabilities:
  - Primary capability
  - Secondary capability
constraints:
  - What the agent cannot do
  - Scope limitations
inputs:
  - Expected input format
  - Required parameters
outputs:
  - Output format
  - Deliverables
tools:
  - Tool1
  - Tool2
version: 1.0.0
---

# Agent Name

## Purpose
[Clear statement of what this agent does]

## Constraints
[CRITICAL constraints that must be enforced]

## Instructions
[Detailed operational instructions]

## Response Format
[Expected output structure]
```

## Step-by-Step Agent Creation

### 1. Identify the Need

**Questions to Answer:**
- What specialized task needs automation?
- Can existing agents handle this?
- Is the task complex enough to warrant an agent?
- Will multiple users benefit from this agent?

**Example Need:**
"We need automated API documentation generation from code"

### 2. Design the Agent

**Define Core Attributes:**

```yaml
id: api-doc-generator
name: API Documentation Generator
type: specialist
domain: documentation
capabilities:
  - Extract API endpoints from code
  - Generate OpenAPI specifications
  - Create markdown documentation
  - Validate API consistency
constraints:
  - Only processes REST APIs
  - Requires structured code comments
  - Cannot modify source code
```

### 3. Define Agent Behavior

**Core Sections:**

```markdown
## Purpose
Automatically generate comprehensive API documentation from source code, including endpoint descriptions, request/response schemas, and usage examples.

## Constraints
**CRITICAL: Operating boundaries:**
- **Read only**: Never modify source code
- **Scope**: Only REST API endpoints
- **Output**: Only to docs/ directory
- **Format**: OpenAPI 3.0 and Markdown

## Instructions

### Phase 1: Discovery
1. Scan codebase for API endpoints
2. Identify HTTP methods and routes
3. Extract parameter definitions
4. Find response schemas

### Phase 2: Documentation Generation
1. Create OpenAPI specification
2. Generate markdown documentation
3. Include code examples
4. Add authentication details

### Phase 3: Validation
1. Verify all endpoints documented
2. Check for missing parameters
3. Validate example responses
4. Test generated documentation
```

### 4. Implement Agent Integration

**Integration Points:**

```markdown
## Integration with Other Agents

### Upstream Agents
- **code-analyzer**: Provides code structure analysis
- **pattern-extractor**: Identifies API patterns

### Downstream Agents
- **template-documenter**: Formats final documentation
- **version-controller**: Manages doc versions

### Coordination
- Can be invoked by agent-coordinator
- Reports to meta-agent for monitoring
```

### 5. Create Agent File

**Location**: `.claude/agents/api-doc-generator.md`

**Complete Example:**

```markdown
---
id: api-doc-generator
name: API Documentation Generator
type: specialist
domain: documentation
capabilities:
  - Extract API endpoints from code
  - Generate OpenAPI specifications
  - Create markdown documentation
constraints:
  - Read-only operation
  - REST APIs only
  - Structured comments required
inputs:
  - Source code directory
  - API framework type
  - Output format preference
outputs:
  - OpenAPI specification
  - Markdown documentation
  - Usage examples
tools:
  - Read
  - Write
  - Grep
  - MultiEdit
version: 1.0.0
---

# API Documentation Generator

## Purpose
Automatically generate comprehensive API documentation...

[Rest of agent definition]
```

## Agent Coordination Patterns

### Pattern 1: Sequential Delegation

```markdown
## Coordination: Sequential
1. Agent A completes task
2. Passes output to Agent B
3. Agent B processes and continues

Example:
code-scanner → api-doc-generator → template-documenter
```

### Pattern 2: Parallel Execution

```markdown
## Coordination: Parallel
1. Coordinator splits task
2. Multiple agents work simultaneously
3. Results merged by coordinator

Example:
- api-doc-generator (endpoints)
- schema-validator (data models)
- example-generator (usage examples)
```

### Pattern 3: Conditional Routing

```markdown
## Coordination: Conditional
IF condition A:
  Route to Agent X
ELSE IF condition B:
  Route to Agent Y
ELSE:
  Route to Agent Z

Example:
IF Python API: python-doc-agent
IF Node API: node-doc-agent
IF Go API: go-doc-agent
```

## Testing Your Agent

### 1. Unit Testing

```markdown
## Test Cases

### Test 1: Basic Functionality
**Input**: Simple REST API with 3 endpoints
**Expected**: Complete documentation for all endpoints
**Validation**: Check all endpoints documented

### Test 2: Edge Cases
**Input**: API with complex nested schemas
**Expected**: Proper schema documentation
**Validation**: Verify nested structures preserved

### Test 3: Error Handling
**Input**: Malformed API code
**Expected**: Graceful error reporting
**Validation**: No crashes, clear error messages
```

### 2. Integration Testing

```markdown
## Integration Tests

### With Agent Coordinator
- Verify proper task delegation
- Check output format compatibility
- Test error propagation

### With Other Specialists
- Test data exchange formats
- Verify no conflicts
- Check resource sharing
```

### 3. Performance Testing

```markdown
## Performance Metrics

- **Speed**: Process 100 endpoints in < 30 seconds
- **Memory**: Stay under 500MB RAM
- **Accuracy**: 95%+ endpoint detection
- **Completeness**: No missing parameters
```

## Common Agent Types

### Analyzer Agents

```yaml
type: analyzer
purpose: Analyze and report on system aspects
examples:
  - code-complexity-analyzer
  - dependency-analyzer
  - performance-analyzer
```

### Validator Agents

```yaml
type: validator
purpose: Validate and verify system correctness
examples:
  - security-validator
  - schema-validator
  - convention-validator
```

### Generator Agents

```yaml
type: generator
purpose: Generate new content or code
examples:
  - test-generator
  - documentation-generator
  - scaffold-generator
```

### Transformer Agents

```yaml
type: transformer
purpose: Transform existing content
examples:
  - code-migrator
  - format-converter
  - optimization-transformer
```

## Best Practices

### DO:
- ✅ Keep agents focused on single responsibility
- ✅ Define clear input/output contracts
- ✅ Include comprehensive error handling
- ✅ Document coordination requirements
- ✅ Provide usage examples
- ✅ Test with real-world scenarios
- ✅ Version agents for compatibility

### DON'T:
- ❌ Create overly complex agents
- ❌ Duplicate existing agent functionality
- ❌ Ignore constraint boundaries
- ❌ Skip integration testing
- ❌ Forget error handling
- ❌ Make agents too tightly coupled

## Common Pitfalls

### Agent Too Broad
**Problem**: Agent tries to do everything
**Solution**: Split into multiple focused agents

### Poor Error Handling
**Problem**: Agent crashes on unexpected input
**Solution**: Add robust validation and fallbacks

### Missing Coordination
**Problem**: Agent doesn't work with others
**Solution**: Define clear integration points

### Insufficient Testing
**Problem**: Agent fails in production
**Solution**: Comprehensive test coverage

## Examples from System

### Template Scanner Agent

A real agent from the system that analyzes templates:

```markdown
## Purpose
Scans and analyzes template files to extract handler definitions, metadata, and relationships for migration and optimization.

## Capabilities
- Extract handler definitions with line numbers
- Parse handler metadata and structure
- Identify handler relationships
- Generate scanner reports
```

### Template Migrator Agent

An agent that migrates handlers:

```markdown
## Purpose
Migrates handlers from monolithic template files to modular structure while preserving functionality.

## Constraints
- Never modify source templates
- Work only in staging directories
- Preserve exact functionality
```

## Related Resources

- [System Integration](system-integration.md)
- [Agent Coordination](../cross-system/agent-coordination.md)
- [Creating Handlers](creating-handlers.md)
- [Template Architecture](../architecture/template-architecture.md)
- Existing agents in `.claude/agents/` for examples