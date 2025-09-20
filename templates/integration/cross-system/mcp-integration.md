---
id: mcp-integration
type: integration-guide
category: cross-system
title: MCP Tool Integration
audience: developer
complexity: advanced
dependencies:
  - tool-integration
  - system-integration
prerequisites:
  - Understanding of MCP protocol
  - Knowledge of tool interfaces
  - Familiarity with async operations
version: 1.0.0
status: beta
---

# MCP Tool Integration

## Overview

This guide covers integrating Model Context Protocol (MCP) tools into the Claude Template System, enabling seamless interaction between Claude and external tools through the MCP standard.

## Prerequisites

- Understanding of MCP protocol basics
- Knowledge of tool interfaces and contracts
- Familiarity with async operations and callbacks
- Understanding of the template system's tool layer

## MCP Architecture Overview

### Protocol Layers

```
┌─────────────────────────┐
│  Claude Template System  │
├─────────────────────────┤
│    MCP Integration Layer │
├─────────────────────────┤
│      MCP Protocol        │
├─────────────────────────┤
│     External Tools       │
└─────────────────────────┘
```

### Communication Flow

```
Handler → MCP Adapter → MCP Server → Tool → Response
```

## MCP Tool Categories

### 1. Data Access Tools

```yaml
category: data-access
tools:
  - database-query
  - api-fetch
  - file-system
  - cache-access
integration:
  - Async operations required
  - Result streaming supported
  - Error handling critical
```

### 2. Computation Tools

```yaml
category: computation
tools:
  - code-execution
  - data-processing
  - ml-inference
  - optimization
integration:
  - Resource limits enforced
  - Timeout handling required
  - Progress tracking needed
```

### 3. External Service Tools

```yaml
category: external-services
tools:
  - email-sender
  - notification-service
  - deployment-trigger
  - monitoring-alert
integration:
  - Authentication required
  - Rate limiting enforced
  - Retry logic needed
```

## Integration Implementation

### Step 1: Define MCP Tool Interface

```typescript
// Conceptual MCP tool interface
interface MCPTool {
  id: string;
  name: string;
  version: string;
  capabilities: Capability[];
  
  // MCP methods
  initialize(): Promise<void>;
  execute(params: any): Promise<any>;
  cleanup(): Promise<void>;
  
  // Metadata
  getSchema(): ToolSchema;
  validateParams(params: any): ValidationResult;
}
```

### Step 2: Create Tool Adapter

```markdown
#### Handler: mcp-tool-adapter
**Purpose**: Bridge between template system and MCP tools
**Process**:
1. Receive tool invocation request
2. Validate parameters against schema
3. Initialize MCP connection
4. Execute tool via MCP
5. Process response
6. Handle errors/timeouts
7. Return formatted result
```

### Step 3: Implement Tool Handlers

```markdown
---
id: execute-mcp-tool
name: Execute MCP Tool
role: operator
domain: cross-system
tools: ["MCP"]
---

#### Handler: execute-mcp-tool
**Triggers**: "use MCP tool", "execute external tool"
**Target Pattern**: Tool name and parameters
**Pre-conditions**:
- MCP server available
- Tool registered
- Parameters valid
**Process**:
1. Parse tool request
2. Load tool schema
3. Validate parameters
4. Initialize MCP connection
5. Execute tool
6. Process response
7. Format for template system
**Success**: Tool executes, returns result
**Failure**: Clear error with recovery options
```

## MCP Tool Registration

### Registration Format

```yaml
# .claude/mcp-tools/tool-registry.yaml
tools:
  - id: database-query
    name: Database Query Tool
    version: 1.0.0
    server: mcp://localhost:8080
    capabilities:
      - sql-query
      - schema-inspect
      - transaction
    schema:
      input:
        query: string
        database: string
        timeout: number
      output:
        results: array
        metadata: object
```

### Dynamic Registration

```markdown
#### Handler: register-mcp-tool
**Process**:
1. Validate tool manifest
2. Test MCP connection
3. Verify capabilities
4. Add to registry
5. Create tool handlers
6. Update documentation
```

## Error Handling

### MCP-Specific Errors

```markdown
## Error Types

### Connection Errors
- MCP server unreachable
- Authentication failed
- Protocol version mismatch

### Execution Errors
- Tool not found
- Invalid parameters
- Timeout exceeded
- Resource limit hit

### Response Errors
- Malformed response
- Partial response
- Encoding issues
```

### Error Recovery Patterns

```markdown
#### Pattern: Retry with Backoff
**Process**:
1. Initial attempt fails
2. Wait 1 second
3. Retry (max 3 times)
4. Double wait time each retry
5. Fall back to alternative

#### Pattern: Circuit Breaker
**Process**:
1. Track failure rate
2. If > 50% failures in 10 attempts
3. Open circuit (skip tool)
4. Try again after cooldown
5. Reset if successful
```

## Security Considerations

### Authentication

```yaml
auth_methods:
  - api_key:
      location: header
      name: X-MCP-API-Key
  - oauth:
      flow: client_credentials
      token_url: /oauth/token
  - mtls:
      cert_required: true
      verify_mode: CERT_REQUIRED
```

### Authorization

```markdown
## Tool Permissions

### Read-Only Tools
- Can access data
- Cannot modify state
- No side effects

### Write Tools
- Can modify data
- Require confirmation
- Audit logging enabled

### Admin Tools
- Full system access
- Require explicit approval
- Detailed logging
```

## Performance Optimization

### Connection Pooling

```yaml
connection_pool:
  min_size: 2
  max_size: 10
  timeout: 30
  idle_timeout: 300
  validation_interval: 60
```

### Caching Strategy

```markdown
## Cache Levels

1. **Response Cache**
   - Cache tool responses
   - TTL based on tool type
   - Invalidate on write operations

2. **Schema Cache**
   - Cache tool schemas
   - Refresh daily
   - Version-aware

3. **Connection Cache**
   - Reuse MCP connections
   - Keep-alive enabled
   - Auto-reconnect
```

## Monitoring and Observability

### Metrics to Track

```yaml
metrics:
  - tool_invocations:
      type: counter
      labels: [tool_id, status]
  - execution_time:
      type: histogram
      labels: [tool_id]
  - error_rate:
      type: gauge
      labels: [tool_id, error_type]
  - connection_pool:
      type: gauge
      labels: [state]
```

### Logging Requirements

```markdown
## Log Levels

### INFO
- Tool invocation start/end
- Connection established
- Cache hits

### WARN
- Retry attempts
- Slow responses (>5s)
- Connection pool exhausted

### ERROR
- Tool failures
- Connection errors
- Invalid responses

### DEBUG
- Full request/response
- Connection details
- Cache operations
```

## Examples

### Example: Database Query Tool

```markdown
#### MCP Tool: Database Query
**Configuration**:
```yaml
id: postgres-query
server: mcp://db-server:5432
credentials: ${DB_CREDENTIALS}
max_connections: 5
```

**Handler Integration**:
```markdown
#### Handler: query-user-data
**Process**:
1. Prepare SQL query
2. Invoke MCP database tool
3. Handle pagination if needed
4. Transform results
5. Return to caller
```

### Example: External API Tool

```markdown
#### MCP Tool: REST API Client
**Configuration**:
```yaml
id: api-client
server: mcp://api-gateway:8080
auth: oauth2
rate_limit: 100/minute
```

**Usage Pattern**:
```markdown
1. Request API operation
2. MCP handles auth
3. Execute API call
4. Transform response
5. Handle rate limits
```

## Testing MCP Integration

### Unit Tests

```markdown
## Test Cases

### Connection Tests
- Test successful connection
- Test auth failure
- Test timeout
- Test reconnection

### Execution Tests
- Test valid parameters
- Test invalid parameters
- Test large payloads
- Test concurrent requests

### Error Tests
- Test network failure
- Test server error
- Test malformed response
- Test resource limits
```

### Integration Tests

```markdown
## End-to-End Tests

1. **Happy Path**
   - Connect to MCP server
   - Execute tool successfully
   - Verify response
   - Check side effects

2. **Error Recovery**
   - Simulate failures
   - Verify retry logic
   - Check fallbacks
   - Validate error messages

3. **Performance**
   - Load test tools
   - Measure latency
   - Check resource usage
   - Verify scaling
```

## Common Pitfalls

### Synchronous Assumptions
**Problem**: Treating async MCP calls as synchronous
**Solution**: Proper async/await handling

### Missing Error Handling
**Problem**: Not handling MCP-specific errors
**Solution**: Comprehensive error coverage

### Resource Leaks
**Problem**: Not closing MCP connections
**Solution**: Proper cleanup in finally blocks

### Security Oversights
**Problem**: Hardcoded credentials
**Solution**: Use environment variables or secrets manager

## Related Resources

- [Tool Integration](tool-integration.md)
- [System Integration](../guides/system-integration.md)
- [Agent Coordination](agent-coordination.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- MCP Protocol Documentation (external)