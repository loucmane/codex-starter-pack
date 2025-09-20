---
id: tool-to-convention
name: Tool to Convention Validator
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "Tool usage must follow conventions"
dependencies: []
tools:
  - templates/conventions/ checks
version: 1.0.0
---

#### Handler: tool-to-convention {#tool-to-convention}
**Triggers**: Tool usage must follow conventions
**Target Pattern**: Convention check needed before tool use
**Pre-conditions**: 
- Tool selected for use
- Conventions apply to operation
**Process**:
1. Identify applicable conventions
2. Route to templates/conventions/ checks
3. Validate tool parameters
4. Execute with convention compliance
**Success**: Tool runs with proper conventions
**Failure**: Show convention violations, correct and retry
**Examples**:
- Git commit → Check commit message conventions
- File naming → Validate naming standards