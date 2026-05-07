# Decisions

- 2026-05-07 — Do not reinitialize Taskmaster for Task 12. Rationale: current repository evidence shows Taskmaster is installed, configured, and valid; reinitialization would be destructive/noisy and contradicts the documented "DO NOT RE-INITIALIZE" rule.
- 2026-05-07 — Implement `python3 scripts/codex-task taskmaster health` as the Task 12 current-state gap. Rationale: it gives agents a deterministic authoritative full-graph health report and documents the filtered-list warning caveat.
