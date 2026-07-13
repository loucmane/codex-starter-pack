# Task 240 Make Worktree And Child-Agent Evidence First-Class – Implementation Notes

## Delivered Workstreams

- Added nullable `repository_identity`, `worktree_root`, `head`, and `parent_agent_id` event fields while keeping schema version `1` and legacy-row compatibility.
- Captured repository/worktree context once per ledger open and added explicit `AEGIS_AGENT_ID`, `AEGIS_AGENT_TYPE`, and `AEGIS_PARENT_AGENT_ID` adapter defaults; explicit event payloads still win.
- Normalized Codex `apply_patch`, nonzero PostToolUse outcomes, `SubagentStart`, `SubagentStop`, and session-root parent identity. Claude hook rows inherit the same repository context.
- Added repository/worktree/branch/HEAD/parent filters and made witness/replay consumption branch-safe by default.
- Added installer-owned `SessionStart`, `PostToolUse`, `SubagentStart`, and `SubagentStop` Codex hooks through structural merge/uninstall logic that preserves unrelated project configuration and refuses malformed JSON.
- Generalized reload markers to multiple agents so Claude and Codex prove activation independently.
- Added four required Codex mechanical gates and documented trust/reload behavior in the adapter contract and release matrix.
- Preserved byte-identical runtime/package mirrors and advisory enforcement.

## Acceptance Coverage

- Two child worktrees write concurrently through installed Codex hooks: one mutation and one failure.
- Six rows retain complete repository/worktree/branch/HEAD and agent context; every child-derived row retains its parent, including the inferred scope row.
- Four-process SQLite concurrency retains 100/100 rows; transient lock retry succeeds.
- Old SQLite rows remain readable before migration and preserved after additive migration.
- Sibling branch verification/replay evidence cannot satisfy the current branch.
- Both child worktrees are removed normally and 6/6 rows remain in the one shared store.
- Full measurements, unsupported surfaces, and the parent-only rollback are in `reports/worktree-child-evidence/task240-coverage-report.md`.
