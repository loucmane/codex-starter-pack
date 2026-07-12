# Task 237 Make Managed Agent Guidance Truthful And Mode-Aware – Handoff Summary

## Current State

- Task 237 implementation is complete on `feat/task-237-mode-aware-guidance`.
- Taskmaster Task 237 is done again after PR #259's fresh Codex install idempotence correction.
- The correction passes the formerly failing fixture and the full CI-equivalent local suite:
  1,755 passed, four opt-in distribution smokes skipped.
- Canonical and packaged installers are byte-identical.
- Combined regression result: 225 passed, 2 opt-in distribution smokes skipped.
- Live Blog update preview is safe; isolated Blog advisory apply and second-run idempotence pass.
- Enforcement runtime behavior is unchanged.
- Post-`done` readiness reports the documented Task 244 source-checkout compatibility BLOCKED
  state; do not fabricate installed Aegis state or remove the completed tracker to hide it.

## Next Steps

1. Push the CI-fix commit to PR #259.
2. Watch the new exact-head checks, mark the PR ready, and merge only after every required check
   passes.
3. After merge and a clean Blog task boundary, update Blog and record one real orientation
   canary confirming agents no longer apologize for skipped strict ceremony.

## Primary Evidence

- `reports/mode-aware-agent-guidance/task-verification.md`
- `designs/mode-aware-guidance-contract.md`
- `scripts/_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`
- Archived on 2026-07-11 22:59 CEST — Folder moved to archive and tracker marked COMPLETED.
