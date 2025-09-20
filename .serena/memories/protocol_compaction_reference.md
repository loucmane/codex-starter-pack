# Compaction Protocol Reference

## Definition
- Compaction moves an ongoing session to a new chat window when context is nearing capacity (~85–90%).
- It does **not** start a new session; all work continues under the same session ID.
- Purpose: preserve continuity while respecting the model’s context limit.

## Triggers
1. User signal (e.g., “context is heavy, let’s start a new chat”).
2. System signal (slow responses or context warnings).
3. AI signal (noticing degraded output or template thresholds).

## Pre-Compaction Checklist
1. **Complete current subtask** – finish the workflow currently in progress.
2. **Update session log** – add progress entries noting context pressure and readiness.
3. **Create Serena memory** – `compaction_YYYY-MM-DD_<topic>` summarizing the checkpoint.
4. **Update work-tracking handoff** – document the current state and next steps.
5. **Save task state** – e.g., Task Master list if applicable.
6. **Snapshot Git status** – confirm clean state or note outstanding changes (optional but recommended).

## Compaction Checkpoint Message
```
📝 Compaction Checkpoint – Session YYYY-MM-DD-XYZ

### Current State
**Location**: /path/to/project
**Branch**: main
**Last Completed**: Specific achievement or milestone

### Work Completed in This Context
1. ✅ Completed task 1
2. ✅ Completed task 2
3. ✅ Completed task 3

### Critical Context
- Serena memory: compaction_YYYY-MM-DD_<topic>
- Work-tracking handoff updated (paths)
- Sessions log updated with compaction entries
- Todo/task list saved (if applicable)

### Stopping Point
Describe exact stopping point and outstanding items.

### To Resume in New Context
“Continue with <task> from <specific point>. See sessions/... and Serena memory for details.”

### Git Status
Include `git status --short` output if relevant.
```

## Recovery Procedure (Next Chat)
1. Run environment checks: `pwd`, `git status`, `git branch`, `date`.
2. Read latest session log entry (the checkpoint) and Serena compaction memory.
3. Review work-tracking handoff.
4. Reload task/todo state if used.
5. Confirm understanding of current task before proceeding.

## Critical Guidelines
- Never start from scratch—always recover using sessions + Serena memory.
- Avoid redoing completed work; resume exactly where the checkpoint indicates.
- Maintain the same workflow style (handlers, ULTRATHINK, S:W:H:E).
- Document resumption in session log once the new chat begins.
