---
id: timestamp-usage-patterns
type: convention
category: timestamps
title: When and Where to Use Timestamps
applies_to: all
enforcement: required
dependencies:
  - timestamp-format-rules
version: 1.0.0
status: stable
---

# Timestamp Usage Patterns

## Convention
Timestamps must be used consistently in specific contexts to maintain chronological accuracy and enable proper tracking.

> **Guard enforcement**: `scripts/codex-guard` verifies that timestamps come from recorded `date` commands and that chronological rules are respected.

## When Timestamps Are Required

### Always Required
1. **sessions/ entries** - Every session start
2. **Progress logs** - Every entry
3. **Work folder creation** - In folder name
4. **TRACKER.md updates** - Started/Updated fields
5. **HANDOFF.md** - Last session time
6. **Memory file names** - Session memories
7. **Git commits** - When referencing time
8. **Error logs** - Every error entry
9. **Performance metrics** - All measurements
10. **Changelog entries** - Version dates

### Sometimes Required
1. **Code comments** - For TODOs with deadlines
2. **Documentation** - Last updated notices
3. **Test results** - Execution times
4. **Meeting notes** - Start/end times
5. **Decision records** - When decision made

### Not Required
1. **Regular code** - Unless tracking specific times
2. **Type definitions** - Static content
3. **Configuration files** - Unless versioned
4. **README files** - Unless showing examples

## Context-Specific Usage

### Session Documentation
```markdown
## Session: 2025-07-30 14:30 CEST
**Command**: date "+%Y-%m-%d %H:%M %Z"
**When**: At session start
**Why**: Track when work happened

### 📋 Progress Log
- **14:30** - Session started
  **Command**: date '+%H:%M'
  **When**: For each entry
  **Why**: Track work progression
```

### Work Tracking
```bash
# Folder creation
mkdir "$(date +%Y%m%d)-feature-ACTIVE"
# Result: 20250730-feature-ACTIVE

**When**: Creating work folder
**Why**: Chronological organization
```

### Code Comments
```javascript
// TODO(2025-08-15): Remove after migration
// DEPRECATED(2025-07-30): Use newFunction instead
// FIXME(john, 2025-07-30): Critical bug found

**When**: Time-sensitive TODOs
**Why**: Track deadlines and urgency
```

### Git Commits
```bash
gac "fix: resolved issue found at $(date '+%Y-%m-%d %H:%M')"

**When**: Referencing specific time
**Why**: Audit trail for debugging
```

### Test Execution
```javascript
console.log(`Test started at: ${new Date().toISOString()}`);
// Test execution
console.log(`Test completed at: ${new Date().toISOString()}`);

**When**: Performance testing
**Why**: Measure execution time
```

## Timestamp Precision Requirements

### High Precision (Milliseconds)
```javascript
// Performance metrics
const start = performance.now();
// ... operation ...
const end = performance.now();
console.log(`Operation took ${end - start}ms`);

**Use for**:
- Performance measurements
- Benchmarking
- Race condition debugging
```

### Medium Precision (Seconds)
```bash
# Log entries
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Operation completed"

**Use for**:
- Log files
- Audit trails  
- Transaction records
```

### Low Precision (Minutes)
```markdown
- **14:30** - Meeting started
- **15:45** - Decision reached

**Use for**:
- Human-readable logs
- Meeting notes
- Progress tracking
```

### Date Only
```markdown
**Started**: 2025-07-30
**Completed**: 2025-08-02

**Use for**:
- Project milestones
- Version releases
- Daily summaries
```

## Examples by File Type

### sessions/
```markdown
## Session: 2025-07-30 14:30 CEST  # Full timestamp

### 📋 Progress Log
- **14:30** - Started implementation  # Time only
- **15:15** - Completed first module  # Time only
- **16:00** - Session ended           # Time only
```

### TRACKER.md
```markdown
**Started**: 2025-07-30        # Date only
**Last Updated**: 2025-07-30   # Date only

## Progress Log
- **2025-07-30 14:30**: Started work  # Date + time
- **2025-07-30 15:45**: Checkpoint    # Date + time
```

### CHANGELOG.md
```markdown
## [1.2.0] - 2025-07-30  # Date only

### Added
- New feature (implemented 14:30-16:00)  # Time range
```

### Memory Files
```
session_2025-07-30_template_migration.md  # Date in filename

# Content
**Session Date**: 2025-07-30 14:30 CEST  # Full timestamp
**Duration**: 14:30 - 17:00              # Time range
```

## Timezone Considerations

### When to Include Timezone
```markdown
# Always include for:
- Session starts: "2025-07-30 14:30 CEST"
- Meeting times: "Call at 10:00 PST"
- Deadline specifications: "Due by 23:59 UTC"
- International coordination: "Deploy at 00:00 UTC"

# Optional for:
- Local progress logs (timezone implied)
- Internal documentation (team in same zone)
```

### When to Use UTC
```javascript
// API responses
{
  "timestamp": "2025-07-30T12:30:00Z",  // Always UTC
  "created_at": "2025-07-30T12:30:00Z"
}

// Server logs
console.log(`[${new Date().toISOString()}] Server started`);
// Output: [2025-07-30T12:30:00.000Z] Server started
```

## Anti-Patterns

### ❌ Don't Do This
```markdown
# Vague timestamps
"Updated recently"
"Sometime yesterday"
"Last week"

# Inconsistent formats in same file
- 14:30 - Entry one
- 2:45 PM - Entry two  # Different format
- 15.00 - Entry three  # Different separator

# Missing timestamps where needed
## Session: [No timestamp]  # Always need timestamp

# Unnecessary timestamps
const PI = 3.14159;  // Created 2025-07-30  # Not needed
```

### ✅ Do This Instead
```markdown
# Specific timestamps
"Updated 2025-07-30 14:30"
"2025-07-29 16:00"
"2025-07-23 09:00"

# Consistent format throughout
- **14:30** - Entry one
- **14:45** - Entry two
- **15:00** - Entry three

# Timestamps where required
## Session: 2025-07-30 14:30 CEST

# No unnecessary timestamps
const PI = 3.14159;  // Mathematical constant
```

## Special Patterns

### Duration Tracking
```markdown
**Start**: 2025-07-30 14:30
**End**: 2025-07-30 17:00
**Duration**: 2.5 hours

# Or inline
Task completed (14:30-17:00, 2.5 hours)
```

### Relative Timestamps
```javascript
// For user-facing displays
function getRelativeTime(date) {
  // Returns: "2 hours ago", "yesterday", "last week"
}

// But store absolute time
const created = new Date().toISOString();
```

### Batch Operations
```bash
# Timestamp multiple files
for file in *.log; do
  mv "$file" "$(date +%Y%m%d)_$file"
done
```

## Decision Tree

```
Need a timestamp?
├── Is it for documentation?
│   ├── Session/Progress? → YES (required)
│   └── General docs? → MAYBE (if time-sensitive)
├── Is it for tracking?
│   ├── Work/Tasks? → YES (required)
│   └── Changes? → YES (required)
├── Is it for code?
│   ├── TODO/FIXME? → MAYBE (if deadline)
│   └── Regular code? → NO (not needed)
└── Is it for debugging?
    └── Logs/Errors? → YES (required)
```

## Rationale

### Why These Patterns

1. **Traceability**: Know when things happened
2. **Debugging**: Correlate events with issues
3. **Accountability**: Track work and decisions
4. **Coordination**: Sync across timezones
5. **Automation**: Enable time-based operations

### Benefits
- **Clear History**: Chronological record of events
- **Easy Debugging**: Timestamps aid troubleshooting
- **Better Planning**: Accurate time tracking
- **Audit Trail**: Complete record for compliance
- **Team Coordination**: Everyone knows the timeline