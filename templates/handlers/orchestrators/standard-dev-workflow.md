---
id: standard-dev-workflow
name: Standard Development Workflow
role: orchestrator
domain: development
stability: stable
triggers:
  - "implement X"
  - "add feature Y"
  - "create functionality Z"  
dependencies:
  - start-new-work
tools:
  - TodoWrite
version: 1.0.0
---

#### Handler: standard-dev-workflow {#standard-dev-workflow}
**Triggers**: "implement X", "add feature Y", "create functionality Z"
**Target Pattern**: Feature specification after action verb
**Pre-conditions**: 
- Clear feature requirements
- Work folder exists or will be created
**Process**:
1. If no work folder, route to start-new-work first
2. Break down into implementation steps
3. Create detailed todos
4. Begin with research/exploration
5. Follow TDD if applicable
6. Document as you go
**Success**: Feature implemented with tests and docs
**Failure**: Requirements unclear, needs clarification
**Examples**:
- "implement user login" → Full auth flow
- "add dark mode" → Theme system implementation