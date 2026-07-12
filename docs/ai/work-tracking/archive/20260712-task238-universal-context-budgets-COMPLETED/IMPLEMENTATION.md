# Task 238 Enforce Universal Context Budgets Across Aegis Commands – Implementation Notes

## Planned Workstreams

### Shared presentation contract

- Added `aegis_foundation/output_budget.py` with default (60 lines / 8 KiB /
  five-item sample), verbose (120 lines / 32 KiB / twenty-item sample), and
  intentional all-detail modes.
- The renderer analyzes the complete payload before projection, aggregates normalized
  collection paths and recognized category fields, and records exact totals,
  truncation, artifacts, and one next action.
- Detection and exit-code decisions always consume the complete payload. Projection is
  the final stdout/MCP presentation step only.
- Bounded JSON is always valid and has a minimal fail-closed envelope if ordinary
  sampling still cannot satisfy the byte cap. Text keeps the command's leading verdict
  and reserves space for truncation, artifact, and next-action guidance.

### CLI and artifact integration

- Routed `status`, `update`, `next`, `doctor`, `verify`, `closeout`, `witness`, and
  `replay` through the shared renderer.
- Added mutually exclusive `--verbose` and `--all` flags. `--json` remains bounded;
  `--all --json` is the explicit complete structured output.
- Replay now writes the complete `aegis-replay-report.json` in its selected work
  directory before rendering stdout. Existing verify/update/witness/closeout artifacts
  remain complete and unchanged.
- Corrected legacy next/closeout wording so it no longer describes plain `--json` as
  complete output; source and packaged installer assets remain byte-identical.

### MCP response budgets

- Added `detail=default|verbose|all` to the MCP status, update, next, doctor, verify,
  closeout, and closeout-ready tools.
- The budget applies to the complete success/error envelope after FastMCP pretty JSON
  serialization. A compact MCP metadata adapter prevents transport indentation from
  turning a bounded one-line projection into more than 60 lines.
- Scalar compatibility fields remain present at every envelope level. Tests that
  intentionally inspect every operation/check now request `detail=all` explicitly.

### Standalone readiness and documentation

- Added the same numeric modes to the standalone readiness hook without requiring an
  import from the Aegis package in installed targets. Default output uses a head/tail,
  status-prioritized sample with exact READY/WARN/BLOCKED counts.
- Source and packaged readiness scripts remain byte-identical.
- Updated the invocation contract, packaged invocation contract, and usability roadmap
  to define CLI and MCP detail semantics.

### Verification and dogfood

- Added 0, 10, 3,500, and 100,000 event fixtures, high-cardinality category coverage,
  valid-JSON and hard-cap checks, text/JSON/all-mode checks, CLI routing checks, MCP
  wire-size checks, failed-report retention, readiness parity, and replay artifact
  retention.
- Ran HP-Fetcher status against 4,151 advisory pending events. Final output was one line
  and 4,307 bytes in 92.381 ms; pending, aggregate state, and Git fingerprints were
  identical before and after.

## Out of Scope Preserved

- No pending event was drained, repaired, or deleted.
- No detection rule, exit class, strict/advisory enforcement rule, legacy S:W:H:E
  surface, hash chain, sandbox mechanism, or PR-4 retirement decision changed.
- `witness_lib.py` remains the complete report producer; the CLI shared renderer owns
  its presentation budget, so no duplicate sampling logic was added to the managed
  witness asset.
