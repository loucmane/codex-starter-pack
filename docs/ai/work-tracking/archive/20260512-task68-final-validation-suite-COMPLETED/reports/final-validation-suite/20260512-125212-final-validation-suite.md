# Final Validation Suite Runbook

- Label: final-validation-suite
- Created at: 2026-05-12T12:52:12+02:00
- Mode: final-validation-suite
- Executes commands: True
- Status: failed
- Valid: False

## Current State

- Branch: feat/task-68-final-validation-suite
- HEAD: 80dccaf4ff616c31a70174d471dbd9d44d45ad9c
- Dirty status entries: 11
- Current session: sessions/2026/05/2026-05-12-001-task68-final-validation-suite.md
- Current plan: plans/2026-05-12-task68-final-validation-suite.md
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE']

## Requirement Coverage

| Requirement | Covered By |
| --- | --- |
| Validation checklist automation | validation final-suite manifest, validation final-suite runbook |
| Reference integrity checks | scanner suite, automatic reference-fix gate |
| Security validation | scanner security validator, Phase 0 validation report |
| Performance validation | template performance harness |
| Cost validation | template cost report |
| Compatibility validation | agent compatibility report |
| Validation report generation | report generate --kind all, final validation report outputs |
| Regression tests | pytest suite |
| Validation sign-off workflow | final validation runbook sign-off checklist |

## Validation Checks

| Check | Category | Status | Evidence | Command |
| --- | --- | --- | --- | --- |
| Current Git status | workflow-state | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/01-git-status.txt | `git status --short --branch` |
| Taskmaster graph health | workflow-state | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/02-taskmaster-health.txt | `python3 scripts/codex-task taskmaster health` |
| Plan and tracker sync | workflow-state | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/03-plan-sync.txt | `python3 scripts/codex-task plan sync` |
| Work-tracking audit | workflow-state | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/04-work-tracking-audit.txt | `python3 scripts/codex-task work-tracking audit` |
| Codex guard validation | guard | failed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/05-codex-guard.txt | `python3 scripts/codex-guard validate --include-untracked` |
| Template drift check | guard | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/06-template-drift.txt | `python3 scripts/codex-guard drift-check --strict` |
| Scanner validation suite | scanner | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/07-scanner-suite.txt | `python3 scripts/template-ssot-scanner/run_all_scanners.py --profile ci` |
| Automatic reference-fix gate | scanner | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/08-reference-fix-gate.txt | `python3 scripts/template-ssot-scanner/apply_reference_fixes.py --dry-run --fail-on-changes --log-file docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/reference-fix-gate.json` |
| Static validation report pipeline | reports | failed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/09-static-report-pipeline.txt | `python3 scripts/codex-task report generate --kind all --strict-drift --strict-monitoring --strict-phase0 --strict-performance --strict-cost` |
| Agent compatibility validation | compatibility | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/10-agent-compatibility.txt | `python3 scripts/codex-task agent compatibility-report --strict --report-file docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/agent-compatibility.json --runbook-file docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/agent-compatibility.md` |
| Python regression tests | tests | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/11-pytest.txt | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py` |
| Patch whitespace check | git | passed | docs/ai/work-tracking/active/20260512-task68-final-validation-suite-ACTIVE/reports/final-validation-suite/20260512-125212-final-validation-suite-evidence/12-diff-check.txt | `git diff --check` |

## Sign-Off Checklist

- [ ] All required final-suite checks passed or have an explicit documented waiver.
- [ ] Final validation JSON and Markdown runbook are stored in the task evidence folder.
- [ ] Plan, tracker, session, handoff, findings, decisions, and changelog reference the final evidence.
- [ ] Taskmaster status and generated task file are current.
- [ ] No policy-only validation gap is hidden by prose-only documentation.

## Non-Goals

- No standalone security, performance, cost, reference, or compatibility validator is created by this suite.
- No external service, repository setting, hosted dashboard, or approval workflow is modified.
- Dirty Git status is recorded as evidence; patch hygiene is enforced by git diff --check.

Validation command outputs are captured in the evidence files listed above.
