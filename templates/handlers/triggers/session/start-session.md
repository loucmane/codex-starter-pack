---
id: start-session
name: Start Session with Smart Title
title: Start Session with Smart Title
role: trigger
type: trigger
domain: session
stability: stable
status: stable
triggers:
  - "let's start"
  - "begin work"
  - "start today's session"
  - "new session"
dependencies:
  - session-resolver
tools:
  - Edit
  - Read
  - Bash
version: 3.0.0
---

# Start Session Handler

## Purpose
Creates new session files with meaningful titles derived from the task description.

## Title Generation Strategy

### Priority Order for Title Extraction:
1. **Explicit task description** from user input
2. **Primary goal** if specified  
3. **Context from previous session** if continuing
4. **Default to task type** (e.g., "debugging", "feature-development")
5. **Fallback to "general-work"** (never "untitled")

### Integration with Hooks (Title Hints)
- The UserPromptSubmit hook stores optional title hints in `logs/state.json` under:
  - `session.exact_title` (preferred when provided by the user, e.g., "called 'My Feature'")
  - `session.suggested_title` (kebab-case hint derived from the request)
- Use this precedence when generating the title:
  1. `session.exact_title` if present
  2. `session.suggested_title` if present
  3. Extracted description from user input (per strategy above)
  4. Previous session context
  5. Task type (e.g., "debugging", "feature-development")
  6. Fallback: `general-development` (never "untitled")

#### Example (reading state)
```python
import json
from pathlib import Path

state = {}
try:
    p = Path('logs/state.json')
    if p.exists():
        state = json.loads(p.read_text())
except Exception:
    state = {}

title = None
exact = state.get('session', {}).get('exact_title')
hint = state.get('session', {}).get('suggested_title')
if exact:
    title = exact
elif hint:
    title = hint
else:
    title = 'general-development'
```

### Title Format Rules:
- Maximum 60 characters for filename
- Convert to kebab-case (lowercase-with-dashes)
- Remove special characters
- Keep descriptive and meaningful
- Examples:
  - User: "let's start working on auth" → `implement-authentication`
  - User: "begin debugging the API" → `debug-api-issues`
  - User: "continue from yesterday" → `continue-[previous-task-name]`

## Execution Protocol

### 1. Gather Context
```bash
# Get timestamp
date '+%Y-%m-%d %H:%M %Z'

# Check git status
git status --short
git rev-parse --abbrev-ref HEAD

# Check for existing session
ls -la sessions/current 2>/dev/null || echo "No current session"
```

### 2. Extract Task Information
```
From user input, identify:
- Main action verb (implement, fix, debug, refactor, etc.)
- Target component/feature
- Continuation context if applicable

Examples:
- "let's fix the login bug" → fix-login-bug
- "start implementing user profiles" → implement-user-profiles
- "continue template migration" → continue-template-migration
```

### 3. Generate Session ID & Title
```python
# Pseudocode for title generation
task_description = extract_from_user_input()
if not task_description:
    task_description = get_from_previous_session()
if not task_description:
    task_description = "general-development"

# Convert to filename-safe format
title = task_description.lower()
title = re.sub(r'[^\w\s-]', '', title)
title = re.sub(r'\s+', '-', title)
title = title[:60].strip('-')

# Generate session ID
date_part = "YYYY-MM-DD"
sequence = get_next_sequence_for_date(date_part)
session_id = f"{date_part}-{sequence:03d}"
filename = f"{session_id}-{title}.md"
```

### 4. Create Session File
```yaml
---
session_id: YYYY-MM-DD-NNN
date: YYYY-MM-DD
time: HH:MM ZONE
title: Title Case Version of Task
checksum: [calculate if needed]
---

## Session: YYYY-MM-DD HH:MM ZONE

**AI Assistant**: Claude (model) ✓
**Developer**: [from git config]
**Task**: [Full task description]
**Task Source**: User request

### Session Validation ✓
- [x] Date from `date` command: [timestamp]
- [x] Task verified by: user request
- [x] Git status checked: Yes - [branch]
- [x] Previous session reviewed: [Yes/No]

### 🎯 Session Goals
- [ ] Primary: [Based on task extraction]
- [ ] Secondary: [If applicable]
- [ ] Tertiary: [If applicable]

### 📍 Starting Context
[Previous session context or fresh start]

### 📝 Progress Log
- **[HH:MM]** - Session started: [task description]
```

### 5. Update Current Symlink (safe, no rm*)
```bash
# Atomically re-point the symlink without deleting the target
# Works even if sessions/current exists (ln -sfn replaces the link itself)
ln -sfn "sessions/YYYY/MM/YYYY-MM-DD-NNN-title.md" sessions/current

# Optional: verify
test -L sessions/current && readlink -f sessions/current
```

### 6. Backwards Compatibility
For sessions/ compatibility:
- Append minimal session header
- Note that real session is in sessions/

### 7. Update sessions/state.json (non-authoritative helper)
```json
{
  "current": "YYYY-MM-DD-NNN-title.md",
  "paused": ["YYYY-MM-DD-PPP-prev.md"],
  "updated_at": "2025-08-13T12:34:56Z"
}
```
- Purpose: helper for UIs/agents; `sessions/current` remains the source of truth
- Recommended flow when starting a new same-day session:
  - Move previous `current` (if any) to `paused`
  - Set `current` to the new filename
  - Keep ISO timestamps for auditing

## Example Workflows

### Starting Fresh Work
```
User: "let's start implementing the search feature"
Title: implement-search-feature
File: 2025-08-09-001-implement-search-feature.md
```

### Continuing Previous Work
```
User: "let's continue"
[Read previous session for context]
Title: continue-[previous-task-name]
File: 2025-08-09-001-continue-template-migration.md
```

### Debugging Session
```
User: "need to debug the API errors"
Title: debug-api-errors
File: 2025-08-09-001-debug-api-errors.md
```

## Error Handling

### Cannot Extract Title
- Never use "untitled"
- Default to task type: "development", "debugging", "review"
- Include timestamp if absolutely necessary: "session-YYYYMMDD"

### Directory Creation Issues
- Ensure sessions/YYYY/MM/ exists
- Create with proper permissions
- Fall back to sessions/ if critical failure

## Integration Points

### With session-resolver
- Ensures new session is immediately resolvable
- Updates current pointer atomically
- Maintains format compatibility

### With end-session handler
- Provides proper title for session summary
- Makes session history searchable
- Enables meaningful session navigation

## Remember
**Every session deserves a meaningful title that describes the work being done!**

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/triggers/session/start-session.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
