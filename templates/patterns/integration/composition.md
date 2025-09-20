---
id: pattern-composition
type: pattern
category: integration
title: Pattern Composition Strategies
pattern_type: structural
complexity: complex
dependencies:
  - patterns/routing/meta-routing.md
  - patterns/selection/handler-selection.md
related:
  - patterns/integration/cross-system.md
version: 1.0.0
status: stable
---

# Pattern Composition Strategies

## Pattern Description
Strategies for combining multiple patterns to create more complex behaviors and workflows. These patterns show how simpler patterns can be composed into sophisticated solutions.

## Pattern Structure
1. Identify component patterns
2. Define composition strategy
3. Establish interfaces
4. Coordinate execution
5. Manage dependencies
6. Handle emergent behavior

## When to Use
- Complex workflows needing multiple patterns
- Building higher-level abstractions
- Creating reusable compositions
- Orchestrating pattern interactions
- Solving multi-faceted problems

## When NOT to Use
- Simple single-pattern solutions
- Over-engineering simple tasks
- Unnecessary complexity
- Performance-critical paths

## Composition Types

### Sequential Composition
Patterns execute in order:
```markdown
## Sequential Pipeline
Pattern A → Pattern B → Pattern C → Result
   ↓           ↓           ↓
Validate    Transform    Output

Example:
1. Intent Detection → 
2. Handler Selection → 
3. Tool Selection → 
4. Execution
```

### Parallel Composition
Patterns execute simultaneously:
```markdown
## Parallel Execution
     Input
    ↙  ↓  ↘
  P1   P2   P3
    ↘  ↓  ↙
    Combine
       ↓
     Result

Example:
- Search in code (Pattern 1)
- Search in docs (Pattern 2)  } Parallel
- Search in tests (Pattern 3)
- Merge results
```

### Nested Composition
Patterns contain patterns:
```markdown
## Nested Structure
Outer Pattern {
  Setup Phase {
    Pattern A
    Pattern B
  }
  Main Phase {
    Pattern C {
      Sub-Pattern D
      Sub-Pattern E
    }
  }
  Cleanup Phase {
    Pattern F
  }
}
```

### Conditional Composition
Pattern selection based on conditions:
```markdown
## Conditional Flow
Input → Analyze
         ↓
    [Condition?]
     ↙      ↘
Pattern A  Pattern B
     ↘      ↙
      Result

Example:
If simple request → Quick Pattern
If complex request → Deep Analysis Pattern
```

## Composition Strategies

### Builder Strategy
Build complex behavior incrementally:
```javascript
class WorkflowBuilder {
  constructor() {
    this.patterns = [];
  }
  
  addPattern(pattern) {
    this.patterns.push(pattern);
    return this;
  }
  
  withValidation() {
    return this.addPattern(validationPattern);
  }
  
  withLogging() {
    return this.addPattern(loggingPattern);
  }
  
  build() {
    return new CompositePattern(this.patterns);
  }
}
```

### Decorator Strategy
Enhance patterns with additional behavior:
```markdown
## Pattern Decoration
Base: Search Pattern
+ Add: Caching decorator
+ Add: Logging decorator
+ Add: Retry decorator
= Enhanced Search Pattern

Each decorator:
- Wraps previous
- Adds behavior
- Preserves interface
```

### Chain Strategy
Link patterns in responsibility chain:
```markdown
## Responsibility Chain
Request → Handler1 → Handler2 → Handler3
            ↓          ↓          ↓
         Can't     Can't      Handles
         handle    handle        ↓
                              Response

Each handler:
- Tries to handle
- Passes if can't
- Chain continues
```

### Template Strategy
Define pattern skeleton:
```markdown
## Template Pattern
Abstract Workflow {
  1. Initialize (variable)
  2. Validate (variable)
  3. Process (fixed)
  4. Transform (variable)
  5. Output (fixed)
}

Concrete implementations:
- Override variable parts
- Inherit fixed parts
- Maintain structure
```

## Common Compositions

### ULTRATHINK Composition
Complete development workflow:
```markdown
## ULTRATHINK Composite
Components:
1. Context Detection Pattern
2. Session Management Pattern
3. Work Tracking Pattern
4. Handler Selection Pattern
5. Execution Pattern
6. State Persistence Pattern

Flow:
Detect → Initialize → Track → Select → Execute → Save
```

### Search and Process Composition
Find and transform:
```markdown
## Search-Process Composite
Components:
1. File Discovery Pattern (Glob)
2. Content Search Pattern (Grep)
3. Data Transform Pattern
4. Output Generation Pattern

Flow:
Find files → Search content → Transform → Output
```

### Development Workflow Composition
Full feature development:
```markdown
## Feature Development Composite
Components:
1. Work Initialization Pattern
2. Code Creation Pattern
3. Test Creation Pattern
4. Documentation Pattern
5. Progress Tracking Pattern

Flow:
Init → Code → Test → Document → Track
```

### Error Recovery Composition
Robust error handling:
```markdown
## Error Recovery Composite
Components:
1. Error Detection Pattern
2. Context Capture Pattern
3. Recovery Strategy Pattern
4. Retry Pattern
5. Fallback Pattern

Flow:
Detect → Capture → Recover → Retry → Fallback
```

## Dependency Management

### Dependency Graph
Track pattern dependencies:
```markdown
## Pattern Dependencies
A ─depends→ B
↓           ↓
C ←─────────┴─depends

Execution order:
1. B (no dependencies)
2. A (needs B)
3. C (needs A and B)
```

### Dependency Injection
Provide dependencies:
```javascript
class CompositePattern {
  constructor(dependencies) {
    this.auth = dependencies.authPattern;
    this.data = dependencies.dataPattern;
    this.log = dependencies.logPattern;
  }
  
  execute() {
    this.auth.validate();
    const data = this.data.fetch();
    this.log.record(data);
    return data;
  }
}
```

### Lazy Dependencies
Load only when needed:
```markdown
## Lazy Loading
Pattern starts → 
Check if Feature X needed →
  Yes: Load Pattern X
  No: Skip Pattern X
Continue execution
```

## Coordination Patterns

### Orchestrator Coordination
Central control:
```markdown
## Orchestrator Pattern
     Orchestrator
    ↙    ↓    ↘
Worker1 Worker2 Worker3
    ↘    ↓    ↙
     Results

Orchestrator:
- Controls flow
- Manages state
- Handles errors
- Combines results
```

### Choreography Coordination
Distributed control:
```markdown
## Choreography Pattern
Service A → Event → Service B
    ↓                    ↓
  Event               Event
    ↓                    ↓
Service C ← Event ← Service D

Each service:
- Knows its triggers
- Emits events
- Self-coordinating
```

### Saga Coordination
Long-running transactions:
```markdown
## Saga Pattern
Step 1 → Step 2 → Step 3 → Complete
  ↓        ↓        ↓
Compensate ← Rollback ← Error

Each step:
- Has compensation
- Can rollback
- Maintains consistency
```

## Emergent Behavior

### Synergy Patterns
Combined effect greater than parts:
```markdown
## Synergy Example
Pattern A: Fast search
Pattern B: Smart caching
Combined: Ultra-fast repeated searches

Emergent: Performance beyond individual patterns
```

### Interference Patterns
Patterns conflict:
```markdown
## Interference Example
Pattern A: Aggressive caching
Pattern B: Real-time updates
Conflict: Stale cache data

Resolution: Cache invalidation strategy
```

## Testing Compositions

### Unit Testing
Test individual patterns:
```markdown
Test each pattern in isolation:
- Pattern A: ✓ Works alone
- Pattern B: ✓ Works alone
- Pattern C: ✓ Works alone
```

### Integration Testing
Test pattern interactions:
```markdown
Test pattern combinations:
- A → B: ✓ Works together
- B → C: ✓ Works together
- A → B → C: ✓ Full flow works
```

### Composition Testing
Test emergent behavior:
```markdown
Test composite properties:
- Performance: Meets requirements
- Reliability: Handles failures
- Scalability: Grows with load
- Maintainability: Easy to modify
```

## Anti-Patterns to Avoid

1. **Over-composition**: Don't combine unnecessarily
2. **Tight coupling**: Keep patterns independent
3. **Hidden dependencies**: Make dependencies explicit
4. **Complex hierarchies**: Keep composition shallow
5. **Premature optimization**: Start simple, compose as needed

## Examples

### Good Composition
```markdown
## Well-Composed Workflow
Purpose: Process user registration

Composition:
1. Validation Pattern (input check)
2. Authentication Pattern (create account)
3. Notification Pattern (send email)
4. Logging Pattern (audit trail)

Clear interfaces between patterns
Each pattern single responsibility
Easy to modify or extend
```

### Poor Composition
```markdown
## Over-Engineered Composition
Purpose: Read a file

Unnecessary composition:
1. Permission checker pattern
2. File validator pattern
3. Read optimizer pattern
4. Cache manager pattern
5. Logger pattern
6. Metric collector pattern

Too complex for simple task!
```

## Related Patterns
- [Cross-System](cross-system.md) - System integration
- [Meta-Routing](../routing/meta-routing.md) - High-level routing
- [Handler Selection](../selection/handler-selection.md) - Handler composition

## Handler References
Composition is fundamental to the entire handler system architecture