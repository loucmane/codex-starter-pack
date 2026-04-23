# Task 93 Compaction Detection Kickoff - 2026-04-23

## Current State
- Branch: `feat/task-93-remediate-compaction-detection`.
- Taskmaster Task 93 is `in-progress`.
- Subtasks `93.1` and `93.2` are done after the scope audit and rewrite-vs-retire decision.
- Active work tracking: `docs/ai/work-tracking/active/20260423-task93-remediate-compaction-detection-ACTIVE/`.
- Current session: `sessions/2026/04/2026-04-23-002-task93-compaction-detection.md`.
- Current plan: `plans/2026-04-23-task93-remediate-compaction-detection.md`.

## Key Decision
Retire `templates/behaviors/session/compaction-detection.md` as executable behavior instead of rewriting it as another active source. Keep canonical compaction guidance in `compaction-preparation.md`, `prepare-compaction.md`, and `workflows/session/compaction.md`; keep session-end guidance in `session-end.md` and `end-session.md`.

## Scope Audit Findings
- `compaction-detection.md` is deprecated but still contains blocking session-end and full `gac` guidance.
- `templates/BEHAVIORS.md` still combines session-end and compaction triggers into a single flow.
- `scripts/codex-guard` still includes the deprecated compaction detection file in `GAC_SUMMARY_DOCS`, which keeps it canonical for enforcement.

## Next Steps
1. Fix baseline guard setup gaps: tracker needs explicit date command entry, chronological ordering, and this Serena memory logged.
2. Run plan sync, work-tracking audit, and `python3 scripts/codex-guard validate --include-untracked` again.
3. Implement Task 93 behavior retirement and guard/test updates.
