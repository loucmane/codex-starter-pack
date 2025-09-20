---
id: workflow-to-tool
name: Workflow to Tool Router
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "Workflow step requires specific tool"
dependencies:
  - search-code
  - find-references
tools:
  - TOOLS.md tool selection
version: 1.0.0
---

#### Handler: workflow-to-tool {#workflow-to-tool}
**Triggers**: Workflow step requires specific tool
**Target Pattern**: Tool needed within workflow context
**Pre-conditions**: 
- Active workflow in progress
- Tool requirement identified
**Process**:
1. Identify required tool capability
2. Route to TOOLS.md tool selection
3. Execute tool with workflow context
4. Return results to workflow
**Success**: Tool completes, workflow continues
**Failure**: Suggest alternative tools or manual steps
**Examples**:
- Bug fix workflow needs search → Routes to search-code handler
- Refactoring needs symbol analysis → Routes to find-references