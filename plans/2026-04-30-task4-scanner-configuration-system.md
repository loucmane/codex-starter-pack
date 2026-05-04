---
session_id: 2026-04-30-001
work_context: task4-scanner-configuration-system
handler_target: templates/engine/core/portable-foundation-spec.md
task_ids: [4]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/
  - templates/engine/core/portable-foundation-spec.md
  - .taskmaster/tasks/task_004.txt
  - scripts/codex-task
plan_version: v1
emergency_bypass: false
---

# Plan - Task 4 Scanner Configuration System

## Header
- **Session ID (S)**: 2026-04-30-001
- **Work Context (W)**: task4-scanner-configuration-system
- **Handler Target (H)**: templates/engine/core/portable-foundation-spec.md
- **Task IDs**: 4
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/, templates/engine/core/portable-foundation-spec.md, .taskmaster/tasks/task_004.txt, scripts/codex-task
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Audit pending Taskmaster backlog and reconcile Task 4 with the portable foundation vision | docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/designs/backlog-alignment-audit.md | completed |
| plan-step-implement | Normalize pending task subtasks so future sessions execute current scope gates instead of stale migration subtasks | .taskmaster/tasks/tasks.json; .taskmaster/tasks/task_004.txt; .taskmaster/tasks/task_005.txt; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/IMPLEMENTATION.md | completed |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status | docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/TRACKER.md | completed |
| plan-step-config-schema | Complete Task 4.1 scanner YAML configuration schema contract, examples, docs, and tests | scripts/template-ssot-scanner/config/scanner_config.schema.json; scripts/template-ssot-scanner/config/examples/scanner_config.example.yaml; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/reports/scanner-configuration-system/tests-2026-04-30-config-schema.txt | completed |
| plan-step-config-loader | Complete Task 4.2 ConfigLoader singleton, lazy loading, default fallback, schema validation, hot reload detection, thread-safety tests, and performance coverage | scripts/template-ssot-scanner/config/config_loader.py; scripts/template-ssot-scanner/test_config_loader.py; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/reports/scanner-configuration-system/tests-2026-04-30-config-loader.txt | completed |
| plan-step-rule-engine | Complete Task 4.3 rule engine with priority taxonomy, rule definitions, threshold evaluation, custom execution, and performance coverage | scripts/template-ssot-scanner/config/rule_engine.py; scripts/template-ssot-scanner/test_rule_engine.py; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/reports/scanner-configuration-system/tests-2026-04-30-rule-engine.txt | completed |
| plan-step-pattern-matcher | Complete Task 4.4 allowlist/blocklist pattern matcher with glob/regex support, rule scoping, expiration handling, blocklist precedence, and performance coverage | scripts/template-ssot-scanner/config/pattern_matcher.py; scripts/template-ssot-scanner/test_pattern_matcher.py; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/reports/scanner-configuration-system/tests-2026-04-30-pattern-matcher.txt | completed |
| plan-step-inheritance | Complete Task 4.5 configuration inheritance, environment overlays, profiles, merge strategies, cycle detection, loader resolve helpers, and performance coverage | scripts/template-ssot-scanner/config/inheritance.py; scripts/template-ssot-scanner/test_inheritance.py; docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/reports/scanner-configuration-system/tests-2026-04-30-inheritance.txt | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/`
- `templates/engine/core/portable-foundation-spec.md`
- `.taskmaster/tasks/task_004.txt`
- `scripts/template-ssot-scanner/scanner_config.yaml`
- `scripts/template-ssot-scanner/config/`
- `scripts/template-ssot-scanner/test_config_loader.py`
- `scripts/template-ssot-scanner/test_rule_engine.py`
- `scripts/template-ssot-scanner/test_pattern_matcher.py`
- `scripts/template-ssot-scanner/test_inheritance.py`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `4`

## Branch Policy
- Working branch: `feat/task-4-scanner-configuration-system`

## Amendments & Versioning
- 2026-04-30 - Task 4 kickoff created via the guided wizard flow.
- 2026-04-30 - Corrected generated kickoff plan from wizard-placeholder wording to Taskmaster backlog alignment and scanner-configuration reconciliation scope.
- 2026-04-30 - Completed backlog normalization for Tasks 5-80 using Taskmaster CLI commands.
- 2026-04-30 - Verified backlog normalization with Taskmaster dependency validation, JSON parse check, work-tracking audit, plan sync, guard, and diff check.
- 2026-04-30 - Completed Task 4.1 by adding the scanner configuration JSON Schema, full example YAML, default config expansion, config docs, schema regression tests, and Taskmaster status evidence.
- 2026-04-30 - Completed Task 4.2 by adding the thread-safe ConfigLoader, singleton/lazy/default/reload behavior, loader docs, and 39-test scanner/config regression evidence.
- 2026-04-30 - Completed Task 4.3 by adding the RuleEngine, rule priority taxonomy, schema/config priority support, docs, and 60-test scanner/config regression evidence.
- 2026-04-30 - Completed Task 4.4 by adding PatternMatcher, allowlist/blocklist glob/regex matching, rule scoping, expiration handling, blocklist precedence, docs, and 81-test scanner/config regression evidence.
- 2026-04-30 - Completed Task 4.5 by adding ConfigResolver inheritance/profile/overlay resolution, merge strategy handling, loader resolve helpers, docs, and 95-test scanner/config regression evidence.
- 2026-04-30 - Ended the April 30 Task 4 session with Task 4 still active; next session should continue with Task 4.6.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Start a new dated session, then read `sessions/2026/04/2026-04-30-001-task4-scanner-configuration-system.md` and this plan.
  2. Review Taskmaster Task 4 and its subtasks.
  3. Review the backlog alignment audit before changing Taskmaster backlog state.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: Task 4.1, 4.2, 4.3, 4.4, 4.5, and 4.9 are complete. Continue with subtask 4.6 (`Add Schema Validation with jsonschema (Compile-Time and Runtime)`) before environment variable overrides or scanner dependency injection.

## Conflict & Scope Declaration
- Related plans: Tasks 81-102 foundation enforcement and portability work; Task 1 codebase analysis; Task 3 scanner reconciliation.
- Guard cross-check: backlog normalization must preserve Taskmaster-generated files, current session pointers, and work-tracking lifecycle compliance.

## Evidence Checklist
- Backlog alignment audit under `designs/`
- Taskmaster-generated task file changes
- Tracker/session entries for audit and normalization progress
- Stored guard, work-tracking audit, and Taskmaster status evidence
- Scanner configuration schema, example YAML, docs, and 27-test scanner validation report
- ConfigLoader implementation, docs, and 39-test scanner/config validation report
- RuleEngine implementation, priority taxonomy docs/config updates, and 60-test scanner/config validation report
- PatternMatcher implementation, allowlist/blocklist docs/config updates, and 81-test scanner/config validation report
- ConfigResolver inheritance/profile/overlay implementation, loader resolve helpers, docs, and 95-test scanner/config validation report

## Emergency Bypass Protocol
- No bypass authorized.
