---
id: deploy-specialist
name: Deploy Specialist
role: trigger
domain: workflow
stability: stable
triggers:
  - "get expert help on X"
  - "need specialist for Y"
  - "deploy expert"
dependencies: []
tools:
  - Task
version: 1.0.0
---

#### Handler: deploy-specialist {#deploy-specialist}
**Triggers**: "get expert help on X", "need specialist for Y", "deploy expert"
**Target Pattern**: Expertise area needed
**Pre-conditions**: 
- Clear task for specialist
- Constraints defined
**Process**:
1. Identify specialist type
2. Prepare task description
3. Set clear constraints
4. Deploy specialist
5. Integrate results
**Success**: Expert solution provided
**Failure**: Task unclear for specialist
**Examples**:
- "need expert on database design" → DB specialist
- "get security expert" → Security analysis