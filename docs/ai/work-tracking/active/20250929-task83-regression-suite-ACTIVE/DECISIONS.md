# Task 83 Regression Suite – Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-09-29 | Treat registration regression suite as baseline guard for meta workflow assets | Ensures future template edits cannot drop orchestrator/pattern references without test failures |
| 2025-09-29 | Include guard integration regression suite targeting placeholder handlers | Validates guard enforcement on meta workflow gaps before Task 83 completion |
| 2025-09-29 | Snapshot regression evidence into work-tracking reports directory | Ensures long-term access even if root reports rotate or are cleaned.
| 2025-09-29 | Require Meta Workflow Guard CI workflow to run registration & integration suites on every PR | Guarantees enforcement regardless of local hooks and preserves artefacts for plan-step-verify |

