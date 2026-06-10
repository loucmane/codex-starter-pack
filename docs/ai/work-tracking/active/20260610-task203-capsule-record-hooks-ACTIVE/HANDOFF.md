# Task 203 Capsule PR-1b: async record hooks – Handoff Summary

## Current State
- PR-1b implemented and verified: recorder live in the codex repo (events from both the
  running session via hot-reload and a fresh headless session), full suite 1216 passed /
  4 env-gated skips, evidence under reports/capsule-record-hooks/.
- Real hook payload fixtures committed under tests/fixtures/hook_payloads/ (8 event
  types, subagent attribution included).
- Spec-revision finding: exec-form hook args do NOT expand $CLAUDE_PROJECT_DIR on CLI
  2.1.170 — shipped shell-form + async instead (async is the load-bearing property).

## Next Steps
- Push feat/task-203-capsule-record-hooks, open the PR, wait for CI, explicit owner
  approval before merge.
- After merge: HP-Coach rollout via aegis plan-install + aegis install --apply there
  (spec section 1.1 — its installed gate_lib drifts from assets, so the upgrade run is
  required regardless), then watch events appear during normal product work.
- Then PR-1c (task 204): gate-decisions dual-write to the ledger with JSONL parity.
