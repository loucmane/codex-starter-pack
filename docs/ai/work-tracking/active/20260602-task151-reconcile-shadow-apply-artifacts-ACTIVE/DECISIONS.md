# Decisions

- 2026-06-02 — Keep Task 151 separate from Task 150. Task 150 remains the disabled primitive layer; Task 151 builds shadow artifact orchestration on top of it.
- 2026-06-02 — Allow Taskmaster mutation only in a detached sacrificial clone under `/tmp`; the governed repository must never be the subprocess working directory for `task-master set-status`.
- 2026-06-02 — Treat local shadow reports as a single declared output path and CI shadow reports as artifact-ready JSON with zero repo-file writes.
- 2026-06-02 — Keep the older Task 147 exact-delta fixture contract intact and let Task 151 add target-specific runtime paths, such as `.taskmaster/state.json`, when the actual baseline requires them.
- 2026-06-03 — Keep sacrificial cascade validation dependent on a real `task-master` CLI, but skip the three real-cascade tests when that CLI is absent in CI. Do not replace the real cascade with a fake in the production path.
