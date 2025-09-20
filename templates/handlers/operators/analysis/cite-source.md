---
id: cite-source
name: Cite Source
role: operator
domain: analysis
stability: stable
triggers:
  - "where does this come from"
  - "what's the source"
  - "cite your reference"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: cite-source {#cite-source}
**Triggers**: "where does this come from", "what's the source", "cite your reference"
**Target Pattern**: Information needing citation
**Pre-conditions**: 
- Previous claim or information stated
- Source should be traceable
**Process**:
1. Identify information to cite
2. **PRIMARY**: Trace to source:
   - Code location (file:line)
   - Documentation section
   - Tool output
   - Memory reference
3. Provide exact reference
4. Include relevant context
5. Link to full source
**Success**: Source cited with precision
**Failure**: Source unclear, explain search
**Examples**:
- "where does that error come from" → Stack trace file:line
- "cite the naming convention" → templates/conventions/:section