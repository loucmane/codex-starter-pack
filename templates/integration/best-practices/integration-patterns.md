---
id: integration-patterns
type: integration-guide
category: best-practices
title: Integration Best Practices
audience: architect
complexity: advanced
dependencies:
  - system-integration
  - pattern-composition
prerequisites:
  - Understanding of system architecture
  - Knowledge of integration patterns
  - Experience with distributed systems
version: 1.0.0
status: stable
---

# Integration Best Practices

## Overview

This guide provides best practices for integrating components within the Claude Template System and with external systems, covering patterns, anti-patterns, and proven strategies.

## Prerequisites

- Understanding of system architecture
- Knowledge of common integration patterns
- Experience with distributed systems
- Familiarity with error handling and recovery

## Integration Principles

### 1. Loose Coupling

```markdown
## Maintain Independence

✅ **Good: Loose Coupling**
```yaml
component_a:
  interface: well-defined
  dependencies: minimal
  communication: async messages
  
component_b:
  interface: well-defined
  dependencies: minimal
  communication: async messages

integration:
  method: message_queue
  format: standardized
  coupling: loose
```

❌ **Bad: Tight Coupling**
```yaml
component_a:
  directly_calls: component_b.internal_method()
  shares: internal_state
  assumes: component_b_implementation
```

**Benefits**:
- Independent deployment
- Isolated failures
- Easier testing
- Better scalability
```

### 2. Contract-First Design

```yaml
# Define contracts before implementation
contract:
  name: user-service
  version: 1.0.0
  
  endpoints:
    - path: /users/{id}
      method: GET
      request:
        params:
          id: string
      response:
        200:
          schema:
            id: string
            name: string
            email: string
        404:
          schema:
            error: string
  
  events:
    - name: user.created
      schema:
        userId: string
        timestamp: datetime
```

### 3. Idempotency

```markdown
## Design for Idempotency

```yaml
operation: create-user
idempotency:
  key: email_address
  behavior:
    - First call: Creates user
    - Repeat calls: Returns existing user
    - No side effects on repeats
  
implementation:
  - Check if exists
  - If not, create
  - Return result
  - Same response every time
```

**Why It Matters**:
- Safe retries
- Network reliability
- Distributed consistency
- Error recovery
```

## Integration Patterns

### Request-Response Pattern

```yaml
pattern: request-response
use_when:
  - Synchronous operations
  - Immediate response needed
  - Simple queries

implementation:
  client:
    - Send request
    - Wait for response
    - Handle timeout
    - Retry if needed
  
  server:
    - Receive request
    - Process
    - Send response
    - Log transaction

best_practices:
  - Set reasonable timeouts
  - Implement circuit breakers
  - Use exponential backoff
  - Cache responses when possible
```

### Event-Driven Pattern

```yaml
pattern: event-driven
use_when:
  - Asynchronous operations
  - Multiple consumers
  - Loose coupling needed
  - Audit trail required

implementation:
  producer:
    - Generate event
    - Publish to bus
    - Fire and forget
  
  consumer:
    - Subscribe to events
    - Process asynchronously
    - Acknowledge receipt
  
  event_bus:
    - Route events
    - Ensure delivery
    - Handle failures

best_practices:
  - Use event schemas
  - Version events
  - Implement dead letter queues
  - Monitor event flow
```

### Saga Pattern

```yaml
pattern: distributed-saga
use_when:
  - Multi-step transactions
  - Distributed systems
  - Compensation needed
  - Long-running processes

implementation:
  orchestrator:
    - Coordinate steps
    - Track state
    - Handle failures
    - Execute compensation
  
  steps:
    - action: forward_action
      compensation: reverse_action
      timeout: 30s
      retry: 3
  
  compensation:
    - Reverse order execution
    - Restore original state
    - Notify stakeholders

best_practices:
  - Make steps idempotent
  - Log all transitions
  - Test compensation logic
  - Monitor saga health
```

## Error Handling Strategies

### Retry Strategies

```yaml
retry_strategies:
  exponential_backoff:
    initial_delay: 1s
    multiplier: 2
    max_delay: 60s
    max_attempts: 5
    jitter: true
  
  linear_backoff:
    delay: 5s
    max_attempts: 3
  
  circuit_breaker:
    failure_threshold: 5
    timeout: 30s
    half_open_attempts: 3
    reset_timeout: 60s
```

### Fallback Mechanisms

```markdown
## Graceful Degradation

```yaml
fallback_chain:
  primary:
    service: live-database
    timeout: 5s
  
  secondary:
    service: read-replica
    timeout: 10s
    condition: primary_failed
  
  tertiary:
    service: cache
    timeout: 1s
    condition: secondary_failed
  
  final:
    response: default-value
    condition: all_failed
```

**Implementation**:
1. Try primary service
2. On failure, try fallbacks
3. Return best available result
4. Log degradation level
```

### Error Propagation

```yaml
error_handling:
  capture:
    - Log locally
    - Add context
    - Preserve stack trace
  
  enrich:
    - Add timestamp
    - Include request ID
    - Add service info
  
  propagate:
    - Sanitize sensitive data
    - Use standard format
    - Include recovery hints
  
  respond:
    - User-friendly message
    - Technical details if debug
    - Suggested actions
```

## Performance Optimization

### Caching Strategies

```yaml
caching:
  levels:
    L1:
      type: in-memory
      size: 100MB
      ttl: 60s
      scope: process
    
    L2:
      type: redis
      size: 1GB
      ttl: 3600s
      scope: shared
    
    L3:
      type: cdn
      ttl: 86400s
      scope: global
  
  invalidation:
    strategies:
      - ttl-based
      - event-based
      - manual
  
  patterns:
    - cache-aside
    - read-through
    - write-through
    - write-behind
```

### Connection Pooling

```yaml
connection_pool:
  configuration:
    min_size: 5
    max_size: 20
    acquire_timeout: 10s
    idle_timeout: 300s
    max_lifetime: 3600s
  
  monitoring:
    - active_connections
    - waiting_requests
    - connection_errors
    - pool_exhaustion
  
  optimization:
    - Prewarming
    - Health checks
    - Automatic scaling
    - Connection reuse
```

### Batch Processing

```yaml
batching:
  configuration:
    batch_size: 100
    batch_timeout: 5s
    max_batch_size: 1000
  
  triggers:
    - size_reached
    - timeout_elapsed
    - manual_flush
  
  benefits:
    - Reduced overhead
    - Better throughput
    - Efficient resource use
  
  considerations:
    - Increased latency
    - Memory usage
    - Error handling complexity
```

## Security Best Practices

### Authentication & Authorization

```yaml
security:
  authentication:
    methods:
      - oauth2
      - api_keys
      - mtls
    
    token_management:
      - Short-lived tokens
      - Refresh tokens
      - Token rotation
  
  authorization:
    model: rbac  # or abac
    enforcement: gateway
    caching: 5m
  
  audit:
    - Log all access
    - Track changes
    - Monitor anomalies
```

### Data Protection

```yaml
data_protection:
  in_transit:
    - TLS 1.3
    - Certificate pinning
    - Mutual TLS
  
  at_rest:
    - Encryption
    - Key rotation
    - Access controls
  
  sensitive_data:
    - Masking
    - Tokenization
    - Redaction in logs
```

## Monitoring and Observability

### Key Metrics

```yaml
metrics:
  golden_signals:
    - latency:
        p50: < 100ms
        p99: < 1s
    - traffic:
        rps: current_rate
        trends: hourly/daily
    - errors:
        rate: < 0.1%
        types: categorized
    - saturation:
        cpu: < 70%
        memory: < 80%
  
  business_metrics:
    - success_rate
    - conversion_rate
    - user_satisfaction
```

### Distributed Tracing

```yaml
tracing:
  implementation:
    - Trace ID propagation
    - Span collection
    - Context preservation
  
  sampling:
    strategy: adaptive
    base_rate: 0.1
    error_rate: 1.0
  
  storage:
    retention: 7d
    indexing: trace_id, service, operation
```

### Logging Standards

```yaml
logging:
  format:
    timestamp: ISO-8601
    level: ERROR|WARN|INFO|DEBUG
    service: service-name
    trace_id: correlation-id
    message: human-readable
    context: structured-data
  
  practices:
    - Structured logging
    - Correlation IDs
    - Contextual information
    - No sensitive data
  
  aggregation:
    - Centralized logging
    - Log parsing
    - Alerting rules
```

## Testing Integration

### Integration Testing

```yaml
integration_tests:
  scope:
    - Component interfaces
    - Data flow
    - Error scenarios
    - Performance
  
  environment:
    - Isolated test env
    - Mock external services
    - Test data management
  
  strategies:
    - Contract testing
    - End-to-end testing
    - Chaos engineering
```

### Contract Testing

```yaml
contract_testing:
  provider:
    - Define contract
    - Implement endpoints
    - Verify compliance
  
  consumer:
    - Define expectations
    - Mock provider
    - Verify integration
  
  broker:
    - Store contracts
    - Version management
    - Compatibility checks
```

## Common Anti-Patterns

### Anti-Pattern: Chatty Integration

```markdown
❌ **Bad: Too Many Calls**
```yaml
# Making 100 calls to get user data
for user_id in user_ids:
  user = get_user(user_id)  # N+1 problem
```

✅ **Good: Batch Operations**
```yaml
# Single call for all users
users = get_users_batch(user_ids)
```
```

### Anti-Pattern: Distributed Monolith

```markdown
❌ **Bad: False Microservices**
- Services must deploy together
- Shared databases
- Synchronous communication only
- No service autonomy

✅ **Good: True Microservices**
- Independent deployment
- Own data stores
- Async communication
- Service autonomy
```

### Anti-Pattern: No Circuit Breaker

```markdown
❌ **Bad: Cascading Failures**
```yaml
service_a:
  calls: service_b
  timeout: 60s
  retry: unlimited
  # Service B down = Service A hangs
```

✅ **Good: Circuit Breaker**
```yaml
service_a:
  calls: service_b
  circuit_breaker:
    enabled: true
    threshold: 5 failures
    timeout: 30s
  fallback: cache_or_default
```
```

## Migration Strategies

### Strangler Fig Pattern

```yaml
migration: strangler_fig
steps:
  1:
    route: 100% to legacy
    new_system: development
  2:
    route: 10% to new
    monitor: performance
  3:
    route: 50% to new
    validate: correctness
  4:
    route: 100% to new
    legacy: standby
  5:
    decommission: legacy
```

### Blue-Green Deployment

```yaml
deployment: blue_green
process:
  - Deploy to green
  - Test green environment
  - Switch traffic to green
  - Monitor for issues
  - Keep blue as rollback
  - After stability, update blue
```

## Checklist for Integration

### Design Phase
- [ ] Contracts defined
- [ ] Error handling planned
- [ ] Security considered
- [ ] Performance targets set

### Implementation Phase
- [ ] Idempotency implemented
- [ ] Retries configured
- [ ] Circuit breakers added
- [ ] Monitoring in place

### Testing Phase
- [ ] Unit tests complete
- [ ] Integration tests passing
- [ ] Contract tests verified
- [ ] Load tests performed

### Deployment Phase
- [ ] Rollback plan ready
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Documentation updated

## Related Resources

- [System Integration](../guides/system-integration.md)
- [Pattern Composition](../composition/pattern-composition.md)
- [System Architecture](../architecture/system-architecture.md)
- [Handler Design](handler-design.md)
- [Template Design](template-design.md)