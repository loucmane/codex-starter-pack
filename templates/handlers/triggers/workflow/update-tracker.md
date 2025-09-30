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
1. Open TRACKER.md (ensure latest plan-step-scope is complete).
2. Run `date "+%Y-%m-%d %H:%M %Z"` and log the command in the active session before editing.
3. Append a new Progress Log entry with the recorded timestamp. Entries must be in chronological order; do not insert in the middle.
4. Update Current State (replace entire section) and Next Steps as needed.
5. Save changes and run `python3 scripts/codex-guard validate --include-untracked` before committing.
**Success**: Progress recorded
**Failure**: No work folder found
**Examples**:
- "update progress" → Auto-summary
- "log that we finished X" → Specific entry
