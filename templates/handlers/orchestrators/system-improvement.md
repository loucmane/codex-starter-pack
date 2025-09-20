---
id: system-improvement
name: System Improvement
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "improve system"
  - "make better"
  - "enhancement requests"
dependencies:
  - system-improvements
tools: []
version: 1.0.0
---

#### Pattern: system-improvement {#system-improvement}
**Triggers**: "improve system", "make better", enhancement requests
**Pre-conditions**: Meta-work requested
**Process**:
1. Load BUILDING-BETTER.md#system-improvements
2. Check which component to improve
3. Follow improvement workflow
**Success**: System enhanced
**Failure**: Ask what to improve
**Examples**:
- "Make reminders better" → This pattern system!
- "Improve handlers" → Update template files