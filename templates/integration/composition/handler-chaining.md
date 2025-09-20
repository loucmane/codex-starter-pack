---
id: handler-chaining
type: integration-guide
category: composition
title: Chaining Handlers Together
audience: developer
complexity: intermediate
dependencies:
  - creating-handlers
  - workflow-composition
prerequisites:
  - Understanding of handler system
  - Knowledge of handler roles
  - Familiarity with data flow
version: 1.0.0
status: stable
---

# Chaining Handlers Together

## Overview

This guide covers how to chain handlers together effectively, including data passing, error propagation, and maintaining handler independence while enabling cooperation.

## Prerequisites

- Understanding of handler roles (trigger/orchestrator/operator)
- Knowledge of handler inputs and outputs
- Familiarity with data transformation
- Understanding of error handling

## Handler Chain Fundamentals

### Basic Chain Structure

```
Trigger → Orchestrator → Operator → Operator → Response
   ↑                                              ↓
 Input                                         Output
```

### Data Flow Types

```markdown
## 1. Pipeline Flow
Handler A output → Handler B input → Handler C input

## 2. Fan-Out Flow
         ┌→ Handler B
Handler A ─┼→ Handler C
         └→ Handler D

## 3. Fan-In Flow
Handler A ─┐
Handler B ─┼→ Handler D
Handler C ─┘

## 4. Mesh Flow
Handlers interconnect based on needs
```

## Chain Implementation Patterns

### Pattern 1: Simple Sequential Chain

```markdown
#### Implementation: File Processing Chain

**Chain**: read-file → transform-content → validate → write-file

```yaml
chain: file-processor
handlers:
  - id: reader
    handler: read-file
    params:
      path: ${input.file_path}
    output: file_content
  
  - id: transformer
    handler: transform-content
    input: ${reader.output}
    params:
      format: ${input.target_format}
    output: transformed_content
  
  - id: validator
    handler: validate-content
    input: ${transformer.output}
    output: validation_result
  
  - id: writer
    handler: write-file
    input: ${transformer.output}
    params:
      path: ${input.output_path}
    condition: ${validator.output.is_valid}
```
```

### Pattern 2: Conditional Chain

```markdown
#### Implementation: Smart Router Chain

**Decision-based chaining**:

```yaml
chain: smart-router
handlers:
  - id: analyzer
    handler: analyze-request
    output: request_type
  
  - id: router
    conditional:
      - when: ${analyzer.output} == "code"
        handler: code-processor
      - when: ${analyzer.output} == "docs"
        handler: doc-processor
      - when: ${analyzer.output} == "test"
        handler: test-processor
      - default:
        handler: general-processor
```
```

### Pattern 3: Parallel Chain with Aggregation

```markdown
#### Implementation: Multi-Analysis Chain

**Parallel execution with result merging**:

```yaml
chain: comprehensive-analysis
handlers:
  - id: prepare
    handler: prepare-codebase
    output: prepared_code
  
  - id: parallel_analysis
    parallel:
      - handler: complexity-analyzer
        input: ${prepare.output}
        output_key: complexity
      - handler: security-scanner
        input: ${prepare.output}
        output_key: security
      - handler: performance-profiler
        input: ${prepare.output}
        output_key: performance
  
  - id: aggregator
    handler: merge-results
    input: ${parallel_analysis.outputs}
    output: comprehensive_report
```
```

## Data Transformation Between Handlers

### Transform Strategies

```markdown
## 1. Direct Pass-Through
No transformation needed:
```yaml
handler_a.output → handler_b.input
```

## 2. Field Mapping
Map output fields to input fields:
```yaml
transform:
  handler_b.input.file_path: handler_a.output.path
  handler_b.input.content: handler_a.output.data
```

## 3. Computed Transform
Derive new values:
```yaml
transform:
  handler_b.input.size: len(handler_a.output.content)
  handler_b.input.hash: sha256(handler_a.output.content)
```

## 4. Aggregation Transform
Combine multiple outputs:
```yaml
transform:
  handler_d.input.results: [
    handler_a.output,
    handler_b.output,
    handler_c.output
  ]
```
```

### Data Contracts

```yaml
# Handler output contract
handler: code-analyzer
output_contract:
  type: object
  properties:
    complexity:
      type: number
      min: 0
      max: 100
    issues:
      type: array
      items:
        type: object
        properties:
          severity: enum[low|medium|high]
          message: string
          line: number

# Handler input contract
handler: issue-fixer
input_contract:
  type: object
  required: [issues, file_path]
  properties:
    issues:
      type: array
    file_path:
      type: string
```

## Error Handling in Chains

### Error Propagation Strategies

```markdown
## 1. Fail Fast
Stop chain on first error:
```yaml
error_strategy: fail_fast
on_error: abort_chain
```

## 2. Continue with Defaults
Use default values on error:
```yaml
error_strategy: continue
on_error:
  use_default: ${handler.default_output}
  log_error: true
```

## 3. Alternative Path
Switch to fallback chain:
```yaml
error_strategy: fallback
on_error:
  switch_to: fallback_chain
  preserve_context: true
```

## 4. Partial Success
Continue with partial results:
```yaml
error_strategy: best_effort
on_error:
  mark_failed: true
  continue: true
  aggregate_errors: true
```
```

### Error Recovery Examples

```yaml
chain: resilient-processor
handlers:
  - id: primary
    handler: primary-processor
    on_error:
      retry:
        attempts: 3
        backoff: exponential
      then:
        fallback_to: backup
  
  - id: backup
    handler: backup-processor
    condition: ${primary.failed}
    on_error:
      fallback_to: manual
  
  - id: manual
    handler: manual-processor
    condition: ${backup.failed}
```

## State Management in Chains

### Chain Context

```yaml
chain_context:
  id: chain-instance-123
  started_at: "2024-01-20T10:00:00Z"
  current_handler: transformer
  state:
    user_input: original-request
    intermediate_results:
      reader: {content: "file data"}
      transformer: {status: "in_progress"}
    errors: []
    metadata:
      retry_count: 0
      execution_time: 1500
```

### State Persistence Points

```markdown
## When to Persist State

1. **Before Expensive Operations**
   - Save state before long-running handlers
   - Enable resume on failure

2. **After Critical Changes**
   - Persist after irreversible operations
   - Ensure consistency

3. **At Decision Points**
   - Save before conditional branches
   - Track path taken

4. **End of Phases**
   - Checkpoint between logical phases
   - Natural recovery points
```

## Advanced Chaining Techniques

### Dynamic Handler Selection

```python
# Conceptual dynamic chaining
def build_chain(context):
    chain = Chain()
    
    # Dynamic handler selection
    if context.is_complex:
        chain.add(ComplexAnalyzer())
    else:
        chain.add(SimpleAnalyzer())
    
    # Conditional additions
    if context.needs_validation:
        chain.add(Validator())
    
    # Runtime-determined parallelism
    if context.file_count > 10:
        chain.add_parallel([
            FileProcessor(i) 
            for i in range(context.file_count)
        ])
    else:
        chain.add(SequentialProcessor())
    
    return chain
```

### Recursive Chains

```yaml
chain: recursive-optimizer
handlers:
  - id: measure
    handler: performance-measurer
    output: current_score
  
  - id: optimize
    handler: optimization-step
    input: ${measure.output}
  
  - id: check
    handler: improvement-checker
    input:
      before: ${measure.output}
      after: ${optimize.output}
  
  - id: recurse
    condition: ${check.output.improved}
    recurse_to: measure
    max_depth: 10
```

### Chain Composition

```yaml
# Chains can include other chains
chain: master-workflow
handlers:
  - id: setup
    handler: environment-setup
  
  - id: analysis_chain
    include_chain: comprehensive-analysis
    input: ${setup.output}
  
  - id: processing_chain
    include_chain: file-processor
    input: ${analysis_chain.output}
  
  - id: cleanup
    handler: environment-cleanup
```

## Performance Optimization

### Optimization Strategies

```markdown
## 1. Handler Reuse
Cache handler instances:
```yaml
handler_pool:
  max_instances: 10
  reuse_policy: least_recently_used
```

## 2. Batch Processing
Group similar operations:
```yaml
batching:
  enabled: true
  batch_size: 100
  timeout: 5s
```

## 3. Lazy Evaluation
Defer execution until needed:
```yaml
evaluation: lazy
execute_when: ${output.required}
```

## 4. Short-Circuit Evaluation
Stop early when possible:
```yaml
short_circuit:
  on_condition: ${result.found}
  skip_remaining: true
```
```

## Real-World Examples

### Example: Bug Fix Chain

```yaml
chain: bug-fix-workflow
handlers:
  - id: reproduce
    handler: bug-reproducer
    input: ${bug_report}
    output: reproduction_steps
  
  - id: locate
    handler: bug-locator
    input: ${reproduce.output}
    output: affected_files
  
  - id: analyze
    handler: root-cause-analyzer
    input:
      files: ${locate.output}
      steps: ${reproduce.output}
    output: root_cause
  
  - id: fix
    handler: bug-fixer
    input:
      cause: ${analyze.output}
      files: ${locate.output}
    output: fixed_files
  
  - id: test
    handler: test-runner
    input: ${fix.output}
    output: test_results
  
  - id: verify
    handler: fix-verifier
    input:
      original: ${reproduce.output}
      fixed: ${test.output}
    output: verification_status
```

### Example: Deployment Chain

```yaml
chain: safe-deployment
handlers:
  - id: build
    handler: application-builder
    output: build_artifacts
  
  - id: test
    parallel:
      - handler: unit-tester
      - handler: integration-tester
      - handler: smoke-tester
    input: ${build.output}
    fail_fast: true
  
  - id: stage
    handler: staging-deployer
    input: ${build.output}
    condition: ${test.all_passed}
  
  - id: validate_staging
    handler: staging-validator
    input: ${stage.output}
    timeout: 300s
  
  - id: approve
    handler: approval-gate
    input: ${validate_staging.output}
    manual: true
  
  - id: deploy
    handler: production-deployer
    input: ${build.output}
    condition: ${approve.approved}
    rollback_on_failure: true
```

## Best Practices

### DO:
- ✅ Keep handlers loosely coupled
- ✅ Define clear data contracts
- ✅ Handle errors at appropriate levels
- ✅ Use meaningful handler names
- ✅ Document chain purpose and flow
- ✅ Test chains end-to-end

### DON'T:
- ❌ Create circular dependencies
- ❌ Pass unnecessary data between handlers
- ❌ Ignore error cases
- ❌ Make chains too complex
- ❌ Skip validation between handlers
- ❌ Hardcode handler sequences

## Common Pitfalls

### Data Loss Between Handlers
**Problem**: Important data not passed through chain
**Solution**: Use chain context to preserve all data

### Tight Coupling
**Problem**: Handlers depend on specific implementations
**Solution**: Use contracts and interfaces

### Error Cascade
**Problem**: One error crashes entire chain
**Solution**: Implement proper error boundaries

### Performance Bottlenecks
**Problem**: Sequential execution of parallelizable work
**Solution**: Identify and parallelize independent handlers

## Testing Chains

### Unit Testing

```yaml
test: individual-handler
setup:
  mock_inputs: true
  isolate_handler: true
test_cases:
  - input: valid_data
    expected: success
  - input: invalid_data
    expected: error
```

### Integration Testing

```yaml
test: chain-integration
setup:
  use_real_handlers: true
  mock_external_services: true
test_cases:
  - scenario: happy_path
    verify: all_handlers_execute
  - scenario: error_recovery
    verify: fallback_activated
```

### End-to-End Testing

```yaml
test: full-chain
setup:
  production_like: true
  real_data: true
verify:
  - chain_completes
  - output_correct
  - performance_acceptable
  - errors_handled
```

## Related Resources

- [Creating Handlers](../guides/creating-handlers.md)
- [Workflow Composition](workflow-composition.md)
- [Pattern Composition](pattern-composition.md)
- [Handler Architecture](../architecture/handler-architecture.md)
- [Best Practices](../best-practices/handler-design.md)