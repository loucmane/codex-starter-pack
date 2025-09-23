---
id: work-continuation
name: Work Continuation
role: orchestrator
domain: workflow
stability: stable
triggers:
  - "continue"
  - "resume"
  - "back to"
  - "keep working"
  - "where were we"
dependencies:
  - continue-work
tools:
  - TodoWrite
version: 1.0.0
---
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.


#### Pattern: work-continuation {#work-continuation}
**Triggers**: continue, resume, "back to", "keep working", "where were we"
**Pre-conditions**: Previous work context exists
**Process**:
1. Check TodoWrite for active tasks
2. Check recent work folders
3. Load WORKFLOWS.md#continue-work
**Success**: Resumed from correct context
**Failure**: Ask which work to continue
**Examples**:
- "Continue working on auth" → Resumes auth work
- "Where were we?" → Shows current context