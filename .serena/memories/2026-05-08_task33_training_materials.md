# Task 33 - Training Materials

Date: 2026-05-08
Branch: feat/task-33-training-materials
Active work tracking: docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/
Session: sessions/2026/05/2026-05-08-009-task33-training-materials.md
Plan: plans/2026-05-08-task33-training-materials.md

## Scope Decision
Task 33 historical wording referenced videos, office hours, surveys, and broad training execution. Scope reconciliation found the current repo gap is narrower and repo-native: current onboarding/training for the portable Codex foundation and Claude runtime adapter, plus guide navigation cleanup.

## Implementation
- Added templates/guides/training/foundation-onboarding.md with learning path, evidence/gate rules, hands-on exercises, completion checklist, and feedback guidance.
- Replaced stale templates/guides/index.md navigation with current links to foundation, Taskmaster, session/work-tracking, guide, and Claude runtime references.
- Added tests/meta_workflow_guard/test_training_materials.py to verify guide links resolve and training sections/commands are present.

## Evidence So Far
- Focused training test: 4 passed.
- Training/metadata guard selection: 22 passed.
- Full pytest: 338 passed.

## Next Steps
Finish Task 33 closeout: record Serena memory in tracker/session, mark Taskmaster 33.2 and 33 done, regenerate only Task 33 file, run final health/plan-sync/work-tracking-audit/guard/diff-check evidence, commit, push, PR, merge, then archive work tracking post-merge.