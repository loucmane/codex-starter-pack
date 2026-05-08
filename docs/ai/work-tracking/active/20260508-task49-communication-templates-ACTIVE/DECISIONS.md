# Decisions

- 2026-05-08 — Implement Task 49 as a governed guide plus focused tests, not as external distribution-list automation. The current foundation communicates through repository artifacts: PR descriptions, session/tracker/handoff entries, Taskmaster status, guard/test evidence, and direct GitHub state.
- 2026-05-08 — Do not add a `.github/PULL_REQUEST_TEMPLATE*` in this task. A committed PR template would be useful later, but the smallest proven current-state gap is reusable communication payload guidance discoverable from the guide hub.
- 2026-05-08 — Do not manually edit `.taskmaster/tasks/tasks.json` or the generated parent task file to force updated parent details after `task-master update-task` failed. Preserve Taskmaster-managed files and rely on completed subtasks plus work-tracking evidence for the current-scope record.
