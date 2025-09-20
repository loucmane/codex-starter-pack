---
id: update-tracker
name: Update Tracker
role: trigger
domain: workflow
stability: stable
triggers:
  - "update progress"
  - "log work done"
  - "record status"
dependencies: []
tools:
  - Edit
version: 1.0.0
---

#### Handler: update-tracker {#update-tracker}
**Triggers**: "update progress", "log work done", "record status"
**Target Pattern**: Progress information
**Pre-conditions**: 
- Work folder exists
- Progress to record
**Process**:
1. Open TRACKER.md
2. Find Progress Log section
3. Add timestamped entry
4. Update Current State
5. Adjust Next Steps
**Success**: Progress recorded
**Failure**: No work folder found
**Examples**:
- "update progress" → Auto-summary
- "log that we finished X" → Specific entry