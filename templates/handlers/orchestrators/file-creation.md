---
id: file-creation
name: File Creation
title: File Creation
role: orchestrator
type: orchestrator
domain: file
stability: stable
status: stable
triggers:
  - "create file"
  - "new file"
  - "write a file"
  - "generate"
dependencies: []
tools:
  - Write
version: 1.0.0
---

#### Pattern: file-creation {#file-creation}
**Triggers**: create file, new file, "write a file", generate
**Pre-conditions**: File type and location clear
**Process**:
1. Check templates/conventions/#naming-conventions
2. Verify parent directory exists
3. If work-related → Create in proper work folder
4. Use Write tool (not Serena)
**Success**: File created with proper conventions
**Failure**: Ask for file details
**Examples**:
- "Create MyComponent.tsx" → Check casing conventions
- "New test file" → Follow test naming pattern

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/file-creation.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
