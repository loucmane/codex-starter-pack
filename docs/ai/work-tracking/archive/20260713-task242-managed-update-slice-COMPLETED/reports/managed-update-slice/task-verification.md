# Task 242 Managed-Update Extraction Verification

## Outcome

Task 242 extracted the deterministic managed-update slice from the installer without changing
installed bytes, invocation shape, update classification, mutable target state, manifest schema,
or rollback semantics. The source and packaged installers remain byte-identical, and every
unknown semantic overwrite remains fail-closed.

## Changed Architecture

- `aegis_foundation/managed_update.py` is the authoritative stdlib-only core for managed assets,
  asset-set assembly, target-specific materialization, checksum/prior-byte recovery, operation
  classification, and summaries.
- `scripts/_aegis_installer.py` supplies policy constants and renderer/materializer callbacks and
  retains orchestration, I/O, report generation, apply, rollback, and legacy private adapters.
- `aegis_foundation/assets/scripts/_aegis_installer.py` is a mechanical byte-identical mirror.
- No installed repository receives a new state copy or migration.

## Measured Surface

| Surface | Before | After | Delta |
|---|---:|---:|---:|
| `scripts/_aegis_installer.py` | 14,349 | 13,942 | -407 lines |
| `aegis_foundation/managed_update.py` | 0 | 870 | +870 lines |
| Installer source diff | — | 128 additions / 535 deletions | -407 net |
| Target migrations | 0 | 0 | 0 |

## Golden Consumer Contracts

| Consumer | Scenario | Summary | Operation digest |
|---|---|---|---|
| Codex | fresh Codex target with project entrypoint/hooks | 38 create, 2 safe modify, 0 skip/conflict/manual | `4367457a215ea7d0c08321e8fa5cddb51b52da107a3e8e3784a9a8be4c7f57d3` |
| HP-Fetcher | installed Claude target with a known-prior stale gate | 0 create, 2 safe modify, 30 skip, 0 conflict/manual | `0be616403ea8b4d6c614d12de8153726e6daa456b0da8244bc394d5ad37b2a66` |
| Blog | installed multi-agent target with a known-prior stale ledger | 0 create, 2 safe modify, 40 skip, 0 conflict/manual | `314290cb214c29b5f4aaaa36d538bf73725495cecae84eb1258e15541bb97ba1` |

The tests also prove dry-run byte preservation, source/package generated-byte parity,
source/package plan parity, custom entrypoint/hook preservation, and `manual-review` refusal for
unrecoverable local divergence.

## Read-Only Downstream Preview

No downstream repository was mutated.

- Blog preview: safe; 2 creates, 14 modifies, 26 skips, zero conflicts/manual reviews. Capsule
  compilation and workflow evidence remained available.
- HP-Fetcher preview: safe; 1 create, 9 modifies, 22 skips, zero conflicts/manual reviews. Its
  three known Task 80 workflow-state failures remained evidence only: branch alignment, missing
  report path, and advisory pending tracking.

The live counts intentionally differ from synthetic goldens because downstream installed assets
are older; both paths still exercise the same extracted classifier.

## Original Branch Verification Matrix

- Golden managed-update tests: 6 passed.
- Focused update compatibility selection: 9 passed, 131 deselected.
- Fixture/cross-project selection: 14 passed.
- Installer plus extracted-core suite: 145 passed, one opt-in certification smoke skipped.
- MCP server and end-to-end suite: 76 passed, one opt-in real-target wheel smoke skipped.
- Release and invocation suite: 22 passed, two opt-in wheel smokes skipped.
- Opt-in local wheel CLI smoke: passed.
- Opt-in local wheel MCP stdio smoke: passed using an isolated `/tmp` uv/uvx cache wrapper so
  nested processes did not write the read-only home cache.
- Black 26.3.1: passed.
- Ruff 0.15.12: passed.
- Source/package installer comparison: byte-identical.
- `git diff --check`: passed.
- Taskmaster health: 245 tasks, 383 subtasks, 430 dependency references, zero invalid.
- Plan/tracker sync, work-tracking audit, readiness, and S:W:H:E guard: passed.
- Timestamp regressions: 5 passed.
- Template drift: zero findings.
- CI-profile scanner chain: all six stages passed; zero broken references and zero security
  findings.
- Reference-fix dry-run: no fixes.
- Monitoring and performance: passed. Phase 0, cost, and migration dashboards completed with
  their policy-defined warning status and successful exit codes.
- Complete repository suite: **1,765 passed, four opt-in smokes skipped, one baseline-specific
  failure** in 377.60 seconds.
- Exit-zero local regression gate with only the proven temp-location assertion deselected:
  **1,765 passed, four opt-in smokes skipped, one deselected** in 363.77 seconds.

## Current-Main Reconciliation Verification

- Reconciled current main Tasks 247–251 without restoring stale pre-adapter behavior.
- Added explicit shared-runtime ownership to the extracted asset policy: multi-agent installs emit
  shared Claude/Codex hook assets once, while Codex-only installs render the same dispatchers.
- Ported Tasks 248–249 hook safety into the extracted materializer/planner: semantically identical
  owner-created JSON is adopted byte-for-byte; structural merging requires a fresh target or an
  unchanged recorded baseline; divergent installed or unowned hooks remain `manual-review`.
- Managed-update/golden tests: 10 passed.
- Codex hook, apply-patch, and source/package parity tests: 49 passed.
- Installer and release-distribution tests: 155 passed, three explicit opt-in smokes skipped.
- Ruff and Black checks pass through isolated `/tmp` tool caches; `git diff --check` passes.
- Source/package installer SHA-256 is byte-identical.
- Taskmaster health: 250 tasks, 383 subtasks, 435 dependency references, zero invalid.
- Complete suite in the Task 242 `/tmp` worktree: 2,030 passed, four opt-in smokes skipped, and the
  one known governed-checkout location assertion failed after 431.99 seconds.
- The exact location assertion passed when evaluated with a non-temp repository context, proving
  the failure is the documented worktree premise rather than the managed-update implementation.
- Signed runtime tree `d29cea9793057340e9b4334cf94287b6300fbe4e` passed the complete suite
  from a non-temp task-bearing checkout: **2,031 passed, four explicit opt-in smokes skipped,
  zero failures** in 407.46 seconds.
- Hosted protected CI's first witness run accounted for 23 of 24 paths and rejected only the
  required `.plan_state/sync.log` plan/tracker hash ledger. The repository brief now declares
  `.plan_state/` as an always-in-scope governance surface, with a focused policy regression test;
  no wildcard or witness bypass was added.
- Fresh hosted protected CI and witness evidence remain required for the corrected PR head.

## Disclosed Baseline-Specific Results

### Governed-checkout temp-location assertion

`test_test_enabled_apply_refuses_governed_repo_target_before_validation` expects the governed
repository to be outside the system temp tree and therefore expects `target_not_isolated_temp`.
Both `/tmp/codex-task242` and untouched `/tmp/codex-task240` instead return
`candidate_already_done`. The exact isolated test fails identically in both worktrees. Task 242
does not touch the reconcile apparatus or this test. The assertion remains unchanged; hosted CI
from the normal checkout is required before delivery.

### Optional real-target wheel MCP lifecycle smoke

The opt-in real-target wheel MCP harness installs Aegis and immediately calls kickoff without
acknowledging the required client-reload marker. It fails identically on untouched Task 240.
The basic wheel CLI and MCP stdio smokes pass. Task 242 does not weaken the client-reload contract
or broaden into harness repair.

## Safety And Rollback

- Unknown prior bytes and local divergence remain unsafe and require manual review.
- Seed-once owner configuration remains owner-maintained.
- Project-authored Claude/Codex/AGENTS text and unrelated Codex hooks remain structurally
  preserved.
- Source-root, package, installer-private, CLI, and MCP invocation shapes remain compatible.
- Advisory/strict behavior, ledger schema, runtime pointer, manifest schema, and target layout are
  unchanged.
- Rollback is a reviewed revert of the Task 242 commit. No downstream repair or migration is
  required.

## Hosted Delivery Gate

The exact signed PR head must pass the repository's normal-checkout Python matrix, source guard,
meta-workflow guard, Aegis witness, and evidence-gated delivery checks. Task 240 and Task 241 are
already delivered; Task 242 can target `main` directly after its current-main reconciliation is
committed and independently verified.
