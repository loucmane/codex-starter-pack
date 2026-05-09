# Task 25 Phase 0 Scanner Validation

Date: 2026-05-09
Branch: feat/task-25-phase-0-scanner-validation
Active work tracking: docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/
Session: sessions/2026/05/2026-05-09-002-task25-phase-0-scanner-validation.md
Plan: plans/2026-05-09-task25-phase-0-scanner-validation.md

## Scope
Task 25 was reconciled from older wording into a current portable-foundation gate. Tasks 3/4/7/17 already provide scanner suite, scanner config, baseline outputs, and static monitoring. The remaining gap is one machine-readable Phase 0 scanner validation artifact that aggregates scanner output completeness, baseline metrics, security findings, and monitoring status.

## Implementation
Added scripts/template-phase0-validation. The script reads existing scanner output files without mutating them, validates required JSON wrappers/output format, verifies baseline metric availability, checks security error/warning counts, reports existing baseline findings, includes monitoring status, and writes latest.md/latest.json. Overall status is fail for error-level failed checks, warn for warning-only findings, pass when clean. Strict mode exits nonzero only on fail.

Wired the report into scripts/_repo_structure.py as phase0_validation_report_dir and into scripts/codex-task report generate with --kind phase0|all plus --scanner-data-dir, --phase0-monitoring-file, --phase0-report-dir, and --strict-phase0. CI guard workflows now generate and upload reports/phase0-scanner-validation/.

Added reports/phase0-scanner-validation/README.md and tests/meta_workflow_guard/test_phase0_scanner_validation.py. Updated focused codex-task/repo-structure tests for report wiring, bootstrap directories, sync assets, and configured roots.

## Evidence
Focused pytest stored at docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/tests-2026-05-09-focused.txt.
Full pytest stored at docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/tests-2026-05-09-full.txt.
Task-local generated Phase 0 sample report: docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/sample-phase0/latest.json.
Task-local codex-task phase0 report: docs/ai/work-tracking/active/20260509-task25-phase-0-scanner-validation-ACTIVE/reports/phase0-scanner-validation/codex-task-phase0/latest.json.

Current real scanner state is warn, not fail: required outputs exist, wrappers and baseline metrics pass, security error count is zero, monitoring passes, and warning-level security/baseline findings remain visible.

## Remaining
Complete final verification evidence: plan sync, work-tracking audit, codex guard, diff-check, taskmaster health, update tracker/session/handoff, mark Taskmaster 25.2 and parent 25 done if all pass, commit/push/PR/merge/archive using direct git/GitHub workflow.