# Task 36 Implement Template Governance Board – Implementation Notes

## Planned Workstreams
- Scope reconciliation: completed in `designs/template-governance-scope-reconciliation.md`.
- Governance policy: add a repo-local `templates/metadata/template-governance-policy.json` for review classes, roles, approval model, escalation, notification evidence, and required evidence fields.
- Governance helper: add a non-mutating `scripts/template_governance.py` assessor that maps version/lifecycle/emergency signals to a required review path.
- Tests: add focused governance tests and run them with lifecycle/versioning regressions.

## Completed Implementation
- Added `templates/metadata/template-governance-policy.json` with routine, coordinated, breaking, and emergency review classes. Each class defines priority, required roles, approval guidance, escalation path, notification audiences, and required evidence.
- Added `scripts/template_governance.py` as a non-mutating governance assessor that:
  - loads policy from the configured templates root;
  - uses `scripts/template_versioning.py` classification when previous/current versions are supplied;
  - maps lifecycle transitions to review classes;
  - forces emergency review when requested;
  - chooses the highest-priority review class deterministically;
  - emits text or JSON review payloads without editing repository files.
- Added `tests/meta_workflow_guard/test_template_governance.py` for policy loading, validation errors, version-change mapping, lifecycle-transition precedence, emergency override, CLI output, and real-policy behavior.

## Initial Verification
- Focused governance/lifecycle/versioning regression: `30 passed`.

## Evidence
- `reports/template-governance-board/tests-2026-05-12-focused.txt` - governance, versioning, and lifecycle focused regression, `30 passed`.
- `reports/template-governance-board/tests-2026-05-12-meta-workflow.txt` - full meta-workflow regression, `243 passed`.
- `reports/template-governance-board/cli-2026-05-12-breaking.json` - JSON governance assessment showing a major version change requires breaking review.
- `reports/template-governance-board/cli-2026-05-12-emergency.txt` - text governance assessment showing emergency review overrides a routine patch change.
- `reports/template-governance-board/plan-sync-2026-05-12.txt` - plan/tracker sync evidence.
- `reports/template-governance-board/work-tracking-audit-2026-05-12.txt` - work-tracking audit evidence.
- `reports/template-governance-board/guard-2026-05-12.txt` - guard validation evidence.
- `reports/template-governance-board/taskmaster-health-2026-05-12.txt` - Taskmaster full-graph health evidence.
- `reports/template-governance-board/diff-check-2026-05-12.txt` - whitespace diff check evidence.
