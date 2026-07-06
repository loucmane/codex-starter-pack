# Capsule Boundary Dogfood - 2026-07-06

Task: TM-228

Scope: acceptance dogfood for the capsule freshness and boundary-trigger model shipped in
TM-226/TM-227. This report records observed behavior first; implementation changes are only
in scope for concrete trigger bugs found during the pass.

## Baseline

- Branch: `feat/task-228-capsule-boundary-dogfood`
- HEAD at start: `5b591d3` (`feat: wire capsule boundary refresh triggers (#245)`)
- Focused capsule suite: `44 passed`
- Pre-orientation capsule status: stale
- Stale reasons included missing freshness snapshot from the older capsule runtime, branch
  change, HEAD change, Taskmaster hash change, brief config hash change, and worktree status
  change.

## Acceptance Matrix

| Boundary | Trigger | Expected | Observed | Result |
| --- | --- | --- | --- | --- |
| Orientation | `python3 -m aegis_foundation.cli next --target-dir .` | stale capsule refreshes with `compile_reason: orientation` | refreshed at `2026-07-06T15:41:09Z`; status became fresh | Pass |
| Capsule check | `python3 -m aegis_foundation.cli brief --target-dir . --check` | current capsule passes budget/canary/parse checks | `capsule check: ok` | Pass |
| Verification | `python3 -m aegis_foundation.cli verify --target-dir . --strict` | stale capsule refreshes with `compile_reason: verification` before verification result | refreshed with `compile_reason: verification`; strict verification then failed because the upstream source tree has no installed Aegis manifest | Pass for capsule trigger; expected environmental verify failure |
| Pre-delivery | `python3 -m aegis_foundation.cli witness --target-dir . --base origin/main --json` | stale capsule refreshes with `compile_reason: pre-delivery` before witness result | refreshed with `compile_reason: pre-delivery`; witness then failed `verification_at_head` because no `codex:tests` pass exists at uncommitted HEAD | Pass for capsule trigger; expected pre-commit witness failure |
| Task status | Hook recorder payload for `task-master set-status --id=228 --status=in-progress` | passive recorder refreshes with `compile_reason: task-status-change` | refreshed with `compile_reason: task-status-change` using temp ledger at `/tmp/aegis-task-228-state` | Pass |
| Post-merge | Hook recorder payload for `gh pr merge 245 --squash --delete-branch` | passive recorder refreshes with `compile_reason: post-merge` | refreshed with `compile_reason: post-merge` using temp ledger at `/tmp/aegis-task-228-state` | Pass |
| Session start | `gate_lib.py sessionstart` payload with `source=startup` | injected capsule renders to stdout and records `compile_reason: session-start` | stdout contained the computed capsule; status showed `compile_reason: session-start` | Pass |
| Session resume | `gate_lib.py sessionstart` payload with `source=resume` and `AEGIS_CAPSULE=on` | injected capsule renders to stdout and records `compile_reason: session-resume` | stdout contained the computed capsule; status showed `compile_reason: session-resume` | Pass |
| Risk register | Hook recorder payload for `.aegis/capsule/risk-seed.json` write | passive recorder refreshes with `compile_reason: risk-register-change` | refreshed with `compile_reason: risk-register-change` using temp ledger at `/tmp/aegis-task-228-state` | Pass |
| HP-Coach downstream | `/home/loucmane/dev/hpfetcher/.aegis/bin/aegis next --target-dir .` | installed shim sees upstream runtime and refreshes downstream capsule with `compile_reason: orientation` | refreshed HP-Coach capsule with `compile_reason: orientation`, `event_count: 11067`, `gate_decision_count: 5645`; status fresh when run with access to the real ledger path | Pass |

## Findings

- `aegis next` currently reports `not_installed (phase: bootstrap)` in the upstream source
  repo because this repo is not installed as an Aegis target. That guidance is expected for
  the package source tree and did not prevent the capsule refresh.
- `python3 -m aegis_foundation.cli verify --target-dir . --strict` fails strict verification
  for this repo with `Aegis manifest missing or invalid JSON` because the upstream source tree
  is not installed as an Aegis target. This is environmental for the strict verify path, not a
  capsule trigger bug.
- Dogfood exposed a freshness bug: hashing only `git status --porcelain` misses content edits
  after a file is already dirty or untracked. The fix is to include bounded content markers in
  the worktree freshness hash: git blob hashes for tracked dirty files and SHA-256 content
  hashes for untracked files under the 1 MB cap.
- The recorder-driven checks used `XDG_STATE_HOME=/tmp/aegis-task-228-state` to avoid writing
  dogfood events into the operator's persistent ledger while still exercising the real hook
  code path.
- HP-Coach's shim resolves `AEGIS_SOURCE_ROOT=/home/loucmane/codex` and therefore sees the
  current upstream runtime immediately. Its manifest metadata is stale, but the active source
  root is valid.
- HP-Coach ledger reads require access to the real out-of-worktree ledger under
  `~/.local/state/aegis/98edd9f1da147a59f44b3101c11e10cdf10909a8/ledger.db`. A sandboxed
  status probe without that access can report zero ledger events; the same status command with
  real ledger access reported the capsule fresh.

## Validation

- Focused capsule suite before the fix: `44 passed`
- Focused brief compiler module after the fix: `18 passed`
- Focused capsule suite after the fix: `46 passed`
- `python3 -m py_compile .claude/scripts/brief_lib.py aegis_foundation/assets/.claude/scripts/brief_lib.py`: pass
- `python3 scripts/codex-task taskmaster health`: OK
- `python3 scripts/codex-task work-tracking audit`: pass
- `python3 scripts/codex-guard validate --include-untracked`: pass
- `git diff --check`: pass
