# Task 245 completed-delivery guidance

- Branch: `feat/task-245-completed-delivery-guidance`
- Purpose: fix Blog Task 67 guidance ordering so proven merged delivery on synchronized `main` is terminal before historical branch-mismatch guidance, while preventing a stale Task 67 closeout report from controlling active Task 38.
- Implementation: `scripts/_aegis_installer.py` and its packaged mirror bind passed closeout reports to current-work identity and require GitHub merged PR truth, PR-base parity, merge-commit ancestry, matching upstream, and `0/0` ahead/behind proof.
- Replay fixture: `tests/fixtures/aegis/blog-task67-completed-delivery.json`.
- Verification so far: source/package `cmp` passed; incident-focused tests `8 passed`; full installer tests `129 passed, 1 skipped`; MCP/continuation suite `213 passed, 2 skipped`; Ruff passed; Taskmaster health passed; readiness is `READY | task=245`.
- Live Blog canary: current Task 38 evaluates as `authority=taskmaster:38`, `phase=closeout`, `state=closeout_required`; retained Task 67 evidence no longer arms delivery guidance.
- Remaining: complete repository/full-suite verification, store report, close out Taskmaster/Aegis, archive tracking, and deliver a task-only PR. Preserve unrelated `.codex`, `.agents`, and local `.aegis` drift.