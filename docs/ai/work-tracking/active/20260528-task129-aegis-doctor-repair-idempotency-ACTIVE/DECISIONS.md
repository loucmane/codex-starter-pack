# Decisions

- 2026-05-28 — Implement `aegis doctor` as a read-only diagnostic surface first. It should return structured checks, summary status, current-state classification, a repair plan, and next action.
- 2026-05-28 — Implement `aegis repair` as an explicit dry-run/apply surface. Dry-run must be read-only; apply must only execute deterministic low-risk actions and write a repair report.
- 2026-05-28 — Keep Taskmaster and Serena optional. Doctor should report them as optional absent unless current work explicitly marks them required.
- 2026-05-28 — Prefer replay-safe no-op semantics over hidden mutation: repeated install/start/log/verify/closeout should either return already-applied status, pass from completed state, or refuse with actionable next steps.
- 2026-05-29 — Treat Task 129 as complete after the second live Claude pass plus focused regression verification. The exact missing-surface backfill branch is protected by regression coverage, while the live workflow now completes without the first-run workaround.
