# Task 16 Performance Testing Harness Kickoff

Date: 2026-05-10
Branch: feat/task-16-performance-testing-harness
Taskmaster: Task 16 in-progress; subtask 16.1 done; subtask 16.2 in-progress.

Scope decision:
- Do not implement stale greenfield benchmark wording literally.
- Implement Task 16 as a portable static performance harness grounded in the current foundation.
- Current foundation already has template metrics (Task 97), static monitoring (Task 17), Phase 0 validation (Task 25), scanner profiling/stat metadata (Task 45), and one-off Task 1 performance notes.
- Proven gap: no reusable report that measures core foundation operation durations, compares them with repo-local thresholds, classifies regressions against optional baselines, and publishes CI artifacts.

Implemented direction so far:
- Added scope reconciliation at docs/ai/work-tracking/active/20260510-task16-performance-testing-harness-ACTIVE/designs/performance-testing-scope-reconciliation.md.
- Added templates/metadata/template-performance-policy.json.
- Added scripts/template-performance-harness for policy-driven performance checks and Markdown/JSON reports.
- Added reports/template-performance/README.md.
- Extended scripts/_repo_structure.py with template_performance_policy_path and performance_report_dir.
- Started wiring scripts/codex-task report generate --kind performance|all and CI artifact generation.
- Added focused tests in tests/meta_workflow_guard/test_template_performance_harness.py and updated codex-task/repo-structure tests.

Verification so far:
- py_compile passed for scripts/template-performance-harness, scripts/_repo_structure.py, scripts/codex-task.
- Focused performance harness tests passed: 5 passed.
- Focused codex-task report/bootstrap tests passed: 4 passed.
- Repo-structure config tests passed with performance report/policy assertions.

Next steps:
- Finish docs/work-tracking updates for implementation.
- Run plan sync so guard sees plan/tracker parity.
- Run the performance harness and focused/full relevant tests.
- Capture final evidence under the active work-tracking report folder.
- Mark plan-step-implement and plan-step-verify complete only after guard/test/performance evidence is recorded.