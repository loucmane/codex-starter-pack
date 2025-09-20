---
id: evidence-check
name: Evidence Check
role: orchestrator
domain: analysis
stability: stable
triggers:
  - "the system"
  - "it uses"
  - "the code"
  - "claims about implementation"
dependencies:
  - gather-evidence
tools: []
version: 1.0.0
---

#### Pattern: evidence-check {#evidence-check}
**Triggers**: "the system", "it uses", "the code", claims about implementation
**Pre-conditions**: Making assertion about codebase
**Process**:
1. Flag: NEED_EVIDENCE = true
2. Load CONVENTIONS.md#gather-evidence
3. Search for proof before claiming
4. Include file:line reference
**Success**: Evidence found and cited
**Failure**: "I need to verify this"
**Examples**:
- "The system uses JWT" → Must find JWT usage
- "It implements caching" → Must locate cache code