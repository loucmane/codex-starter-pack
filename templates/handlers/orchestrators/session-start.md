---
id: session-start
name: Session Start
role: orchestrator
domain: session
stability: stable
triggers:
  - "start new session"
  - "begin session"
  - "new session"
dependencies:
  - session-resolver
tools:
  - date
  - git
  - Edit
  - Read
version: 2.0.0
---

#### Handler: session-start {#session-start}
**Triggers**: "start new session", "begin session", "new session"
**Target Pattern**: User's task description
**Pre-conditions**: 
- sessions/ directory exists
- Git status available
- Date command available
**Process**:
1. **Load session-resolver module**:
   - Import resolve-session function
   - Import get-current-session function
   - Import validate-session-id function
2. **Check for existing session**:
   - Call `get-current-session()` to check sessions/current
   - If active session exists:
     - Ask if continuing or starting fresh
     - If continuing, update existing session
     - If fresh, close current and create new
3. **Gather session data**:
   - `date "+%Y-%m-%d %H:%M %Z"` for timestamp
   - `date "+%Y-%m-%d"` for date
   - `date "+%H:%M %Z"` for time
   - `git config user.name` for developer
   - `git branch --show-current` for branch
   - User's exact task description
4. **Generate session ID**:
   - Format: YYYY-MM-DD-NNN
   - Check sessions/YYYY/MM/ for existing sessions today
   - Increment NNN from highest existing or start at 001
   - Validate with `validate-session-id(session_id)`
5. **Create session file structure**:
   - Ensure directory exists: sessions/YYYY/MM/
   - Create file: YYYY-MM-DD-NNN-untitled.md
6. **Write session with proper structure**:
   ```yaml
   ---
   session_id: YYYY-MM-DD-NNN
   date: YYYY-MM-DD
   time: HH:MM ZONE
   title: untitled
   checksum: [optional]
   ---
   ```
   ```markdown
   ## Session: YYYY-MM-DD HH:MM ZONE
   
   **AI Assistant**: Claude (model) ✓
   **Developer**: [name]
   **Task**: [exact user words]
   **Task Source**: User request
   **TaskMaster ID**: [if applicable]
   
   ### Session Validation ✓
   - [x] Date from `date` command: [timestamp]
   - [x] Task verified by: user request
   - [x] Git status checked: Yes - [branch]
   - [x] TaskMaster tasks reviewed: [status]
   - [x] Previous session reviewed: [Yes/No]
   
   ### 🎯 Session Goals
   - [ ] Primary: [main goal from user input]
   - [ ] Secondary: [derived goal if applicable]
   - [ ] Tertiary: [stretch goal if applicable]
   
   ### 📍 Starting Context
   [Context from previous session or fresh start]
   
   ### 📝 Progress Log
   - **[HH:MM]** - Session started, task: [task]
   ```
7. **Update system references**:
   - Update sessions/current symlink to new session (safe, no rm*):
     ```bash
     ln -sfn "sessions/YYYY/MM/YYYY-MM-DD-NNN-title.md" sessions/current
     test -L sessions/current && readlink -f sessions/current
     ```
   - Update `sessions/state.json` helper (non-authoritative):
     ```json
     {
       "current": "YYYY-MM-DD-NNN-title.md",
       "paused": ["YYYY-MM-DD-PPP-prev.md"],
       "updated_at": "2025-08-13T12:34:56Z"
     }
     ```
     - Move previous `current` (if any) into `paused`; set new `current`
   - For compatibility: Append session header to sessions/
   - Note in sessions/: "Active session: sessions/YYYY/MM/[filename]"
8. **Orchestrate sub-handlers if needed**:
   - If complex task, delegate to specific domain handlers
   - Pass session context to sub-handlers
   - Ensure all handlers aware of new session location
**Success**: Session created in sessions/, symlink updated, system aware
**Failure**: Fall back to sessions/ if sessions/ unavailable
**Examples**:
- "start new session" → Fresh session in sessions/YYYY/MM/
- "begin work on auth" → Session with auth focus, may trigger auth handlers