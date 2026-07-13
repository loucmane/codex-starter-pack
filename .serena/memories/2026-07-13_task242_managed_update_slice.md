# Task 242 Managed-Update Slice

## Scope

Task 242 incrementally extracts managed-asset planning and update-safety logic from the
Aegis installer while preserving installed bytes, source/package parity, private caller
compatibility, fail-closed divergence handling, advisory enforcement, legacy workflow
scaffolding, and S:W:H:E narration.

## Delivered State

- `aegis_foundation.managed_update` is the authoritative stdlib-only core for managed
  assets, shared/client asset assembly, target materialization, prior-byte recovery,
  operation classification, and deterministic summaries.
- `scripts/_aegis_installer.py` remains the policy, renderer, I/O, report, apply, and
  rollback adapter and retains legacy private names.
- The source and packaged installers are byte-identical. The installer shrank from
  13,651 to 13,325 lines; the extracted core is 777 lines.
- Codex, HP-Fetcher, and Blog golden plans pin operation summaries and canonical digests.
  Unknown local divergence still requires manual review.
- No target layout, manifest schema, runtime pointer, ledger, or installed state migration
  changed. Rollback is a single reviewed revert.

## Evidence

- Design: `docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/designs/managed-update-extraction.md`
- Verification: `docs/ai/work-tracking/archive/20260713-task242-managed-update-slice-COMPLETED/reports/managed-update-slice/task-verification.md`
- Golden fixture: `tests/fixtures/aegis/managed-update-golden-plans.json`
- Regression: 1,765 repository tests pass with four opt-in skips; one unchanged temp-path
  assertion fails identically on untouched Task 240 because both isolated worktrees live
  under `/tmp`.

## Continuation

Task 242 is done and archived. Publish it as a stacked draft behind Task 240 and require
exact-head hosted CI from a normal checkout before delivery. Do not mutate downstream Blog
or HP-Fetcher repositories and do not weaken semantic-overwrite refusal.
