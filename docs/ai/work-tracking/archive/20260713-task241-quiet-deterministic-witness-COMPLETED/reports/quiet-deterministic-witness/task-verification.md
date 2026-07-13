# Task 241 Verification Evidence

**Status:** EXACT-HEAD LOCAL VERIFICATION AND DOGFOOD PASSED — hosted CI pending

## Implemented Contract

- Stable semantic classes and process exits: `pass=0`, `fail=1`,
  `unsupported=2`, and `not_derivable_in_ci=0`.
- Deterministic failures take precedence over incomplete CI evidence.
- Local ledger reads are read-only and filter repository, branch, and canonical
  worktree, retaining null attribution only for legacy compatibility.
- Verification requires an explicit commit that resolves to exact current HEAD;
  timestamps never substitute for commit identity.
- NUL-delimited rename-aware diff accounting retains every old/new path.
- Test deletion and test-to-source renames fail; staged and unstaged done flips fail.
- Complete JSON and PR-ready Markdown artifacts retain all evidence while default
  rendering remains one screen and routes through Task 238 budgets.
- Boundary events retain the semantic class, process exit, and both artifact paths.

## Passing Local Evidence

- Pre-commit focused witness/output/capsule matrix: **45 passed**.
- Pre-commit witness plus generated legacy projection matrix: **56 passed**.
- Installer, distribution, autonomous-delivery, delivery-policy, passive-ledger,
  legacy-projection, output-budget, and witness compatibility matrix:
  **301 passed, 3 opt-in certification/wheel smokes skipped** at signed commit
  `9fd71b5734c9ada5cea48942ad5f65d6ab588746`.
- Exact registered `codex:tests` gate (`python3 -m pytest tests/ -q`):
  **1,772 passed, 4 documented opt-in certification/wheel smokes skipped** in
  **300.36 seconds** at the same immutable HEAD. The sandbox-compatible run used
  an isolated `TMPDIR` plus `GIT_CEILING_DIRECTORIES` so tests that require a
  non-Git temporary directory retained their intended premise without changing
  source or test selection.
- Exact-HEAD focused witness/legacy boundary matrix: **40 passed**.
- Ruff lint: all scoped Python files passed.
- Ruff format: all scoped Python files passed.
- Live/package `witness_lib.py` byte parity passed.
- Signed implementation commit and GPG signature verified.
- `git diff --check` passed at the implementation checkpoint.

## Exact-HEAD Witness Dogfood

- The first canonical-store run intentionally failed with process exit `1` only
  because the Remote Control sandbox can read but cannot append to
  `/home/loucmane/.local/state/aegis/.../ledger.db`. It still proved the bounded
  failure surface: **17 lines / 796 bytes**, **14.36 seconds**, 58/58 diff paths
  accounted, no test escalation, and complete JSON/Markdown artifacts.
- A factual PostToolUse payload for the successful registered test gate was then
  passed through Aegis's real passive recorder using an isolated out-of-worktree
  dogfood store. Event `9b5e1560ce944dc083a156177e2cd963` retained the
  repository, branch, worktree, full HEAD, `codex:tests`, command, duration, and
  passing exit class.
- The real source CLI witness against that store passed with process exit `0` in
  **0.18 seconds**. Default stdout was **17 lines / 797 bytes**; all 58 diff paths,
  exact-HEAD verification, task-flip containment, and test-deletion checks passed.
- Complete artifacts were written as `.aegis/reports/witness-report.json`
  (**31,826 bytes**) and `.aegis/reports/delivery-report.md` (**7,783 bytes**).
  The boundary event and generated legacy S:W:H:E projection were recorded.

## Honest Local Limitations

1. The canonical shared ledger is read-only in this Remote Control permission
   profile. The isolated store is deterministic fixture evidence, not a replacement
   production store and not a claim that canonical capture occurred.
2. Four release certification/wheel/MCP smoke tests remain deliberately opt-in and
   must be exercised by their dedicated certification paths, not silently counted.
3. Hosted CI remains authoritative for its own checkout-location premise, Black,
   Python matrix, source guard, and delivery-policy checks.

## Still Required Before Delivery

- refresh the tracked plan, tracker, session, handoff, and Taskmaster terminal state;
- run final Taskmaster, plan, audit, source guard, and source-worktree witness checks;
- publish the exact terminal head and pass hosted CI; and
- preserve rollback and clean-working-tree evidence through source closeout.
