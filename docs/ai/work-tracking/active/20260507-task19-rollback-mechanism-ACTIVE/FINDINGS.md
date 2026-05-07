# Findings

- 2026-05-07 — Task 10 already provides reference-fix rollback through `scripts/template-ssot-scanner/apply_reference_fixes.py`; Task 19 should not duplicate that surface.
- 2026-05-07 — The remaining rollback gap is a cross-workflow checkpoint manifest that captures Git, Taskmaster, session, plan, work-tracking, and Serena state before risky operations.
- 2026-05-07 — The first live checkpoint exposed that `git status --short` output must preserve leading spaces; `scripts/codex-task` now uses newline-only trimming so porcelain status fields and hidden `.taskmaster` paths remain intact.
