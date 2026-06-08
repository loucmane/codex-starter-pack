# Task 180 Observation Artifact Collection Kickoff

Task 180 was opened on 2026-06-08 after HP-Coach dogfood exposed an Aegis observation cleanup catch-22: browser/screenshot tooling creates repo-local artifacts, `aegis observe stop` refuses dirty state, and observation mode blocks raw cleanup commands such as `rm` while still active. The intended fix is a sanctioned `aegis observe stop --collect-artifacts` path that collects only known newly-created observation artifacts into `.aegis/reports/observations/<observation-id>/artifacts/` while preserving fail-closed behavior for source, Taskmaster, protected, pre-existing, symlink-escaping, or unknown changes.

Branch: `feat/task-180-observation-artifact-collection`.
Active tracker: `docs/ai/work-tracking/active/20260608-task180-observation-artifact-collection-ACTIVE/`.
Plan: `plans/2026-06-08-task180-observation-artifact-collection.md`.
Taskmaster task: 180, in-progress.