# Bead ga-ur1c.6.6 Record verified Codex Desktop transport retests – Implementation Notes

## Planned Workstreams
- **2026-09-02 00:21 CEST** — Added strict v1 transport-retest validation to
  `aegis_foundation/reboot_readiness.py`. Exact version/config/rollback/check/time
  evidence promotes only a newer, non-affected build from candidate warnings to
  PASS; known affected builds ignore attestations and still require the disabled
  `codex_app` workaround.
- **2026-09-02 00:21 CEST** — Added
  `scripts/record-codex-desktop-transport-retest` and its package entry point.
  The recorder writes mode-0600 deterministic JSON atomically, is idempotent for
  exact bytes, refuses drift, and supports later append-forward replacement only
  with the exact predecessor SHA-256 while preserving a digest-named private
  backup.
- **2026-09-02 00:21 CEST** — Added the strict JSON Schema, operator runbook,
  recovery guidance, focused validation for valid/missing/mismatched/extra-field
  and affected-build cases, recorder privacy/idempotence/rollback tests, and
  bumped the doctor version to `2026.09.02.1`.
- **2026-09-02 00:21 CEST** — Focused and related regression PASS: 85 tests;
  Ruff lint/format and `git diff --check` PASS. Full repository PASS: 2,482
  passed, 21 expected skips in 231.43 seconds. A preliminary full run's exact 73
  failures were proven to be the existing whole-tree temp-root harness guard;
  all 73 passed unchanged and the clean full suite passed after nesting pytest's
  base under Python's declared temp root.
- **2026-09-02 00:44 CEST** — Published the exact signed source and evidence
  correction through PRs #364 and #365. Installed only the merge-bound
  user-level doctor after preserving predecessor SHA-256
  `fd6509d9b7ce3766f62c40530a847a765ced4c2d462c8cc7cc50394d9009ad26`
  under a mode-0700 rollback root. Recorded the strict mode-0600 attestation,
  verified exact no-op replay, and ran the host doctor to READY with 20/20
  checks passing.
- **2026-09-02 00:44 CEST** — Preserved the first doctor report, which overlapped
  the periodic Obsidian reconciliation and failed only its concurrent health
  check, as separate defect evidence. A stable-window rerun passed every check;
  the deterministic concurrency repair is tracked append-forward as
  `ga-ur1c.6.7` rather than hidden or absorbed into this task.
