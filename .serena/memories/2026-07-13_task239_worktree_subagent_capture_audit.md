# Task 239 — Worktree/Subagent Capture Audit

Task 239 is active on `feat/task-239-worktree-subagent-capture-audit`. It is a
diagnostic-only prerequisite to Task 240. The binding contract is
`docs/ai/work-tracking/active/20260713-task239-worktree-subagent-capture-audit-ACTIVE/designs/worktree-capture-audit-contract.md`.

The audit must distinguish pre-install commits, absent assets, unloaded hooks,
source-root failure, Git-common-dir store mismatch, missing attribution, parent-only
traffic, teardown loss, unsupported client surfaces, and successful capture. Checked-in
artifacts are secret-free and contain no raw prompts/transcripts or live absolute paths.

Do not modify ledger schema, recorder hooks, identity propagation, witness filtering, or
runtime policy in this task. Continue deterministic harness and fixture work even if a
live client is unavailable; record the live row honestly as unsupported/failed.

Preserve unrelated `.codex`, `.agents`, and local `.aegis` drift. Task 238 is merged as
PR #263 at `8bf1f1871ff259987fa1b8d66d875b1adaf8d99e`.
