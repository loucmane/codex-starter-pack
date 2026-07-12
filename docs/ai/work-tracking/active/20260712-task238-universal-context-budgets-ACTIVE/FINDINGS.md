# Findings

- 2026-07-12 — HP-Fetcher still has 4,151 advisory pending event IDs under
  `$.workflow_guidance.details.pending_event_ids`. The final bounded status response
  retained that exact count in 4,307 bytes instead of enumerating the IDs.
- 2026-07-12 — The HP-Fetcher status observation was genuinely read-only: pending-file,
  aggregate `.aegis/state`, pending-count, and Git-porcelain fingerprints were identical
  before and after. No purge, repair, update, or installed-target write was needed.
- 2026-07-12 — FastMCP pretty-serializes dictionaries. A one-line 1.6-KiB inner JSON
  projection became 116 wire lines, so the context budget must govern the complete MCP
  envelope after transport serialization rather than only the nested core report.
- 2026-07-12 — Existing MCP tests intentionally consumed complete operation and check
  arrays. Those consumers now use `detail=all`; bounded default tests independently pin
  exact totals and sample sizes.
- 2026-07-12 — HP-Fetcher's full status payload still contains strict-era pending-log
  guidance while enforcement is advisory. Task 238 does not rewrite workflow-state
  semantics; the safe default status next action is `aegis next`, and Task 243 already
  owns the explicit advisory-pending lifecycle evidence.
- 2026-07-12 — Opt-in wheel smoke initially failed because `uv` selected a read-only
  home cache. An isolated `/tmp` cache made the CLI wheel smoke pass; a temporary HOME
  plus the existing Python user-site path made the MCP stdio wheel smoke pass. This was
  environment isolation, not a product defect.
- 2026-07-13 — Dynamic source-closeout helper loading wrote `scripts/__pycache__` in a
  clean fixture, violating readiness's read-only contract. Readiness now temporarily
  sets `sys.dont_write_bytecode` around the import; source/package scripts remain
  identical and the clean-tree regression passes.
