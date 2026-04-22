---
id: system-improvement
name: System Improvement
title: System Improvement
role: orchestrator
type: orchestrator
domain: workflow
stability: stable
status: stable
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
1. Load templates/integration/guides/extending-templates.md#extending-the-template-system
2. Check which component to improve
3. Follow improvement workflow
**Success**: System enhanced
**Failure**: Ask what to improve
**Examples**:
- "Make reminders better" → This pattern system!
- "Improve handlers" → Update template files

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/system-improvement.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
