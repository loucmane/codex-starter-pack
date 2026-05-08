# Task 33 Setup Training Materials – Implementation Notes

## Planned Workstreams
- Scope reconciliation: completed in `designs/training-materials-scope-reconciliation.md`.
- Training guide: add a current foundation onboarding guide for Codex/Claude workflow users.
- Navigation cleanup: update `templates/guides/index.md` so it points to current existing guides.
- Verification: add focused tests for training guide sections and guide-index links.

## Implemented Training Contract
- Added `templates/guides/training/foundation-onboarding.md` with a learning path, evidence/gate rules, hands-on exercises, a completion checklist, and feedback guidance.
- Replaced stale entries in `templates/guides/index.md` with current links to foundation, Taskmaster, session, work-tracking, guide, and Claude runtime references.
- Added `tests/meta_workflow_guard/test_training_materials.py` to prove the guide hub and training guide links resolve and the onboarding guide contains required training sections.

## Initial Verification
- Focused training tests: `4 passed`.
- Training plus guide metadata guard selection: `22 passed`.

## Evidence
- `reports/training-materials/tests-2026-05-08-training.txt` - focused training-material tests, `4 passed`.
- `reports/training-materials/tests-2026-05-08-training-guard.txt` - training plus metadata/guide guard selection, `22 passed`.
- `reports/training-materials/tests-2026-05-08-full-pytest.txt` - full pytest, `338 passed`.
- `reports/training-materials/taskmaster-health-2026-05-08.txt` - Taskmaster full-graph health.
- `reports/training-materials/plan-sync-2026-05-08.txt` - plan/tracker sync.
- `reports/training-materials/work-tracking-audit-2026-05-08.txt` - active work-tracking audit.
- `reports/training-materials/guard-2026-05-08.txt` - guard validation.
- `reports/training-materials/diff-check-2026-05-08.txt` - whitespace diff check.
- `.serena/memories/2026-05-08_task33_training_materials.md` - Serena continuity memory.
