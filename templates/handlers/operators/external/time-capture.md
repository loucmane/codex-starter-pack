---
id: time-capture
name: Time Capture
role: operator
domain: external
stability: stable
triggers:
  - "timestamp"
  - "date"
  - "current time"
  - "log entry"
  - "now"
dependencies: []
tools:
  - date
version: 1.0.0
---

#### Pattern: time-capture {#time-capture}
**Triggers**: timestamp, date, "current time", "log entry", now
**Pre-conditions**: Time reference needed
**Process**:
1. Execute: `date "+%Y-%m-%d %H:%M %Z"`
2. Immediately record the command as an S:W:H:E entry in the active session (guard requirement)
3. Insert the timestamp where needed; never type manually or reuse stale values
**Success**: Accurate timestamp used
**Failure**: N/A (command always works)
**Examples**:
- "Add timestamp" → 2025-07-13 14:45 CEST
- "Log current time" → Exact system time
