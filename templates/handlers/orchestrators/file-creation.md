---
id: file-creation
name: File Creation
role: orchestrator
domain: file
stability: stable
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