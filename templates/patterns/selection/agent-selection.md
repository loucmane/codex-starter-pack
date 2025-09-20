---
id: agent-selection-patterns
type: pattern
category: selection
title: Agent Selection Patterns
pattern_type: behavioral
complexity: moderate
dependencies:
  - patterns/selection/handler-selection.md
related:
  - patterns/selection/tool-selection.md
  - .claude/agents/
version: 1.0.0
status: stable
---

# Agent Selection Patterns

## Pattern Description
Patterns for selecting and invoking specialized agents for complex tasks that require specific expertise or focused attention. Agents are invoked through the Task tool for specialized operations.

## Pattern Structure
1. Identify task complexity and requirements
2. Determine if specialized agent needed
3. Select appropriate agent
4. Prepare context for agent
5. Invoke through Task tool
6. Process agent results

## When to Use
- Task requires specialized expertise
- Multiple complex steps needed
- Deep analysis required
- Specific domain knowledge needed
- Task benefits from focused execution

## When NOT to Use
- Simple operations that tools can handle
- Direct handler exists for the task
- Quick one-off operations
- User requests direct execution

## Agent Categories

### Development Agents
- **Component creators**: Specialized in UI components
- **API builders**: REST/GraphQL endpoint creation
- **Database specialists**: Schema and query optimization
- **Testing experts**: Test creation and validation

### Analysis Agents
- **Code analyzers**: Deep code structure analysis
- **Performance analysts**: Performance profiling
- **Security auditors**: Security vulnerability detection
- **Architecture reviewers**: System design analysis

### Migration Agents
- **Template migrators**: Template system migration
- **Code migrators**: Legacy code updates
- **Schema migrators**: Database migrations
- **API migrators**: API version upgrades

### Documentation Agents
- **Doc generators**: Auto-documentation creation
- **API documenters**: OpenAPI/Swagger generation
- **Code commenters**: Inline documentation
- **README writers**: Project documentation

## Selection Criteria

### Primary Factors
1. **Task Match**: Does agent specialize in this task?
2. **Complexity Level**: Is task complex enough for agent?
3. **Domain Match**: Does agent have required domain knowledge?
4. **Tool Requirements**: Does agent have needed tool access?

### Secondary Factors
1. **Performance**: Agent execution time
2. **Reliability**: Agent success rate
3. **Maintenance**: Is agent actively maintained?
4. **Dependencies**: Are agent dependencies available?

## Agent Selection Process

### Step 1: Task Analysis
```
1. Identify primary task goal
2. List required capabilities
3. Determine complexity level
4. Note special requirements
```

### Step 2: Agent Discovery
```
1. Check .claude/agents/ directory
2. Filter by domain/category
3. Read agent descriptions
4. Build candidate list
```

### Step 3: Selection
```
1. Score agents by match criteria
2. Check agent availability
3. Verify agent dependencies
4. Select best match
```

### Step 4: Invocation
```
1. Prepare agent context
2. Format Task tool request
3. Include relevant parameters
4. Execute through Task tool
```

## Common Agent Selection Patterns

### Complex Search Pattern
When searching requires multiple rounds:
```
Task: "Deep search for authentication patterns"
Agent: pattern-extractor or code-analyzer
Reason: Multi-file semantic analysis needed
```

### Migration Pattern
When migrating or refactoring systems:
```
Task: "Migrate templates to new structure"
Agent: template-migrator
Reason: Specialized migration logic and validation
```

### Analysis Pattern
When deep analysis needed:
```
Task: "Analyze system performance bottlenecks"
Agent: performance-analyzer
Reason: Specialized profiling and metrics
```

### Creation Pattern
When creating complex structures:
```
Task: "Create full CRUD API with tests"
Agent: api-builder + testing-expert
Reason: Multiple integrated components
```

## Agent Invocation Examples

### Single Agent Invocation
```
Request: "Analyze the authentication system"
Selection: security-auditor agent
Invocation: Task tool with "Run security audit on auth system"
```

### Multi-Agent Pipeline
```
Request: "Refactor and document the API"
Selection: code-refactorer → api-documenter
Invocation: Sequential Task invocations
```

### Conditional Agent Selection
```
Request: "Fix the performance issue"
Analysis: Determine issue type first
Selection: 
  - If DB: database-optimizer
  - If API: api-performance-tuner
  - If UI: frontend-optimizer
```

## Agent Coordination Patterns

### Sequential Execution
Agents run one after another:
1. Analyzer agent identifies issues
2. Fixer agent resolves issues
3. Validator agent confirms fixes

### Parallel Execution
Multiple agents work simultaneously:
- Doc generator on code
- Test creator on functions
- Linter on style

### Hierarchical Execution
Parent agent coordinates child agents:
- Orchestrator manages sub-agents
- Results aggregated by parent
- Final output consolidated

## Best Practices

### Context Preparation
- Provide clear task description
- Include relevant file paths
- Specify constraints and requirements
- Share previous analysis if available

### Result Handling
- Validate agent output
- Check for completeness
- Merge with existing work
- Document agent decisions

### Error Recovery
- Have fallback for agent failure
- Log agent errors for debugging
- Consider manual intervention
- Try alternative agents

## Anti-Patterns to Avoid

1. **Over-using agents**: Don't use agents for simple tasks
2. **Agent chains too long**: Limit to 3-4 agents maximum
3. **Circular dependencies**: Avoid agents calling each other
4. **Missing context**: Always provide sufficient context
5. **Ignoring failures**: Always handle agent errors

## Variations

### Quick Agent Selection
For well-known task-agent mappings, select immediately

### Interactive Selection
Let user choose from top agent candidates

### Learning Selection
Track successful agent uses for future optimization

## Related Patterns
- [Handler Selection](handler-selection.md) - Choosing handlers
- [Tool Selection](tool-selection.md) - Selecting tools
- [Work Patterns](../work-tracking/work-patterns.md) - Work organization

## Agent Directory Reference
For available agents, see: `.claude/agents/`

Common agents:
- template-migrator: Template system migration
- pattern-extractor: Pattern identification
- performance-analyzer: Performance analysis
- security-validator: Security checks
- test-generator: Test creation