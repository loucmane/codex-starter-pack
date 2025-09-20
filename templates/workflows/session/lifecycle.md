---
id: session-lifecycle
type: workflow-component
category: session
title: Session Lifecycle Management
dependencies:
  - ../patterns/task-management.md
related:
  - ./compaction.md
  - ./continuation.md
  - ./state-management.md
version: 1.0.0
status: stable
---

# Session Lifecycle Management

## ⚠️ CRITICAL: PREVENT WRONG INFORMATION IN sessions/

**THESE WILL CAUSE SESSION FAILURE:**
- Using any date/time except COPY-PASTED output from `date "+%Y-%m-%d %H:%M %Z"`
- Typing times from memory (even if you "just ran" the command)
- Using UTC when local time is needed
- Assuming task from context instead of asking user
- Guessing TaskMaster IDs
- Making up developer names
- Writing "probably" or "likely" information

**INSTEAD, ALWAYS:**
1. First message must clarify: "What task are we working on today?"
2. Run actual commands for dates/times
3. Mark unknown information as "Unknown" 
4. Ask before assuming

## 🚨 Pre-Flight Checklist

**BEFORE DOING ANYTHING ELSE:**

1. **Run these commands and save outputs:**
   ```bash
   date "+%Y-%m-%d %H:%M %Z"       # Save as $CURRENT_DATE (local time)
   pwd                             # Save as $WORKING_DIR  
   git branch --show-current       # Save as $CURRENT_BRANCH
   git config user.name || echo "Unknown"  # Save as $GIT_USER
   git log --oneline -5            # Save recent commits
   git status                      # Check for changes
   
   # If using Serena for this session
   echo "Serena memories:" && ls -la .serena/memories/ 2>/dev/null || echo "No Serena memories yet"
   ```

2. **Git Branch Naming Convention:**
   - Format: `feat/{task-id}-{descriptive-name}`
   - Example: `feat/004-shadcn-ui-setup`
   - The task ID should match TaskMaster task number
   - Keep descriptive name concise and kebab-case

3. **Determine the task:**
   - Did user specify a task? → Use their EXACT words
   - No? → Ask "What task should I work on?"
   - NEVER assume based on context

## Session Continuity Protocol

### At Session Start, AI MUST:

1. **FIRST RESPONSE TEMPLATE** (use every time):
   ```
   I'll help with development. First, let me establish the session context:
   
   1. Is this a continuation of the previous session or a new session?
      - If continuation: I'll resume where we left off
      - If new: I'll properly close the previous session first (if needed)
   
   2. What specific task should I work on? 
      - Please provide TaskMaster ID if applicable
      - Or describe what you'd like done
      - Or say "continue" to resume previous work
   
   3. Who is the developer for sessions/ tracking? (I'll check git config)
   
   While you answer, I'll check the current state...
   [Run and show command outputs including git user]
   ```

2. **Check for sessions/** - If exists, read it completely and summarize
   - **CRITICAL**: Read the ENTIRE previous session(s) - DO NOT SKIM
   - **REQUIRED**: Note ALL completed work to avoid duplication
   - **ANALYZE**: Which subtasks were marked done? What was tested? What was fixed?
   - **SUMMARIZE**: "Previous session completed: [specific achievements]"
   - Add new sessions at the TOP (most recent first)
   - Keep all previous sessions for history
   - Use `---` separator between sessions

2a. **If using Serena** - Activate project and read memories:
   - Run: `Activate project MomsBlog and list all memories`
   - Cross-reference Serena memories with sessions/
   - Note any discrepancies or additional context

### Session Lifecycle Rules:

1. **Session Continuation vs New Session**:
   - **If Continuation**: Keep current session entry, update progress
   - **If New Session**: 
     - Check if previous session has "Session End Status"
     - If not, ask: "The previous session wasn't properly ended. Should I close it now?"
     - If yes, add ending summary to previous session
     - Create new session entry at TOP of sessions/

2. **Never Assume Session is Ending**:
   - Sessions continue until explicitly ended by user
   - Don't add "Session End Status" unless user confirms
   - Keep using "Current Status" for ongoing work

3. **Session End Confirmation Required**:
   - If user mentions "ending", "stopping", or similar, ASK:
     ```
     Are you ending this session? If yes, I'll:
     - Update the session with final status
     - Create a Serena memory
     - Prepare handoff instructions
     ```
   - Only proceed with session closure if confirmed

## End of Session - Handoff Best Practices

### Required Steps (in order):

1. **Update sessions/ completely**:
   - Final progress log entry with timestamp
   - Update all sections (Code Changes, Current Status, Next Actions)
   - Add "Session End Status" with accomplishments

2. **Update work tracking handoff.md**:
   - Current state summary
   - What's been tested/verified
   - Known issues or blockers
   - Specific next steps

3. **Create Serena memory**:
   ```bash
   # Format: session_YYYY-MM-DD_descriptive_name
   session_$(date +%Y-%m-%d)_template_system_integration
   ```
   
   **Must include**:
   - Work completed with specific file names
   - Unfinished tasks with exact status
   - Important decisions and rationale
   - "How to Initialize Next Session" section with memory name
   
4. **Update todos final status**:
   - Mark all completed items as done
   - Leave in-progress items clearly marked
   - Add any discovered tasks

5. **Commit with descriptive message**:
   ```bash
   gac "feat: implement template system Phase 3 - added 12 critical integrations"
   ```

6. **Provide initialization message to user**:
   ```
   Session complete! Next session, start with:
   "Activate project MomsBlog, read memory session_2025-07-09_template_system_integration and sessions/"
   ```

## Handoff Quality Checklist:

- [ ] Can someone else continue exactly where you left off?
- [ ] Are all file locations clearly documented?
- [ ] Is the current branch and git status noted?
- [ ] Are test results and verification steps included?
- [ ] Is the next logical step obvious?
- [ ] Did you tell the user how to initialize next session?

## Session Testing Tracking

```markdown
### 📝 Progress Log
- **[HH:MM]** - Starting subtask 7.2: Header Component
- **[HH:MM]** - ✅ Implementation complete, creating testing checkpoint
- **[HH:MM]** - 🧪 TESTING CHECKPOINT: Awaiting user test
  - Files: Header.tsx, header.module.css
  - Focus: Responsive nav, accessibility
- **[HH:MM]** - 👤 User feedback: "Mobile menu overlaps logo on iPhone SE"
- **[HH:MM]** - 🔧 Fixing mobile menu positioning for small screens
- **[HH:MM]** - 🧪 Ready for re-test
- **[HH:MM]** - ✅ User approved: Header component complete
- **[HH:MM]** - Moving to subtask 7.3
```