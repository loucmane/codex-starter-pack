# Findings

- 2026-07-13 — The Remote Control sandbox can read but not append to the canonical
  out-of-worktree ledger. The recorder correctly degraded without blocking; an
  isolated store proved exact-HEAD witness behavior without claiming canonical
  capture.



## Progress Log

- **2026-07-13 14:34** — [S:20260713|W:task241-quiet-deterministic-witness|H:docs/findings|E:.claude/scripts/witness_lib.py] Baseline witness truncates artifact diff paths, accepts timestamp-only verification, filters repository/branch but not worktree, cannot distinguish an empty ledger from an unavailable ledger, and emits no PR-ready Markdown artifact.
- **2026-07-13 15:17** — [S:20260713|W:task241-quiet-deterministic-witness|H:docs/findings|E:docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/reports/quiet-deterministic-witness/task-verification.md] Local full-suite exceptions are environmental and remain unclaimed: restricted-network editable installs, the known /tmp target premise, one unrelated stdio MCP stall, and the cross-worktree Black stall; hosted CI is required.
- **2026-07-13 16:41** — [S:20260713|W:task241-quiet-deterministic-witness|H:remote-control+dogfood|E:docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/reports/quiet-deterministic-witness/task-verification.md] Resolved the earlier network and `/tmp` test premises with enabled network plus an isolated temporary Git ceiling; retained canonical-ledger write denial as the sole local capture limitation instead of silently substituting stores.
- **2026-07-14 16:45** — [S:20260714|W:task241-quiet-deterministic-witness|H:git:merge-main|E:.claude/scripts/witness_lib.py] A non-rewriting merge of current `main` can preserve all later Tasks 247–251 while leaving Task 241's semantic delta limited to the quiet witness runtime, CLI, contracts, regressions, and its own lifecycle evidence; live and packaged witness bytes remain identical.
