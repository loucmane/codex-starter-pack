---
id: common-mistakes
type: workflow-component
category: guides
title: Common Mistakes That Break Sessions
dependencies:
  - ../session/lifecycle.md
related:
  - ../patterns/task-management.md
version: 1.0.0
status: stable
---

# Common Mistakes That Break Sessions

## 🚫 Critical Session-Breaking Mistakes

### 1. Wrong Information in sessions/

**❌ WRONG**: Typing timestamps from memory
```markdown
- **09:30** - Started work (guessed time)
```

**✅ RIGHT**: Copy-paste from date command
```markdown
- **09:32** - Started work [copied from: date "+%H:%M"]
```

### 2. Creating Duplicate Work

**❌ WRONG**: Starting fresh without checking
```
"Let me implement the header component"
[Already done in previous session]
```

**✅ RIGHT**: Always check first
```
"Let me check sessions/current...
I see header was completed in 7.2. Moving to 7.3."
```

### 3. Assuming Task Context

**❌ WRONG**: Guessing what user wants
```
"I'll continue with the authentication task"
[User wanted something else]
```

**✅ RIGHT**: Always ask explicitly
```
"What task should I work on today?
Or should I continue from where we left off?"
```

## 📁 File Management Mistakes

### 1. Creating Unnecessary Files

**❌ WRONG**: New file for every iteration
```
implementation-draft.md
implementation-v2.md
implementation-final.md
implementation-really-final.md
```

**✅ RIGHT**: Use the 6 core files
```
implementation.md (append new versions)
```

### 2. Wrong File Locations

**❌ WRONG**: Creating files anywhere
```
/random-folder/my-notes.md
/src/TODO.md
```

**✅ RIGHT**: Follow structure
```
/docs/ai/work-tracking/active/[work-folder]/tracker.md
```

## 🔧 Tool Usage Mistakes

### 1. Using Wrong Tools

**❌ WRONG**: Using any available tool
```python
# Using Python for simple file read
import os
with open('file.txt') as f:
    content = f.read()
```

**✅ RIGHT**: Use designated tools
```
Read("file.txt")  # Use MCP tools
```

### 2. Forgetting Tool Router

**❌ WRONG**: Direct tool selection
```
"I'll use grep to search"
```

**✅ RIGHT**: Check Tool Router first
```
"Checking TOOLS.md router...
For code search, Router says use Serena search_for_pattern"
```

## 🤝 Handoff Mistakes

### 1. Incomplete Session End

**❌ WRONG**: Abrupt stop
```
"Work done, goodbye!"
```

**✅ RIGHT**: Complete handoff
```
1. Update sessions/ final status
2. Create Serena memory
3. Update todos
4. Commit changes
5. Provide init instructions
```

### 2. Missing Context

**❌ WRONG**: Vague status
```
"Made some progress on authentication"
```

**✅ RIGHT**: Specific details
```
"Completed JWT token generation (auth/token.ts)
Implemented middleware (auth/middleware.ts)
Next: Add refresh token logic"
```

## 📝 Documentation Mistakes

### 1. Not Updating in Real-Time

**❌ WRONG**: Batch updates at end
```
[Do all work]
[Try to remember everything]
[Update docs]
```

**✅ RIGHT**: Document as you go
```
[Complete subtask] → Update tracker
[Make decision] → Update decisions.md
[Find issue] → Update findings.md
```

### 2. Generic Descriptions

**❌ WRONG**: Non-specific updates
```
"Updated some components"
"Fixed various bugs"
"Improved performance"
```

**✅ RIGHT**: Specific details
```
"Updated Header.tsx - added mobile menu"
"Fixed auth timeout bug in middleware.ts line 45"
"Improved query performance from 2s to 200ms"
```

## 🎯 Testing Mistakes

### 1. Skipping Test Checkpoints

**❌ WRONG**: Moving to next task immediately
```
"Header done, starting footer"
[No testing pause]
```

**✅ RIGHT**: Pause for testing
```
"Header implemented. 🧪 Ready for your testing:
- Files: Header.tsx, header.css
- Run: npm dev
- Check: Mobile menu, accessibility"
```

### 2. Not Documenting Test Results

**❌ WRONG**: No test tracking
```
"Tests passed, moving on"
```

**✅ RIGHT**: Document results
```
"Test Results:
- Unit tests: 12/12 passing
- E2E: 3/3 passing
- Accessibility: WCAG AA compliant
- Performance: LCP 1.2s"
```

## 🧠 Context Mistakes

### 1. Not Reading Full Context

**❌ WRONG**: Skimming sessions/
```
"I see we're working on task 7"
[Misses that 7.1-7.3 are done]
```

**✅ RIGHT**: Read completely
```
"Reading full sessions/...
Task 7: Subtasks 7.1-7.3 complete
Currently on: 7.4"
```

### 2. Ignoring Serena Memories

**❌ WRONG**: Only checking sessions/
```
[Misses important context from memories]
```

**✅ RIGHT**: Cross-reference sources
```
1. Read sessions/
2. Check relevant Serena memories
3. Review current todos
4. Verify git status
```

## Prevention Checklist

Before starting work:
- [ ] Run date command for timestamps
- [ ] Read entire sessions/
- [ ] Check Serena memories
- [ ] Verify current task with user
- [ ] Review Tool Router

During work:
- [ ] Update docs in real-time
- [ ] Use correct tools
- [ ] Create test checkpoints
- [ ] Track all decisions

Before ending:
- [ ] Complete all handoff steps
- [ ] Create Serena memory
- [ ] Commit with clear message
- [ ] Provide init instructions

## Recovery Procedures

If you made a mistake:

1. **Acknowledge immediately**
   "I made an error - let me correct that"

2. **Fix the mistake**
   Correct the wrong information

3. **Document the correction**
   Note what was wrong and why

4. **Prevent recurrence**
   Add to this guide if novel

## Remember

**The goal isn't perfection, it's consistency and transparency.**

When in doubt:
- Ask rather than assume
- Check rather than guess
- Document rather than remember
- Test rather than hope