# Task 249 closeout — Codex hook update migration

- PR #275 merged through the normal protected exact-head squash path at
  `d7ffce5eff8df92d08def1e4e2b7aeef2860a81d`.
- Reviewed and merged trees are identical. Pre-merge and exact-merge-SHA Python 3.11/3.12
  matrices, witness, Codex Guard, and Meta Workflow Guard passed.
- Task 249 is done. The updater now migrates a reviewed managed install before strict
  runtime metadata refresh while direct runtime update remains strict.
- Divergent operator-owned `.codex/hooks.json` remains a manual-review refusal with no
  writes. Live Blog remains untouched until Task 40 reaches a safe checkpoint.
- Blog rollout must preserve the existing operator hook, use the supported update flow,
  and stop for owner review of the exact managed `/hooks` hashes.
