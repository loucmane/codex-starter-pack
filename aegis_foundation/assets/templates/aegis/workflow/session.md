---
session_id: {{session_id}}
date: {{date}}
time: {{time_label}}
title: Task {{task_id}} - {{title}}
aegis_current_work: {{current_work_rel}}
---

## Session: {{date}} {{time_label}}
**AI Assistant**: Aegis-enabled agent
**Developer**: project owner
**Task**: Start Task {{task_id}} with Aegis kickoff and establish compliant session, plan, and work-tracking state for {{title}}.
**Task Source**: Aegis-native current work

### Session Validation
- [x] Runtime timestamp captured by Aegis kickoff (`{{timestamp_full}}`)
- [x] Git branch checked (`{{branch_current}}`)
- [x] Aegis current work created (`{{current_work_rel}}`)
- [x] Session pointer created (`sessions/current`)
- [x] Plan pointer created (`plans/current`)
- [x] Active work-tracking folder created (`{{work_rel}}`)

### Session Goals
- [x] Start a fresh Task {{task_id}} session on a task branch.
- [x] Scaffold Task {{task_id}} work tracking.
- [x] Repoint `sessions/current` and `plans/current` to Task {{task_id}}.
- [ ] Confirm task scope before implementation.
- [ ] Capture implementation and verification evidence before closeout.

### Starting Context
Task {{task_id}} was kicked off through Aegis. The project is now expected to use `{{current_work_rel}}`, `sessions/current`, `plans/current`, and the active work-tracking folder as the workflow authority. Taskmaster and Serena are optional integrations unless this task explicitly marks them required.

### Progress Log
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:aegis:kickoff|E:{{current_work_rel}}] Created Aegis-native current work state.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:sessions/current|E:{{session_rel}}] Created current session and repointed `sessions/current`.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:plans/current|E:{{plan_rel}}] Created current plan and repointed `plans/current`.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:work-tracking|E:{{tracker_rel}}] Created active work-tracking scaffold.
