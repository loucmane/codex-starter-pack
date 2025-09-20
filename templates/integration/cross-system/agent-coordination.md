---
id: agent-coordination
type: integration-guide
category: cross-system
title: Multi-Agent Coordination Patterns
audience: architect
complexity: advanced
dependencies:
  - adding-agents
  - system-integration
prerequisites:
  - Deep understanding of agent system
  - Knowledge of coordination patterns
  - Familiarity with state management
version: 1.0.0
status: stable
---

# Multi-Agent Coordination Patterns

## Overview

This guide covers coordination patterns for multi-agent systems, including delegation strategies, communication protocols, state management, and conflict resolution.

## Prerequisites

- Deep understanding of the agent system architecture
- Knowledge of individual agent capabilities
- Familiarity with async coordination patterns
- Understanding of state management principles

## Coordination Architecture

### Agent Hierarchy

```
         Agent Coordinator
              │
    ┌─────────┼─────────┐
    │         │         │
Orchestrator  Meta    Router
    │       Agent      Agent
    │         │         │
┌───┼───┐    │    ┌───┼───┐
│   │   │    │    │   │   │
S1  S2  S3   │    T1  T2  T3
        Specialists  Triggers
```

### Communication Patterns

```markdown
## Pattern Types

### 1. Hub and Spoke
Coordinator acts as central hub
- All communication through coordinator
- Simplified routing
- Single point of failure

### 2. Mesh Network
Agents communicate directly
- Peer-to-peer communication
- Complex routing
- Resilient to failures

### 3. Pipeline
Sequential agent processing
- Output feeds next input
- Clear data flow
- Limited parallelism
```

## Coordination Patterns

### Pattern 1: Task Decomposition

```markdown
#### Decomposition Strategy
**Process**:
1. Coordinator receives complex task
2. Analyzes task requirements
3. Decomposes into subtasks
4. Maps subtasks to agents
5. Delegates with dependencies

**Example**:
Task: "Refactor authentication system"
Decomposition:
- Analyzer: Assess current implementation
- Designer: Create new architecture
- Implementer: Code changes
- Tester: Validate changes
- Documenter: Update docs
```

### Pattern 2: Parallel Execution

```markdown
#### Parallel Coordination
**Process**:
1. Identify independent subtasks
2. Assign to multiple agents
3. Execute simultaneously
4. Synchronize results
5. Merge outputs

**Example**:
```yaml
parallel_tasks:
  - agent: code-analyzer
    task: analyze_complexity
  - agent: security-scanner
    task: find_vulnerabilities
  - agent: performance-profiler
    task: measure_performance
sync_point: all_complete
merge_strategy: aggregate_reports
```
```

### Pattern 3: Consensus Building

```markdown
#### Consensus Protocol
**Process**:
1. Multiple agents analyze same input
2. Each provides recommendation
3. Coordinator evaluates consensus
4. Resolves conflicts
5. Makes final decision

**Example**:
Question: "Best approach for API design?"
Agents:
- REST Expert: "Use RESTful design"
- GraphQL Expert: "Use GraphQL"
- gRPC Expert: "Use gRPC"
Consensus: Weighted voting based on context
```

## State Management

### Shared State Model

```yaml
shared_state:
  task_id: unique-identifier
  status: in_progress
  agents:
    - id: agent-1
      status: working
      progress: 60
    - id: agent-2
      status: complete
      result: success
  dependencies:
    - agent-2 requires agent-1
  checkpoints:
    - timestamp: ISO-8601
      state: snapshot
```

### State Synchronization

```markdown
## Sync Strategies

### 1. Pessimistic Locking
- Agent locks state before modification
- Other agents wait
- Prevents conflicts
- Can cause deadlocks

### 2. Optimistic Concurrency
- Agents work on copies
- Detect conflicts on commit
- Resolve through merge
- Better performance

### 3. Event Sourcing
- State as sequence of events
- Agents publish events
- Rebuild state from events
- Full audit trail
```

## Communication Protocols

### Message Format

```yaml
message:
  id: msg-uuid
  from: sender-agent-id
  to: receiver-agent-id
  type: request|response|event
  timestamp: ISO-8601
  correlation_id: original-request-id
  payload:
    task: task-description
    context: relevant-context
    constraints: execution-constraints
  metadata:
    priority: high|medium|low
    timeout: seconds
    retry_count: number
```

### Protocol Types

```markdown
## Request-Response
**Flow**:
1. Agent A sends request to Agent B
2. Agent B processes request
3. Agent B sends response to Agent A
4. Agent A continues with response

## Publish-Subscribe
**Flow**:
1. Agent publishes event
2. Subscribed agents receive event
3. Each processes independently
4. No direct response required

## Streaming
**Flow**:
1. Agent starts streaming data
2. Receivers process stream
3. Continuous until complete
4. Supports backpressure
```

## Conflict Resolution

### Conflict Types

```markdown
## Resource Conflicts
- Multiple agents need same file
- Solution: Queuing or time-sharing

## Decision Conflicts
- Agents disagree on approach
- Solution: Voting or hierarchy

## Timing Conflicts
- Dependencies not met in time
- Solution: Timeout and fallback

## Data Conflicts
- Concurrent modifications
- Solution: Merge strategies
```

### Resolution Strategies

```markdown
#### Strategy: Priority-Based
**Process**:
1. Assign priority to each agent
2. Higher priority wins conflicts
3. Lower priority retries or aborts

#### Strategy: Voting
**Process**:
1. Each agent votes on decision
2. Majority wins
3. Ties broken by coordinator

#### Strategy: Merge
**Process**:
1. Detect conflicting changes
2. Apply merge algorithm
3. Manual resolution if needed
```

## Error Handling

### Failure Modes

```markdown
## Agent Failures

### 1. Timeout
- Agent doesn't respond in time
- Action: Retry or reassign

### 2. Error Response
- Agent returns error
- Action: Fallback or escalate

### 3. Crash
- Agent becomes unavailable
- Action: Circuit breaker pattern

### 4. Invalid Output
- Agent returns bad data
- Action: Validation and retry
```

### Recovery Patterns

```markdown
#### Pattern: Supervisor
**Implementation**:
1. Supervisor monitors agents
2. Detects failures
3. Restarts failed agents
4. Maintains system stability

#### Pattern: Bulkhead
**Implementation**:
1. Isolate agent failures
2. Prevent cascade failures
3. Continue with reduced capacity
4. Graceful degradation
```

## Performance Optimization

### Load Balancing

```yaml
load_balancing:
  strategy: round_robin|least_loaded|random
  metrics:
    - current_load
    - response_time
    - error_rate
  rebalance_interval: 60
```

### Caching

```markdown
## Cache Levels

### 1. Agent-Level Cache
- Each agent caches its results
- No sharing between agents
- Simple but redundant

### 2. Shared Cache
- Central cache for all agents
- Reduces redundant work
- Requires coordination

### 3. Hierarchical Cache
- Multiple cache levels
- Local and shared caches
- Optimal performance
```

## Monitoring and Observability

### Metrics

```yaml
coordination_metrics:
  - task_completion_time
  - agent_utilization
  - message_throughput
  - error_rate
  - conflict_rate
  - cache_hit_ratio
```

### Tracing

```markdown
## Distributed Tracing

### Trace Structure
```yaml
trace:
  id: trace-uuid
  spans:
    - id: span-1
      agent: coordinator
      operation: task_decomposition
      duration: 100ms
    - id: span-2
      agent: analyzer
      operation: code_analysis
      parent: span-1
      duration: 500ms
```

### Correlation
- Track requests across agents
- Identify bottlenecks
- Debug failures
```

## Examples

### Example: Complex Refactoring

```markdown
## Coordination Flow

1. **Coordinator** receives refactoring request
2. **Decomposition**:
   - Analyzer: Identify affected code
   - Designer: Plan refactoring
   - Implementer: Make changes
   - Tester: Validate changes

3. **Execution**:
   ```yaml
   phase_1: # Analysis (parallel)
     - code-analyzer
     - dependency-analyzer
   phase_2: # Design (sequential)
     - architecture-designer
   phase_3: # Implementation (parallel)
     - code-refactorer
     - test-updater
   phase_4: # Validation (sequential)
     - test-runner
     - quality-checker
   ```

4. **Synchronization**:
   - Wait for all phase agents
   - Merge results
   - Proceed to next phase

5. **Completion**:
   - Aggregate all results
   - Generate report
   - Clean up resources
```

### Example: Multi-Agent Analysis

```markdown
## Parallel Analysis Pattern

Task: "Analyze project health"

Agents:
1. **Code Quality**: Check style, complexity
2. **Security**: Scan vulnerabilities
3. **Performance**: Profile bottlenecks
4. **Documentation**: Assess coverage
5. **Testing**: Measure test quality

Coordination:
- All agents run in parallel
- 30-second timeout per agent
- Partial results acceptable
- Aggregate into health score
```

## Best Practices

### DO:
- ✅ Design for failure from the start
- ✅ Use idempotent operations
- ✅ Implement proper timeout handling
- ✅ Monitor agent health continuously
- ✅ Version agent interfaces
- ✅ Document coordination requirements

### DON'T:
- ❌ Assume agents always succeed
- ❌ Create tight coupling between agents
- ❌ Ignore resource constraints
- ❌ Skip conflict resolution
- ❌ Forget about observability
- ❌ Over-coordinate simple tasks

## Common Pitfalls

### Coordination Overhead
**Problem**: Coordination costs more than execution
**Solution**: Balance coordination with task complexity

### Deadlocks
**Problem**: Circular dependencies between agents
**Solution**: Detect and break deadlocks

### Message Storms
**Problem**: Excessive inter-agent communication
**Solution**: Batch messages, use caching

### State Inconsistency
**Problem**: Agents have different state views
**Solution**: Strong consistency guarantees

## Related Resources

- [Adding Agents](../guides/adding-agents.md)
- [System Integration](../guides/system-integration.md)
- [System Architecture](../architecture/system-architecture.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- Agent Coordinator implementation in `.claude/agents/`