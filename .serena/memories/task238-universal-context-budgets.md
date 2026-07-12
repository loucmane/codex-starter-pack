# Task 238 — Universal Context Budgets

Date: 2026-07-12

Branch: `feat/task-238-universal-context-budgets`

## State

Implementation, local verification, implementation-head hosted CI, Taskmaster closeout,
and supported source archive are complete. Aegis CLI
status/update/next/doctor/verify/closeout/witness/replay output is bounded by default,
MCP applies the same budget to complete success/error envelopes, and standalone
readiness uses the same numeric modes. `--all --json` and MCP `detail=all` retain
intentional complete output. Detection, exit codes, state, and report artifacts remain
complete.

## Dogfood

HP-Fetcher had 4,151 advisory pending IDs. Final Task 238 status output was one line,
4,307 bytes, and 92.381 ms. Pending-file, aggregate state, pending-count, and Git
fingerprints were identical before and after; no repair, update, or drain ran.

## Verification

- focused renderer/readiness/replay/witness/capsule suites pass;
- complete MCP suite passes;
- complete installer suite passes except the existing opt-in certification skip;
- release/cross-project suites pass;
- isolated wheel CLI and MCP stdio smokes pass;
- Taskmaster health and dependency validation pass;
- managed readiness and installer source/package mirrors are byte-identical.

## Delivery

Draft PR #263 passed all seven hosted checks at exact signed implementation head
`5d8b95566cda37f325ef69d4543b49895998d0f7`. Taskmaster Task 238 is done and its
tracking bundle is archived at
`docs/ai/work-tracking/archive/20260712-task238-universal-context-budgets-COMPLETED/`.
The terminal lifecycle commit still needs exact-head hosted revalidation and protected
merge. Preserve unrelated `.codex`, `.agents`, and local `.aegis` drift. The next
program slice is Task 239, the diagnostic worktree/subagent capture audit; no PR-4
retirement is authorized.
