---
id: pattern-composition
type: integration-guide
category: composition
title: Combining Patterns for Complex Behaviors
audience: architect
complexity: advanced
dependencies:
  - workflow-composition
  - handler-chaining
prerequisites:
  - Deep understanding of patterns
  - Knowledge of system architecture
  - Familiarity with composition principles
version: 1.0.0
status: stable
---

# Combining Patterns for Complex Behaviors

## Overview

This guide covers how to combine multiple patterns to create sophisticated behaviors, including pattern layering, emergent behaviors, and complex system interactions.

## Prerequisites

- Deep understanding of individual patterns
- Knowledge of system architecture principles
- Familiarity with composition and decomposition
- Understanding of emergent behaviors

## Pattern Categories

### Foundational Patterns

```yaml
foundational_patterns:
  - sequential: Step-by-step execution
  - parallel: Concurrent execution
  - conditional: Decision-based flow
  - loop: Iterative processing
  - pipeline: Data transformation chain
```

### Structural Patterns

```yaml
structural_patterns:
  - hierarchy: Tree-like organization
  - mesh: Interconnected network
  - layer: Abstraction levels
  - partition: Domain separation
  - bridge: System connection
```

### Behavioral Patterns

```yaml
behavioral_patterns:
  - observer: Event notification
  - strategy: Algorithm selection
  - state: Context-based behavior
  - command: Action encapsulation
  - mediator: Interaction coordination
```

## Pattern Composition Techniques

### Technique 1: Layered Composition

```markdown
## Layered Pattern Stack

┌─────────────────────────┐
│   Orchestration Layer   │ (Workflow patterns)
├─────────────────────────┤
│    Behavioral Layer     │ (Strategy, State)
├─────────────────────────┤
│    Structural Layer     │ (Hierarchy, Mesh)
├─────────────────────────┤
│   Foundational Layer    │ (Sequential, Parallel)
└─────────────────────────┘

**Implementation**:
```yaml
composition: layered-system
layers:
  - foundation:
      patterns: [sequential, parallel]
      purpose: Basic execution flow
  - structure:
      patterns: [hierarchy, partition]
      purpose: Organize components
  - behavior:
      patterns: [strategy, observer]
      purpose: Dynamic behavior
  - orchestration:
      patterns: [workflow, saga]
      purpose: High-level coordination
```
```

### Technique 2: Nested Composition

```markdown
## Pattern Within Pattern

**Example: Parallel Pipelines with Conditional Routing**

```yaml
composition: nested-patterns
outer: parallel
inner:
  - branch_1:
      pattern: pipeline
      steps:
        - conditional:
            if: data.type == "A"
            then: process_a
            else: process_default
  - branch_2:
      pattern: loop
      iterator: sequential
      condition: not_complete
```

Each parallel branch contains different patterns.
```

### Technique 3: Hybrid Composition

```markdown
## Mixed Pattern Integration

**Combine different pattern types for complex behavior**:

```yaml
composition: hybrid-processor
patterns:
  - structural: hierarchy
    behavioral: strategy
    usage: Select processing strategy based on hierarchy level
  
  - structural: partition
    behavioral: mediator
    usage: Mediate between partitioned domains
  
  - foundational: pipeline
    behavioral: state
    usage: Stateful pipeline processing
```
```

## Complex Pattern Combinations

### Saga Pattern with Compensation

```yaml
pattern: distributed-saga
combines:
  - sequential: Transaction steps
  - state: Track saga state
  - command: Encapsulate actions
  - compensation: Rollback on failure

implementation:
  steps:
    - id: reserve_inventory
      action: reserve_items
      compensation: release_items
    
    - id: charge_payment
      action: charge_card
      compensation: refund_payment
      depends_on: reserve_inventory
    
    - id: fulfill_order
      action: ship_items
      compensation: cancel_shipment
      depends_on: charge_payment
  
  on_failure:
    execute_compensations: reverse_order
    notify: failure_handler
```

### Circuit Breaker with Retry

```yaml
pattern: resilient-caller
combines:
  - circuit_breaker: Prevent cascading failures
  - retry: Attempt recovery
  - fallback: Alternative path
  - timeout: Bound execution time

implementation:
  circuit_breaker:
    failure_threshold: 5
    timeout: 30s
    half_open_attempts: 3
  
  retry:
    max_attempts: 3
    backoff: exponential
    base_delay: 1s
  
  fallback:
    strategy: cache|default|alternative_service
  
  timeout:
    operation: 5s
    total: 15s
```

### Event-Driven Orchestration

```yaml
pattern: event-orchestration
combines:
  - observer: Event detection
  - mediator: Event routing
  - strategy: Handler selection
  - state: Workflow state

implementation:
  event_bus:
    topics:
      - user_actions
      - system_events
      - external_triggers
  
  orchestrator:
    listens_to: all_topics
    state_machine:
      states: [idle, processing, waiting, complete]
    strategies:
      - quick_response
      - batch_processing
      - async_handling
  
  handlers:
    - pattern: user_action_handler
      strategy: quick_response
      events: [click, submit, navigate]
    
    - pattern: system_event_handler
      strategy: batch_processing
      events: [log, metric, trace]
```

## Emergent Behaviors

### Self-Organizing Systems

```markdown
## Pattern: Self-Organization

Combining patterns to create emergent behavior:

```yaml
emergent: auto-scaling-system
patterns:
  - observer: Monitor load
  - strategy: Scaling algorithm
  - state: System capacity
  - mediator: Resource coordination

behavior:
  - Low load → Scale down
  - High load → Scale up
  - Failure → Self-heal
  - Pattern detected → Predictive scale
```

No explicit rules for complex scenarios, behavior emerges from pattern interaction.
```

### Adaptive Systems

```markdown
## Pattern: Adaptive Behavior

```yaml
adaptive: learning-optimizer
patterns:
  - observer: Performance monitoring
  - strategy: Optimization strategies
  - state: Historical performance
  - command: Optimization actions

adaptation:
  - Track success rates
  - Adjust strategy weights
  - Learn from failures
  - Evolve over time
```

System improves through pattern feedback loops.
```

## Pattern Interaction Models

### Cooperative Patterns

```yaml
cooperation: synergistic
patterns:
  - cache: Store results
  - pipeline: Process data
interaction:
  - Pipeline checks cache first
  - Cache populated by pipeline
  - Mutual performance benefit
```

### Competitive Patterns

```yaml
competition: resource-contention
patterns:
  - parallel: Multiple workers
  - throttle: Rate limiting
interaction:
  - Workers compete for resources
  - Throttle constrains workers
  - Balance throughput vs resource use
```

### Complementary Patterns

```yaml
complementary: enhanced-capability
patterns:
  - retry: Handle transient failures
  - circuit-breaker: Handle persistent failures
interaction:
  - Retry for temporary issues
  - Circuit breaker for systemic issues
  - Together provide comprehensive resilience
```

## Advanced Composition Examples

### Example: Microservice Orchestration

```yaml
composition: microservice-orchestrator
patterns:
  foundation:
    - async: Non-blocking calls
    - parallel: Concurrent service calls
  
  structural:
    - hierarchy: Service dependencies
    - partition: Domain boundaries
  
  behavioral:
    - saga: Distributed transactions
    - circuit-breaker: Fault tolerance
    - retry: Transient failure handling
  
  orchestration:
    - workflow: Business process
    - compensation: Rollback logic

implementation:
  workflow:
    - validate_request
    - parallel:
        - check_inventory
        - check_credit
        - check_shipping
    - if all_checks_pass:
        - saga:
            - reserve_inventory
            - charge_payment
            - create_shipment
        - notify_customer
    - else:
        - return_error
```

### Example: Data Processing Pipeline

```yaml
composition: etl-pipeline
patterns:
  - pipeline: Main flow
  - parallel: Concurrent processing
  - batch: Group processing
  - retry: Error recovery
  - checkpoint: State preservation

implementation:
  stages:
    - extract:
        pattern: parallel
        sources: [database, api, files]
        error_handling: retry_with_backoff
    
    - transform:
        pattern: pipeline
        steps:
          - clean: Remove invalid data
          - enrich: Add computed fields
          - validate: Check constraints
        batch_size: 1000
        checkpoint_interval: 5000
    
    - load:
        pattern: batch
        destination: data_warehouse
        conflict_resolution: upsert
        error_handling:
          pattern: circuit_breaker
          fallback: dead_letter_queue
```

### Example: Adaptive Rate Limiter

```yaml
composition: adaptive-rate-limiter
patterns:
  - token-bucket: Rate limiting
  - observer: Load monitoring
  - strategy: Adaptation algorithm
  - state: Historical metrics

dynamic_behavior:
  - Monitor system load
  - Adjust token rate based on:
    - Current load
    - Time of day
    - Historical patterns
    - Error rates
  - Strategies:
    - conservative: Low error tolerance
    - aggressive: Max throughput
    - balanced: Optimal trade-off
  - Learning:
    - Track strategy success
    - Adjust strategy selection
    - Improve over time
```

## Testing Composite Patterns

### Unit Testing

```yaml
test: pattern-isolation
approach:
  - Test each pattern independently
  - Mock pattern interactions
  - Verify pattern contracts
```

### Integration Testing

```yaml
test: pattern-interaction
approach:
  - Test pattern combinations
  - Verify emergent behavior
  - Check interference
```

### System Testing

```yaml
test: full-composition
approach:
  - Test complete system
  - Stress test interactions
  - Verify resilience
```

## Best Practices

### DO:
- ✅ Start simple, add complexity gradually
- ✅ Document pattern interactions clearly
- ✅ Test emergent behaviors thoroughly
- ✅ Monitor pattern performance
- ✅ Design for pattern evolution
- ✅ Consider failure modes

### DON'T:
- ❌ Over-engineer with too many patterns
- ❌ Create circular dependencies
- ❌ Ignore pattern conflicts
- ❌ Skip interaction testing
- ❌ Forget about debugging complexity
- ❌ Mix incompatible patterns

## Common Pitfalls

### Pattern Explosion
**Problem**: Too many patterns make system incomprehensible
**Solution**: Limit patterns, document thoroughly

### Hidden Dependencies
**Problem**: Patterns interact in unexpected ways
**Solution**: Explicit interaction contracts

### Performance Degradation
**Problem**: Pattern overhead accumulates
**Solution**: Profile and optimize critical paths

### Debugging Difficulty
**Problem**: Hard to trace through pattern layers
**Solution**: Comprehensive logging and tracing

## Pattern Evolution

### Refactoring Patterns

```markdown
## Evolution Strategies

1. **Pattern Extraction**
   - Identify repeated compositions
   - Extract as new pattern
   - Reuse across system

2. **Pattern Merger**
   - Combine related patterns
   - Simplify interactions
   - Reduce complexity

3. **Pattern Split**
   - Break complex patterns
   - Increase modularity
   - Improve testability
```

## Related Resources

- [Workflow Composition](workflow-composition.md)
- [Handler Chaining](handler-chaining.md)
- [System Architecture](../architecture/system-architecture.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- [Best Practices](../best-practices/integration-patterns.md)