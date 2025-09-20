---
id: architecture-claim
name: Architecture Claim
role: orchestrator
domain: analysis
stability: stable
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