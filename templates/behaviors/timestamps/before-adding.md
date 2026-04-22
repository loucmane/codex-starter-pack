---
trigger: Adding timestamp to any file
title: Before Adding Timestamps
action: Run date command to get actual system time
blocks: Cannot add timestamp without checking actual time
category: timestamps
type: behavior
enforcement: mandatory
status: stable
version: 1.0.0
---

# Before Adding Timestamps

## Trigger Condition
This behavior fires whenever:
- Adding timestamp to sessions/ progress log
- Adding timestamp to TRACKER.md
- Adding timestamp to any work tracking file
- Creating timestamped entries anywhere
- Writing "current time" or "now" references

## Required Action
```
1. ALWAYS run the date command first:
   - For time only: date '+%H:%M'
   - For full timestamp: date '+%Y-%m-%d %H:%M:%S'
   - For date only: date '+%Y-%m-%d'
   - With timezone: date '+%Y-%m-%d %H:%M %Z'

2. Use the EXACT output from the command

3. NEVER estimate or make up timestamps

4. Format according to context:
   - sessions/: **HH:MM** format in bold
   - TRACKER.md: ISO format YYYY-MM-DD HH:MM
   - Git commits: Use actual time
   - Work files: Context-appropriate format
```

## Blocking Gate
**CANNOT PROCEED** with timestamp until:
- Date command has been executed
- Actual system time obtained
- Format appropriate for context
- No estimation or guessing

## Satisfaction Criteria
✓ Date command executed
✓ Actual time captured from output
✓ Timestamp matches system time exactly
✓ Format appropriate for target file

## Example Workflows

### ❌ Wrong Approach
```
AI thinks: "It's probably around 2:15 PM"
Writes: "**14:15** - Completed implementation"
Problem: Made up timestamp without checking
```

### ✅ Correct Approach
```
1. Run: date '+%H:%M'
2. Output: "13:56"
3. Write: "**13:56** - Completed implementation"
Result: Accurate timestamp from system
```

### Full Timestamp Example
```
1. Run: date '+%Y-%m-%d %H:%M:%S'
2. Output: "2025-01-27 13:56:42"
3. Write: "2025-01-27 13:56:42 - System check complete"
```

## Common Timestamp Formats

### sessions/ Progress Log
```bash
date '+%H:%M'  # Returns: "13:56"
# Format: **HH:MM** - Progress entry
```

### Work Tracking Files
```bash
date '+%Y-%m-%d %H:%M'  # Returns: "2025-01-27 13:56"
# Format: ### YYYY-MM-DD HH:MM - Entry
```

### Git Commits
```bash
date '+%Y-%m-%d'  # Returns: "2025-01-27"
# Use in commit messages when needed
```

### With Timezone
```bash
date '+%Y-%m-%d %H:%M %Z'  # Returns: "2025-01-27 13:56 EST"
# When timezone context matters
```

## Special Considerations

### Multiple Timestamps
When adding several timestamps in sequence:
- Run date command for EACH timestamp
- Don't reuse old timestamps
- Time passes between entries

### Session Duration
For calculating session length:
- Capture start time at beginning
- Capture end time at completion
- Calculate difference accurately

### Historical Timestamps
When referencing past events:
- Use recorded timestamps from files
- Don't reconstruct from memory
- Mark as "approximately" if uncertain

## Cross-References
- [sessions/ conventions](../../templates/conventions/#session-md-structure)
- [work-tracking/update-tracker.md](../work-tracking/update-tracker.md)
- [session/session-end.md](../session/session-end.md)

## Error Cases
- **System time unavailable**: Note as "timestamp unavailable"
- **Timezone confusion**: Always specify timezone if ambiguous
- **Format mismatch**: Check target file conventions

## Why This Gate Exists
- Ensures accurate time tracking
- Prevents timeline confusion
- Maintains audit trail integrity
- Enables accurate session duration calculation
- Supports debugging with real timestamps

## Common Violations to Avoid
1. **Estimating time**: "It's probably 2:30" → Never guess
2. **Reusing old time**: Using 14:15 for multiple entries
3. **Future timestamps**: Writing 15:00 when it's 14:45
4. **Skipping seconds**: When precision matters
5. **Wrong timezone**: Using UTC when local expected

## Remember
**Every timestamp must come from the date command - no exceptions!**

## Progress Log

- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:templates/behaviors/timestamps/before-adding.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 behavior-standardization slice
