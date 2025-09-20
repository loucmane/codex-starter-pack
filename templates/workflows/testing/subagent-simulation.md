---
id: subagent-simulation-testing
type: workflow-component
category: testing
title: Subagent Simulation Testing
dependencies:
  - ./simulation-testing.md
  - ../patterns/multi-agent-orchestration.md
related:
  - ./test-checkpoints.md
version: 1.0.0
status: stable
---

# Subagent Simulation Testing

## Purpose

Deploy simulated subagents to test and validate complex systems without full implementation. Particularly useful for:
- Testing workflow interactions
- Validating orchestration patterns
- Simulating specialist responses
- Testing error handling

## Subagent Types for Testing

### Mock Specialists
- UI/UX Expert
- Security Analyst
- Performance Engineer
- Database Architect
- Accessibility Auditor

### System Simulators
- API Response Simulator
- Database Query Simulator
- User Interaction Simulator
- Network Condition Simulator

## Deployment Pattern

```javascript
// Simulated specialist deployment
Task("Simulate UI Expert Review")
Prompt: `
You are a UI/UX expert reviewing a component design.

COMPONENT TO REVIEW:
- Name: UserProfile
- Purpose: Display user information
- Current implementation: [details]

=== SIMULATION CONSTRAINTS ===
RESPOND AS IF YOU ARE:
- A senior UI/UX designer
- Focused on user experience
- Knowledgeable about accessibility
- Familiar with modern patterns

PROVIDE:
- Design assessment
- Usability concerns
- Improvement suggestions
- Accessibility notes

DO NOT:
- Implement changes
- Access real files
- Make actual modifications
=== END CONSTRAINTS ===

Review the component and provide expert feedback.
`
```

## Test Scenarios

### Scenario 1: Multi-Specialist Coordination

```markdown
## Test: Payment System Implementation

### Deploy Specialists
1. Security Expert - Review payment handling
2. Database Architect - Design transaction storage
3. UI Expert - Review checkout flow

### Expected Interactions
- Security flags PCI compliance issues
- Database suggests transaction patterns
- UI recommends flow improvements

### Validation Points
- [ ] All specialists provide domain-specific feedback
- [ ] No conflicts between recommendations
- [ ] Integration points identified
- [ ] Final solution incorporates all perspectives
```

### Scenario 2: Error Handling Simulation

```markdown
## Test: Specialist Failure Recovery

### Simulate Failures
1. Deploy specialist with network timeout
2. Deploy specialist with invalid response
3. Deploy specialist that exceeds constraints

### Expected Behavior
- Timeout: Retry with backoff
- Invalid: Request clarification
- Constraint violation: Reject and re-prompt

### Recovery Validation
- [ ] Graceful failure handling
- [ ] Clear error messages
- [ ] Alternative approaches suggested
- [ ] No session corruption
```

## Simulation Test Report Template

```markdown
## Subagent Test Results - [Date]

### Test Configuration
- **Scenario**: [What's being tested]
- **Specialists**: [List of simulated agents]
- **Constraints**: [Applied limitations]

### Execution Summary
| Specialist | Task | Result | Time |
|------------|------|--------|------|
| UI Expert | Review layout | ✅ Pass | 2.3s |
| Security | Audit auth | ⚠️ Warning | 3.1s |
| Database | Schema design | ✅ Pass | 1.8s |

### Key Findings
1. **Success**: [What worked well]
2. **Issues**: [Problems encountered]
3. **Insights**: [Unexpected discoveries]

### Recommendations
- [Improvements needed]
- [Process refinements]
- [Additional tests required]
```

## Testing Best Practices

### DO:
- ✅ Set clear simulation boundaries
- ✅ Test both success and failure paths
- ✅ Verify constraint enforcement
- ✅ Document specialist interactions
- ✅ Validate orchestration logic

### DON'T:
- ❌ Let simulations access real data
- ❌ Allow sessions/ modifications
- ❌ Skip constraint validation
- ❌ Mix simulation with production
- ❌ Ignore timeout scenarios

## Common Test Patterns

### Pattern 1: Specialist Opinion Gathering
```
Deploy multiple specialists →
Gather diverse perspectives →
Synthesize recommendations →
Validate consensus building
```

### Pattern 2: Sequential Processing
```
Specialist 1 analyzes →
Passes findings to Specialist 2 →
Specialist 2 builds on analysis →
Validate information flow
```

### Pattern 3: Conflict Resolution
```
Specialists disagree →
Orchestrator mediates →
Compromise reached →
Validate resolution process
```

## Integration with Other Systems

### With Task Management
- Create todos for each test scenario
- Track specialist deployment status
- Mark validations complete

### With Session Management
- Log simulation deployments
- Track test execution in sessions/
- Document results for handoff

### With Evidence Gathering
- Capture specialist responses
- Document decision rationale
- Build knowledge base from tests

## Monitoring and Metrics

### Track:
- Response times per specialist
- Success/failure rates
- Constraint violations
- Recovery effectiveness
- Orchestration efficiency

### Report:
- Average specialist performance
- Common failure patterns
- Orchestration bottlenecks
- Improvement opportunities

## Advanced Simulations

### Stress Testing
- Deploy 10+ specialists simultaneously
- Test queue management
- Verify resource limits
- Check timeout handling

### Chaos Testing
- Random specialist failures
- Conflicting recommendations
- Circular dependencies
- Recovery mechanisms

### Performance Testing
- Measure orchestration overhead
- Track context switching costs
- Optimize deployment patterns
- Benchmark against baselines

## Remember

**Simulations reveal system behavior without risk.**

Use them to:
- Validate workflows before implementation
- Test edge cases safely
- Train orchestration patterns
- Build confidence in complex flows