---
id: cross-system-integration-patterns
type: pattern
category: integration
title: Cross-System Integration Patterns
pattern_type: structural
complexity: complex
dependencies:
  - patterns/selection/tool-selection.md
  - patterns/selection/agent-selection.md
related:
  - patterns/integration/composition.md
version: 1.0.0
status: stable
---

# Cross-System Integration Patterns

## Pattern Description
Patterns for integrating different systems, tools, and components to work together effectively. These patterns ensure smooth interoperation between diverse system parts.

## Pattern Structure
1. Identify integration points
2. Define interfaces
3. Establish protocols
4. Implement adapters
5. Handle data transformation
6. Manage error propagation

## When to Use
- Connecting different tools
- Integrating external services
- Bridging system components
- Coordinating subsystems
- Enabling interoperability

## When NOT to Use
- Single system operations
- Isolated components
- No external dependencies
- Simple direct calls

## Integration Types

### Tool Integration
Connecting different tools:
```markdown
## Tool Chain Integration
Pipeline: Grep → Process → Write
1. Grep finds patterns
2. Process transforms data
3. Write saves results

Interface: Standardized data format
Protocol: Sequential execution
Error handling: Fail fast
```

### Service Integration
External service connections:
```markdown
## API Integration
Service: Authentication API
Integration points:
- Login endpoint
- Token validation
- Refresh mechanism
- Logout endpoint

Protocol: REST/JSON
Auth: Bearer tokens
Retry: 3 attempts
Timeout: 30 seconds
```

### System Integration
Component interconnection:
```markdown
## System Components
Frontend ←→ API ←→ Database
    ↓        ↓        ↓
  Cache   Queue   Storage

Protocols:
- HTTP/REST
- WebSocket
- Message Queue
- File System
```

## Integration Patterns

### Adapter Pattern
Bridge incompatible interfaces:
```javascript
class ToolAdapter {
  constructor(tool) {
    this.tool = tool;
  }
  
  // Adapt tool interface to standard
  execute(input) {
    const toolInput = this.transformInput(input);
    const result = this.tool.run(toolInput);
    return this.transformOutput(result);
  }
}
```

### Pipeline Pattern
Sequential processing chain:
```markdown
## Processing Pipeline
Input → Validate → Transform → Process → Output
   ↓        ↓          ↓          ↓        ↓
 Error   Error      Error      Error    Success

Each stage:
- Independent
- Composable
- Error handling
- Pass-through
```

### Hub Pattern
Central integration point:
```markdown
## Integration Hub
       Tools
         ↓
    [Hub/Router]
    ↙    ↓    ↘
Agent  System  Storage

Hub responsibilities:
- Route requests
- Transform data
- Handle errors
- Log operations
```

### Event-Driven Pattern
Loose coupling via events:
```markdown
## Event Integration
Publisher → Event Bus → Subscribers
   Auth    →  Events  → [Logger, Audit, Alert]

Events:
- user.login
- user.logout
- token.refresh
- auth.failed
```

## Data Transformation Patterns

### Format Conversion
Transform between formats:
```markdown
## Format Transformation
JSON → XML: API to legacy system
CSV → JSON: Import to API
Markdown → HTML: Docs to web
YAML → JSON: Config to runtime
```

### Schema Mapping
Map between schemas:
```javascript
// Map internal to external schema
function mapUserSchema(internal) {
  return {
    id: internal.userId,
    name: `${internal.firstName} ${internal.lastName}`,
    email: internal.emailAddress,
    created: internal.createdAt.toISOString()
  };
}
```

### Protocol Translation
Bridge different protocols:
```markdown
## Protocol Bridge
REST client → GraphQL server
1. Receive REST request
2. Build GraphQL query
3. Execute query
4. Transform response
5. Return REST response
```

## Error Handling Patterns

### Error Propagation
Pass errors through systems:
```markdown
## Error Chain
Service A → Service B → Service C
   ↓           ↓           ↓
Error 500 ← Error 503 ← Timeout

Propagation rules:
- Preserve original error
- Add context at each level
- Map to appropriate codes
- Include recovery hints
```

### Circuit Breaker
Prevent cascade failures:
```javascript
class CircuitBreaker {
  constructor(threshold = 5) {
    this.failures = 0;
    this.threshold = threshold;
    this.state = 'CLOSED';
  }
  
  async call(fn) {
    if (this.state === 'OPEN') {
      throw new Error('Circuit breaker open');
    }
    
    try {
      const result = await fn();
      this.reset();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }
}
```

### Retry Pattern
Handle transient failures:
```markdown
## Retry Strategy
Attempts: 3
Backoff: Exponential
Delays: [1s, 2s, 4s]
Conditions:
- Network errors
- 503 Service Unavailable
- Timeout errors
Not retry:
- 401 Unauthorized
- 404 Not Found
- 400 Bad Request
```

## Communication Patterns

### Synchronous Integration
Direct request-response:
```markdown
## Sync Communication
Client → Request → Server
   ↑                  ↓
   ← Response ←────────

Characteristics:
- Blocking
- Immediate response
- Simple flow
- Tight coupling
```

### Asynchronous Integration
Decoupled communication:
```markdown
## Async Communication
Client → Queue → Worker
   ↓              ↓
Ticket         Process
   ↓              ↓
Poll ←──────── Complete

Characteristics:
- Non-blocking
- Eventual response
- Complex flow
- Loose coupling
```

### Streaming Integration
Continuous data flow:
```markdown
## Stream Processing
Source → Stream → Processor → Sink
  Logs → Kafka → Analytics → Database

Characteristics:
- Continuous
- Real-time
- High volume
- Buffered
```

## Integration Testing Patterns

### Contract Testing
Verify interfaces:
```markdown
## Interface Contract
Endpoint: POST /api/users
Request:
  - email: string, required
  - password: string, min 8 chars
Response:
  - id: number
  - email: string
  - created: ISO date
```

### Integration Tests
End-to-end verification:
```markdown
## Integration Test
1. Start services
2. Initialize state
3. Execute workflow
4. Verify results
5. Check side effects
6. Clean up
```

### Mock Integration
Test with mocks:
```javascript
// Mock external service
const mockAuthService = {
  authenticate: jest.fn().mockResolvedValue({
    token: 'mock-token',
    user: { id: 1, email: 'test@example.com' }
  })
};
```

## Common Integration Scenarios

### Database Integration
```markdown
## Database Connection
Application → ORM → Database
          ↓
    Connection Pool
          ↓
      Transactions

Patterns:
- Connection pooling
- Transaction management
- Query optimization
- Cache integration
```

### API Integration
```markdown
## External API
Client → Gateway → External API
   ↓        ↓           ↓
Cache    Rate Limit   Response
   ↓        ↓           ↓
Result ← Transform ← Validate
```

### File System Integration
```markdown
## File Operations
App → File Handler → File System
 ↓         ↓             ↓
Read    Process       Storage
 ↓         ↓             ↓
Parse   Transform      Write
```

### Time Capture Pattern
Special integration for timestamps:
```markdown
## Time Integration
Never type timestamps manually!

Correct approach:
1. Execute: date "+%Y-%m-%d %H:%M %Z"
2. Capture output
3. Use in documents/logs
4. Never hardcode

Example:
- Wrong: "2025-01-15 10:00" (typed)
- Right: `date` → "2025-01-15 10:00 CEST"
```

### File Operation Patterns
Integration between file operations:
```markdown
## File Creation Pattern
Check conventions → Create structure → Write content
                ↓                ↓              ↓
         Naming rules      Directory      Use Write tool

## File Editing Pattern
Read file → Verify content → Apply edits → Save
      ↓            ↓              ↓          ↓
  Read tool   Check rules    Edit tool   Validate
```

## Anti-Patterns to Avoid

1. **Tight coupling**: Use interfaces and adapters
2. **No error handling**: Always handle failures
3. **Synchronous everything**: Use async where appropriate
4. **No timeouts**: Always set timeouts
5. **Hardcoded endpoints**: Use configuration

## Examples

### Good Integration
```markdown
## Tool Integration Example
Task: Search and process files

Integration:
1. Glob finds files
2. Grep searches content
3. Process transforms data
4. Write saves results

Error handling:
- Each step validates input
- Errors logged with context
- Graceful degradation
- Recovery possible
```

### Poor Integration
```markdown
Just call the API and hope it works.
No error handling needed.
Hardcode the endpoints.
```

## Related Patterns
- [Composition](composition.md) - Pattern composition
- [Tool Selection](../selection/tool-selection.md) - Tool choice
- [Agent Selection](../selection/agent-selection.md) - Agent coordination

## Handler References
[Handler: file-operation migrated to handlers/operators/file/file-operator.md]
[Handler: file-creation migrated to handlers/operators/file/file-creator.md]
[Handler: time-capture migrated to handlers/operators/utility/time-capturer.md]