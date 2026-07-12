# Decisions

- 2026-07-12 — Sampling is presentation-only. Complete payloads determine verdicts and
  exit codes; complete files remain the audit and automation source.
- 2026-07-12 — Plain `--json` is bounded because JSON is an agent input too. Complete
  structured stdout requires explicit `--all --json`; MCP uses `detail=all`.
- 2026-07-12 — Default and verbose use five- and twenty-item list samples. Exact totals
  and normalized collection paths remain available even when individual IDs are not.
- 2026-07-12 — MCP budgets apply to the whole success/error response and use compact
  metadata on the pretty-serialized wire. This closes the MCP bypass without changing
  FastMCP's structured response contract.
- 2026-07-12 — Readiness keeps a standalone adapter with the same constants because
  installed hooks cannot assume that the Python package is importable.
- 2026-07-12 — Do not modify witness detection or duplicate sampling inside
  `witness_lib.py`; keep its full report and bound only the final CLI output.
- 2026-07-12 — Preserve all legacy session/plan/tracker/handoff/S:W:H:E surfaces. This
  task improves coexistence and context cost; it authorizes no retirement.
- **2026-07-13 00:06** — [S:20260713|W:task238-universal-context-budgets|H:docs/decisions|E:docs/ai/work-tracking/active/20260712-task238-universal-context-budgets-ACTIVE/reports/universal-context-budgets/task-verification.md] Reuse the existing Task 238 ACTIVE folder and plan across the midnight continuation, mark the prior session complete, and keep hosted delivery as the only remaining verification stage; do not fabricate an installed Aegis manifest in the source checkout.
