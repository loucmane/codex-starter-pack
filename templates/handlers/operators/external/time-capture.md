---
id: time-capture
name: Time Capture
title: Time Capture
role: operator
type: operator
domain: external
stability: stable
status: stable
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

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/external/time-capture.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
