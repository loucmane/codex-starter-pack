# Task 249 Fix pre-adapter Codex manifest update migration – Handoff Summary

## Current State
- The installer and packaged installer are byte-identical and use install-before-runtime
  sequencing for `project_update --apply`; the implementation merged through PR #275 at
  exact reviewed head `d3cbed1f6712a77f15329dee155c3025f67e41c9` as
  `d7ffce5eff8df92d08def1e4e2b7aeef2860a81d`.
- Deterministic regressions cover Codex-only and multi-agent legacy manifests, final-schema
  validity, idempotence, direct-runtime strictness, and divergent-hook refusal before writes.
- Pre-merge and exact-merge-SHA Python 3.11/3.12 CI, witness, Codex Guard, Meta Workflow
  Guard, Taskmaster health, plan sync, audit, source guard, parity, and diff checks pass.
- Taskmaster Task 249 is done and its evidence is terminal. The reviewed and merged trees
  are identical; primary `main` is synchronized while unrelated local drift is preserved.
- A disposable Blog Task 40 snapshot upgraded successfully and passed all 42 strict checks.
- Live Blog remains untouched because Task 40 is active and `.codex/hooks.json` requires
  attended manual review.

## Next Steps
- At a safe Blog checkpoint, rerun preview; preserve the operator hook until the owner
  explicitly chooses the managed candidate, then stop at `/hooks` exact-hash trust review.
- Archived on 2026-07-14 00:16 CEST — Folder moved to archive and tracker marked COMPLETED.
