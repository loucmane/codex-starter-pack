---
id: simulation-test
name: Simulation Test
title: Simulation Test
role: trigger
type: trigger
domain: test
stability: stable
status: stable
triggers:
  - "simulate X"
  - "test workflow Y"
  - "dry run Z"
dependencies: []
tools: []
version: 1.0.0
---

#### Handler: simulation-test {#simulation-test}
**Triggers**: "simulate X", "test workflow Y", "dry run Z"
**Target Pattern**: Workflow or process to simulate
**Pre-conditions**: 
- Workflow defined
- Simulation possible
**Process**:
1. Set up simulation env
2. Create test scenario
3. Run simulation
4. Capture results
5. Analyze outcomes
6. Report findings
**Success**: Simulation reveals insights
**Failure**: Can't simulate accurately
**Examples**:
- "simulate the migration" → Process validation
- "test the deployment flow" → Deploy simulation

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/test/simulation-test.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
