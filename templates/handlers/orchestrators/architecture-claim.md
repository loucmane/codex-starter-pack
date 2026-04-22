---
id: architecture-claim
name: Architecture Claim
title: Architecture Claim
role: orchestrator
type: orchestrator
domain: analysis
stability: stable
status: stable
triggers:
  - "architecture"
  - "designed to"
  - "structured as"
  - "system claims"
dependencies: []
tools: []
version: 1.0.0
---

#### Pattern: architecture-claim {#architecture-claim}
**Triggers**: "architecture", "designed to", "structured as", system claims
**Pre-conditions**: Making design assertion
**Process**:
1. Search for architecture docs first
2. Find code evidence second
3. Cite both sources
**Success**: Multi-source evidence
**Failure**: "Let me investigate the architecture"
**Examples**:
- "The app uses MVC" → Find structure evidence
- "It's event-driven" → Locate event handling

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/architecture-claim.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
