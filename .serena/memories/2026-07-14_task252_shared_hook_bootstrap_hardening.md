# Task 252 Shared Hook Bootstrap Hardening — 2026-07-14

## Scope

Task 252 removes the mutable Aegis source checkout as a shared Codex-hook bootstrap dependency.
It depends on Tasks 242, 248, and 249, and Task 243 now waits for its evidence.

## Confirmed Incident Evidence

- Repeated Stop failures attempted to open
  `/home/loucmane/codex/.claude/scripts/gate_lib.py` while that file was transiently absent.
- Current live and packaged gate libraries are present and byte-identical; no committed deletion
  explains the outage.
- The primary checkout's untracked `.codex/hooks.json` contains absolute source-root commands.
- Current generated hooks are target-root-relative and installed wrappers prefer the local
  `.aegis/bin/aegis` dispatcher.

## Safety Boundary

- Do not edit or stage the primary checkout's `.codex/config.toml`,
  `.codex/deep-work.config.toml`, `.codex/hooks.json`, local `.aegis/`, or `.agents/` drift.
- Do not mutate Blog or begin Taskmaster-to-Gas-Town migration.
- Unknown/custom hook definitions remain manual review; only exact known Aegis forms may migrate.
- PreToolUse remains fail-closed when policy is unavailable; passive hooks degrade once with a
  bounded diagnostic.

## Next Work

Implement the stable bootstrap and managed-update transaction in the isolated Task 252
worktree, add the multi-project and partial-runtime regression matrix, then run source/package,
focused, full-suite, guard, witness, and hosted-CI verification before delivery.
