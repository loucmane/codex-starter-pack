# Decisions

- 2026-06-02 — Keep Task 146 strictly test/report/documentation-only. No reconcile mutation path, mutation flag, Taskmaster status mutation, git write, PR write, or MCP mutation is introduced.
- 2026-06-02 — Store corpus labels as pytest data next to fixture setup functions so labels are reviewed as code and recomputed during test execution.
- 2026-06-02 — Treat unlabelled observed findings as false positives. This prevents the corpus from silently ignoring newly emitted finding classes.
