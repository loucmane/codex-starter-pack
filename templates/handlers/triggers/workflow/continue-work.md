---
id: continue-work
name: Continue Work
role: trigger
domain: workflow
stability: stable
triggers:
  - "continue with X"
  - "back to Y"
  - "resume Z"
dependencies: []
tools:
  - TodoRead
version: 1.0.0
---

#### Handler: continue-work {#continue-work}
**Triggers**: "continue with X", "back to Y", "resume Z"
**Target Pattern**: Extract work identifier after key verb
**Pre-conditions**: 
- Existing work folder must exist
- sessions/ has record of work
**Process**:
1. Search for matching work folder
2. Read current state from TRACKER.md
3. Check TodoWrite for in-progress items
4. Show current status to user
5. Resume from last checkpoint
**Success**: Previous context restored, work resumed
**Failure**: No matching work found, show available options
**Examples**:
- "continue with auth" → Finds *-authentication-ACTIVE folder
- "back to the flow creator" → Resumes meta-flow-creator work