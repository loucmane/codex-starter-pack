---
session_id: {{session_id}}
date: {{date}}
time: {{time_label}}
title: {{work_label}} - {{title}}
aegis_current_work: {{current_work_rel}}
---

## Session: {{date}} {{time_label}}
**AI Assistant**: Aegis-enabled agent
**Developer**: project owner
**{{work_kind}}**: Start {{work_label}} with Aegis kickoff and establish compliant session, plan, and work-tracking state for {{title}}.
**Task Source**: Aegis-native current work

### Session Validation
- [x] Runtime timestamp captured by Aegis kickoff (`{{timestamp_full}}`)
- [x] Git branch checked (`{{branch_current}}`)
- [x] Aegis current work created (`{{current_work_rel}}`)
- [x] Session pointer created (`sessions/current`)
- [x] Plan pointer created (`plans/current`)
- [x] Active work-tracking folder created (`{{work_rel}}`)

### Session Goals
- [x] Start a fresh {{work_label}} session on {{branch_requirement}}.
- [x] Scaffold {{work_label}} work tracking.
- [x] Repoint `sessions/current` and `plans/current` to {{work_label}}.
- [ ] Confirm {{work_kind_lower}} scope before implementation.
- [ ] Capture implementation and verification evidence before closeout.

### Starting Context
{{work_label}} was kicked off through Aegis. The project is now expected to use `{{current_work_rel}}`, `sessions/current`, `plans/current`, and the active work-tracking folder as the workflow authority. {{integration_summary}}

### Progress Log
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:aegis:kickoff|E:{{current_work_rel}}] Created Aegis-native current work state.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:sessions/current|E:{{session_rel}}] Created current session and repointed `sessions/current`.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:plans/current|E:{{plan_rel}}] Created current plan and repointed `plans/current`.
- **[{{time_hm}}]** - [S:{{session_value}}|W:{{work_context}}|H:work-tracking|E:{{tracker_rel}}] Created active work-tracking scaffold.
