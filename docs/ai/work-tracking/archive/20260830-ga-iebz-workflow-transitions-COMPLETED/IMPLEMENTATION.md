# Implementation evidence

## Delivered lifecycle

- Added a versioned `gas-city-workflow` 0.2.0 lifecycle CLI with `begin`, `resume`,
  `recover`, `checkpoint`, `verify`, `publish`, and `finish` commands.
- Added a Git-common-directory transaction journal that records immutable project, rig, bead,
  branch, worktree, and starting-commit identity plus append-forward phase and lifecycle events.
- Made begin/recovery derive the canonical checkout and approved worktree root, validate the bead
  and dependencies, safely create/adopt/fast-forward only an unscaffolded clean worktree, create
  or verify the Aegis scaffold, claim the bead, and require source readiness.
- Pinned the managed operator PATH for every `gc bd` operation so cold starts do not depend on a
  caller shell.
- Added installed-plugin runtime resolution through the canonical Gas City Operations registry,
  while source work continues to use the checked-out tracked runtime.
- Removed the false `.aegis/bin/aegis` readiness candidate from project context and exposed the
  real lifecycle entrypoint and literal begin/resume command shapes.
- Added Git-origin comparison so a stale descriptor or central registry entry blocks after a
  repository rename instead of silently orienting to the wrong identity.

## Recovery proof

The first live `ga-iebz` execution stopped after `worktree-created` because the source checkout's
real session-state schema uses `current` plus `plans/current`, while the initial fixture modeled an
installed-style `task.id`. The successor implementation accepts both supported schemas, derives
the bead from the single-bead current plan, verifies the current session's bead marker, and resumed
the exact same journal to `ready`. A second `resume` omitted `--bead` and independently derived
`ga-iebz` from live source state. No branch or worktree was recreated.

## Verification

- `black` and `ruff` pass on the lifecycle and plugin test surfaces.
- 26 focused plugin/lifecycle tests pass, covering exact replay, safe pre-scaffold fast-forward,
  canonical-main advancement, pre-scaffold failure recovery, path/branch/dependency refusal,
  registered and descriptor-only projects, installed-runtime resolution, origin matching and
  mismatch refusal, journal events, and router-policy non-duplication.
- Live project context reports repository origin `loucmane/gas-city-operations` as exact.
- Live recovery reached `phase=ready`, `bead_status=in_progress`, and a second no-bead resume was
  an exact idempotent replay.
- The live `ga-k0ry` dry run blocks on its unresolved dependency `ga-iebz`, proving dependency
  ordering before any worktree, scaffold, or ledger mutation.
- The source checkout verification branch now self-synchronizes the plan and uses the supported
  source work-tracking audit; installed targets use strict Aegis verification. A failed attempt to
  use installed verification on this source checkout was preserved under ignored `.aegis/reports/`
  and led directly to the explicit backend split.
- A live readiness render now points to the existing tracked `scripts/codex-task aegis next`
  surface instead of the absent source `.aegis/bin/aegis` shim.
- Publication verification reuses all read-only gates without rerunning the timestamped plan-sync
  mutation after the signed commit; the first blocked publication attempt and its appended sync
  record remain preserved in the committed audit log.

## Progress Log
- **2026-08-30 13:02 CEST** - [S:20260830|W:ga-iebz-workflow-transitions|H:plugins/gas-city-workflow|E:docs/ai/work-tracking/archive/20260830-ga-iebz-workflow-transitions-COMPLETED/IMPLEMENTATION.md] Implemented and exercised the memory-independent modular lifecycle, recovery journal, pinned environment, installed runtime, and origin identity guard.
- **2026-08-30 13:24 CEST** - [S:20260830|W:ga-iebz-workflow-transitions|H:github:pr-317|E:PR:317;merge:4b264614c8785271eab4cfd4f2114b1ec4a17b87;plugin:gas-city-workflow@0.2.0+codex.20260830111111] Merged the byte-identical reviewed tree and reinstalled the canonical plugin; cached and source `workflow.py` digests match exactly.
