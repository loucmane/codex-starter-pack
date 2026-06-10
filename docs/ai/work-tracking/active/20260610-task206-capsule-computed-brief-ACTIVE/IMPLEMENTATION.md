# Task 206 Capsule PR-2a: computed aegis brief – Implementation Notes

## What was built
- `brief_lib.py` (assets + live mirror, stdlib-only): compile_capsule producing the 8
  computed fields at READ time — capsule_meta, repo_pose, delivery_state (gh with 800ms
  timeout + cached last-success from the out-of-worktree store; STALE-recheck on miss),
  verification_ledger (per package-x-gate from brief.json with EXPLICIT no-run-on-record
  and STALE-when-HEAD-moved), task_truth (status counts, ledger flips, the stranded-flip
  detector), governance (enforcement state + decision tallies since the last compile
  watermark), drift_sentinel, repo_hygiene (branch threshold + capped oversized-unignored
  scan) — plus seeded risk_register (risk-seed.json consumed exactly once).
- Drift sentinel v1: exactly 5 deterministic checks (CLAUDE.md task-count claim,
  STATUS.md claims, done-flips-vs-commits, plans/current pointer, uncommitted claimed
  done) with attempted/parsed/drift accounting — a crashing or unparseable checker IS
  drift; claim-absent parses clean. Canary at .aegis/capsule/canary.md auto-created and
  must ALWAYS flag; unflagged canary renders SENTINEL BROKEN, never silent zero-drift.
- Answer-shaped markdown render (branch? PRs? tests? task truth? known reds?) with
  as-of stamps and source citations; capsule files written to .aegis/capsule/current.md
  + current.json.
- CLI: aegis brief (markdown), --json, --check (budget 8000 chars + canary + parse
  counters; the only failing mode). Both classified read-only in gate_lib.
- brief_lib.py joins CLAUDE_SUPPORT_FILES (propagates on install/upgrade).

## Live acceptance (merge gate)
`aegis brief` on this repo, first run, matched independently-checked reality: correct
branch/commit/dirty counts, true task counts (192 done / 13 pending / 1 in-progress),
live governance mode + decision tallies (53 allow / 18 would_block), sentinel 6/6
parsed with the canary flagging.

## Verification
14 new tests (degraded non-git compile, verification absence/run/staleness, canary
always-flags + broken-canary failure, stranded-flip, CLAUDE.md claim check, broken
plans pointer, risk-seed once, governance tallies, --check budget, CLI json + capsule
files, gate classification, assets/live parity). Full suite 1261 passed.
