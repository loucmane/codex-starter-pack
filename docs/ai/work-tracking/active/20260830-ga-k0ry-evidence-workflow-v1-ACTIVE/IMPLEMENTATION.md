# Evidence workflow v1 implementation

## Generic surface

- Added strict `gas-city-evidence-run.v1` JSON Schema.
- Added the `gas-city-evidence-workflow` skill and project profile contract.
- Added exactly five executable commands: freeze, validate, bundle audit, report validation, and
  lane comparison.
- Kept `mode=shadow` structural. The generic comparator emits `domain_verdict: null` and cannot
  replace project quality logic.
- Added an optional validated project `base_ref`; HPFetcher now derives new task worktrees from
  `refs/remotes/origin/main` without touching its dirty, parked canonical checkout.
- Added target-aware lightweight lifecycle scaffolding for projects without an installed Aegis
  foundation. The canonical `codex-task` validates the foreign Git root, writes only beneath that
  worktree, forbids cross-project Taskmaster kickoff, and exposes target-aware plan sync.
- Added profile-native readiness for frozen-legacy projects. It binds the transition journal,
  exact bead branch, selected base ancestry, current plan/session, and one matching tracker while
  tolerating only unrelated trackers that are tracked and byte-unchanged at the selected base.
- Made lightweight checkpoint and finish resolve the exact bead-scoped ACTIVE folder instead of
  relying on a single-active-folder memory convention. Cross-project finish reuses the canonical
  transactional archive engine while preserving unrelated historical trackers and frozen `.aegis`
  state; same-repository source closeout remains unchanged.

## Frozen bindings

The manifest binds the parent bead, project and rig, clean subject repository/branch/commit/tree,
profile, request, authorization envelope, prompts, rubrics, schemas, bundle builders, external
inputs, Fable inputs, candidates, lane directories, and authoritative outputs. The validator
recomputes every binding and refuses drift.

The authorization envelope is an audit artifact only. Its exact report write roots and explicit
exclusions are checked, but current dispatch and lifecycle authority remain external gates.

## Fail-closed fixtures

Focused fixtures cover clean freeze/validation plus refusal on overwrite, external/profile drift,
authoritative mode, repair without `supersedes`, dirty source, project/rig mismatch, blind-bundle
leakage, Git/symlink content, undeclared output, candidate mismatch, malformed event chains, and
interrupted closeout. Seal → Fable readback → dispatch → release is digest-chained and strictly
ordered.

Validation evidence:

- Codex plugin validator: PASS.
- Evidence and plugin focused tests: 16 passed; lifecycle/plugin base-ref regression: 28 passed.
- Cross-project lifecycle proof: HPFetcher `hpf-nqzf` reached journal phase `ready` from exact main
  `5415f14f...` in its isolated worktree while the dirty canonical checkout remained untouched.
- Target-aware helper regression: 246 combined `codex-task` and workflow-transition tests passed.
- Packaged `codex-task` parity and all focused lifecycle/evidence regressions: 272 passed.
- Complete repository regression with network available for isolated editable-install fixtures:
  2,322 passed and 21 explicitly skipped.
- Optional `ruff` command was unavailable in the environment; Python compilation and repository
  guard checks remain required before commit.

## Pilot-discovered confinement repair

The first immutable pilot manifest froze successfully before dispatch, but its report roots were
under the operations scratchpad while the managed HPFetcher Sol worker is intentionally writable
only beneath the HPFetcher worktree root. No route, session, or worker mutation occurred.

Repairs now accept a required absolute `supersedes_manifest` only when `repair=true`. The
successor manifest binds that predecessor file's SHA-256 and revalidates its run identity. This
allows a repair to move to an already-approved output root without copying, relocating, or
rewriting old evidence and without widening a worker sandbox. Legacy non-repair manifests remain
valid and must omit the new field. Focused coverage proves cross-root repair, predecessor digest
drift refusal, and backward-compatible validation of run 001.
