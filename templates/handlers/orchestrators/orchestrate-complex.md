---
id: orchestrate-complex
name: Orchestrate Complex
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "this needs multiple experts"
  - "orchestrate X"
  - "coordinate specialists for Y"
dependencies:
  - deploy-specialist
tools:
  - Task
version: 1.0.0
---

#### Handler: orchestrate-complex {#orchestrate-complex}
**Triggers**: "this needs multiple experts", "orchestrate X", "coordinate specialists for Y"
**Target Pattern**: Complex multi-domain task
**Pre-conditions**: 
- Task spans multiple domains
- Clear decomposition possible
**Process**:
1. Decompose into specialist tasks
2. Identify dependencies
3. Deploy in correct order
4. Coordinate results
5. Synthesize solutions
**Success**: Coordinated solution achieved
**Failure**: Dependencies block progress
**Examples**:
- "orchestrate full feature" → Multi-specialist flow
- "coordinate auth implementation" → Security + DB + API experts