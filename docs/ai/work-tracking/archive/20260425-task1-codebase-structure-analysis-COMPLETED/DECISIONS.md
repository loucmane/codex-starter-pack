# Decisions

- 2026-04-25 — Execute Task 1 as a current-state codebase analysis and Taskmaster reconciliation task, not as a literal replay of stale command examples.
- 2026-04-25 — Store generated working evidence under the active Task 1 reports folder and publish the synthesized final report at `.taskmaster/reports/codebase-analysis.md` so downstream Taskmaster tasks can depend on it.
- 2026-04-25 — Do not recreate obsolete root monolith files or missing one-off helper scripts unless the current analysis proves a durable replacement is needed.
- 2026-04-25 — Ignore generated scanner checkpoint/data/script outputs in git; keep durable scanner conclusions in Task 1 reports and preserve intentional scanner reports under `scripts/template-ssot-scanner/output/reports/`.
