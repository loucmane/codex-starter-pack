---
id: lost-context
name: Lost Context
role: orchestrator
domain: session
stability: stable
triggers:
  - "I'm lost"
  - "what was I doing"
  - "confused state"
dependencies: []
tools:
  - TodoWrite
  - git
version: 1.0.0
---

#### Pattern: lost-context {#lost-context}
**Triggers**: "I'm lost", "what was I doing", confused state
**Pre-conditions**: User needs orientation
**Process**:
1. Check TodoWrite state
2. Check recent work folders
3. Run git status
4. Provide current context summary
**Success**: User reoriented
**Failure**: Suggest starting fresh
**Examples**:
- "I'm lost" → Show current state
- "What was I working on?" → Display active tasks