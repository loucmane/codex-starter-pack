# Task 237 Verification - Mode-Aware Agent Guidance

## Outcome

Task 237 replaces contradictory static strict ceremony with one compact, mode-aware managed
entrypoint contract. Enforcement behavior and `.aegis/contract.md` strict semantics are
unchanged.

## Implementation Evidence

- `scripts/_aegis_installer.py` owns one shared mode-aware renderer used by Claude, Codex, and
  Agents entrypoints.
- Every rendered managed block is capped at 25 nonblank lines.
- Existing Claude, Codex, and Agents project content is merged outside deterministic markers.
- Existing Codex content is merged on every install/update, including clean managed targets.
- Fresh Claude and Agents installs now receive explicit managed markers.
- An exact manifest-owned markerless legacy `CLAUDE.md` is migrated instead of being retained as
  project text. If its bytes differ from the recorded checksum, Aegis preserves it
  conservatively.
- `scripts/_aegis_installer.py` and
  `aegis_foundation/assets/scripts/_aegis_installer.py` are byte-identical.

## Blog Dogfood

The live Blog repository was on dirty Task 65 work, so only a dry-run update was executed there.
The preview reported five managed modifications, zero conflicts, zero manual reviews, no
non-managed paths, and `product_file_safety.safe=true`. No live apply was attempted.

An isolated local clone of the committed Blog Task 65 branch was then updated with the current
Task 237 source and a copy of Blog's advisory enforcement state.

| Check | Result |
|---|---|
| First apply | `applied`; 5 modifies, 34 skips, 0 conflicts, 0 manual reviews |
| Product-file safety | safe; no unsafe, manual-review, or non-managed paths |
| Enforcement after apply | advisory |
| Capsule | compiled and fresh |
| Second update preview | 0 modifies, 39 skips |
| Managed-block size | Claude 19, Codex 19, Agents 21 nonblank lines |
| Project-byte preservation | Codex true; Agents true |
| Legacy Claude ceremony | absent after exact manifest-owned migration |
| Formatting | `git diff --check` passed |

The three prior Blog guidance payloads totaled 6,939 bytes; the mode-aware managed blocks total
4,220 bytes, a 39.2% reduction. Claude's markerless strict payload fell from 5,310 bytes and 49
nonblank lines to 1,393 bytes and 19 nonblank lines. Codex and Agents gained explicit advisory
and strict branches, so their previously underspecified blocks grew while remaining below the
25-line budget.

The installed advisory guidance contains `aegis brief` and `aegis witness`, and explicitly says
that per-mutation logging, pending reconciliation, handoff repair, and closeout are not routine
advisory ceremony. The old strict loop is not preserved under `Existing Project Instructions`.

## Operational Metrics

- **Output size:** 6,939 prior managed bytes to 4,220 mode-aware bytes in Blog, a 39.2%
  reduction. All blocks remain within 19-21 nonblank lines against the 25-line budget.
- **Governance calls:** advisory guidance requires zero routine interior calls. The normal
  explicit surface is three boundary/orientation calls: `aegis enforce status` once at
  orientation, `aegis brief` for current context, and `aegis witness` before delivery.
- **Rollback surface:** the Blog apply changed exactly five installer-managed paths and no
  product paths. Rolling back the upstream Task 237 commit and rerunning the managed update
  restores the prior managed blocks while retaining project-owned bytes outside the markers.
- **Replay/idempotence:** the second update preview classified all 39 assets as skips, including
  all three entrypoints.

## Automated Verification

Passed:

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_mcp_server.py \
  tests/meta_workflow_guard/test_aegis_schemas.py \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_continuation_contract.py \
  tests/meta_workflow_guard/test_assets_scripts_parity.py \
  tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py -q

225 passed, 2 skipped in 85.62s
```

The two skips are opt-in distribution smokes:

- `AEGIS_RUN_CERTIFICATION_SMOKE=1` release certification.
- `AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1` real wheel/MCP target smoke.

Also passed:

- Ruff check with cache disabled on all four touched Python files.
- Canonical/package installer byte parity via `cmp -s`.
- `git diff --check`.

A whole-file Black run was evaluated but not retained because these large legacy files are not
globally Black-normalized and it introduced unrelated formatting churn. The Task 237 semantic
changes were reconstructed onto the original formatting, AST-equivalence checked, and then
retested.

## Residual Acceptance

After Task 237 merges and Blog Task 65 reaches a clean boundary, Blog should run its normal Aegis
update and observe one real Claude/Codex orientation cycle. That downstream canary should confirm
the qualitative result directly: advisory agents work normally without apologizing for skipped
strict ceremony. The isolated install already proves the source of those apologies is absent.

## Source Checkout Closeout

The upstream source checkout intentionally has no `.aegis/foundation-manifest.json`, so installed
target strict verification is not a valid closeout gate here. A source invocation correctly
returned `install_aegis_before_verify`; Aegis was not installed into its own source tree. This is
the documented source-checkout closeout gap owned by Task 244.

Source-native validation passed before the terminal Taskmaster transition:

- `bash .claude/scripts/readiness.sh --quick` returned `READY | task=237`.
- Taskmaster health reported 243 tasks, 383 subtasks, 428 dependency references, and zero invalid
  references.
- Plan sync, work-tracking audit, and the S:W:H:E guard passed.
- Taskmaster Task 237 is `done` and only its generated task file was refreshed.

After the task moved to `done`, readiness correctly exposed the known compatibility state:
`BLOCKED | task=237 | ... status is 'done', expected 'in-progress'`. The completed tracker is
retained under `active/` rather than fabricating installed-target current-work state; Task 244
owns the archive-derived readiness fix. Final audit, guard, Taskmaster health/dependency, Ruff,
mirror-parity, and diff checks still pass in this documented terminal state.
