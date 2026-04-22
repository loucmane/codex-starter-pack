---
id: deploy-specialist
name: Deploy Specialist
title: Deploy Specialist
role: trigger
type: trigger
domain: workflow
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/analysis/deploy-specialist.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
