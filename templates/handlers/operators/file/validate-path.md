---
id: validate-path
name: Validate Path
title: Validate Path
role: operator
type: operator
domain: file
stability: stable
status: stable
triggers:
  - "is this the right location"
  - "check file placement"
  - "validate path"
dependencies: []
tools:
  - Serena
version: 1.0.0
---

#### Handler: validate-path {#validate-path}
**Triggers**: "is this the right location", "check file placement", "validate path"
**Target Pattern**: File path to validate
**Pre-conditions**: 
- Path or file type clear
- Project structure known
**Process**:
1. Parse path components
2. **PRIMARY**: Use Serena to find similar files
3. Check project structure conventions
4. Validate against patterns:
   - Source organization
   - Test colocation
   - Asset placement
5. Provide assessment
**Success**: Path validated with reasoning
**Failure**: Multiple valid options exist
**Examples**:
- "is src/utils/auth.ts correct" → Validate utils pattern
- "check test file location" → Confirm colocation rule

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/file/validate-path.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
