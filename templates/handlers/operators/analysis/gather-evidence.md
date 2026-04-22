---
id: gather-evidence
name: Gather Evidence
title: Gather Evidence
role: operator
type: operator
domain: analysis
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/analysis/gather-evidence.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
