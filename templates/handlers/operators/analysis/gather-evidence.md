---
id: gather-evidence
name: Gather Evidence
role: operator
domain: analysis
stability: stable
triggers:
  - "find evidence for X"
  - "gather proof of Y"
  - "show support for Z"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: gather-evidence {#gather-evidence}
**Triggers**: "find evidence for X", "gather proof of Y", "show support for Z"
**Target Pattern**: Topic needing evidence
**Pre-conditions**: 
- Clear evidence target
- Relevant sources available
**Process**:
1. Identify evidence types needed
2. **PRIMARY**: Serena searches:
   - Code implementation
   - Documentation
   - Test coverage
   - Comments/commits
3. **SECONDARY**: External evidence:
   - Package.json dependencies
   - Config files
   - Git history
4. Organize by relevance
5. Summarize findings
**Success**: Multiple evidence sources found
**Failure**: Limited evidence available
**Examples**:
- "find evidence of performance optimization" → Code patterns + commits
- "gather proof of security measures" → Auth code + tests