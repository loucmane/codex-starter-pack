# Bead ga-ur1c.3 Continuously reconcile every registered project into Obsidian – Implementation Notes

## Planned Workstreams
- Generate the installed Obsidian registry deterministically from the canonical Gas City workflow project registry and validated descriptors. A project is never discovered by scanning arbitrary directories.
- Publish each project into its own `GasCity/<project>/Aegis` managed subtree with a stable `Home.md` live-index probe and exact rig-scoped Bead export.
- Extend the strict registry with one fixed-shape continuity dashboard definition. The runtime invokes the pinned continuity entrypoint with constructed arguments, validates its v1 report, and publishes deterministic Now/Next/Blocked/Drift Markdown without exposing the raw snapshot.
- Observe every configured live-index probe on byte-identical cycles; reload Obsidian only when filesystem bytes changed.
- Extend the transactional user installer so the generated registry, runtime, unit write allowlist, timer, initial publication, idempotent reapply, and rollback remain one reviewed operation.

## Implemented Surfaces
- `build_obsidian_registry.py` turns the canonical workflow project registry into one strict tracked Obsidian registry for Gas City Operations, Gas City, HPFetcher, Blog, and descriptor-validated future projects.
- The registry enforces isolated `GasCity/<project-id>/Aegis` outputs beneath one declared managed root and a non-overlapping `GasCity/Continuity` dashboard.
- `obsidian_continuity.py` captures the fixed continuity snapshot/audit interface and atomically renders `Status.md` plus `report.json` from its machine classifications.
- Reconciler cycles publish the dashboard only after every project succeeds. Changed bytes trigger one live-app reload and managed-note read; byte-identical cycles perform the read without reloading.
- The installer includes the dashboard runtime, expands only the exact systemd write allowlist, creates only missing direct managed project parents, and rolls back new parents on failed installation.
- Plugin v0.6.0 and both recovery/reboot runbooks document generation, onboarding, freshness, live-index, and dashboard authority.
- Repair bead `ga-ve57` replaces inferred Bead-store paths with explicit host `rig_root`
  bindings, raises the bounded live-index timeout to 30 seconds, and upgrades installation
  rollback to snapshot and restore private state, managed output trees, service result, and timer
  state after quiescing the reconciler.
- Plugin v0.6.3 raises only the agent-identity ceiling to the pre-existing 5,000-edge bound,
  batches every configured live-index probe after filesystem publication, and reloads a shared
  Obsidian executable/vault endpoint at most once per cycle. Rollback waits through any persistent
  timer catch-up execution, then restores captured state and output trees again before asserting
  the predecessor timer substate.
- Plugin v0.6.4 observes the complete project publication batch before capturing the continuity
  dashboard, then observes the dashboard as a second bounded phase. Rollback restores and reloads
  the predecessor timer/service before clearing failed state and now compares the final service
  enabled/active/substate/result tuple with the captured predecessor.

## Verification to Date
- `ruff check`: PASS for every changed Python source and test.
- Focused Obsidian/plugin/schema suite: `58 passed`.
- Core Aegis installer suite: `158 passed, 1 skipped`.
- Adjacent offline integration modules: `93 passed, 1 skipped`.
- Plugin validation and generated registry `--check --validate-roots`: PASS.
- Two temporary editable-install tests require a network build-dependency fetch and are intentionally deferred to hosted CI; no package installation or safety bypass was used locally.
- `ga-ve57` repair regression: 48 focused Obsidian/plugin tests plus the 158-test Aegis
  installer suite PASS (one certification smoke skipped by its explicit opt-in guard).
- v0.6.3 focused regression: 33 PASS, including a 2,421-agent real-scale fixture, two changed
  projects sharing one reload, and an `elapsed` to `waiting` rollback catch-up with final exact
  tree restoration.
- Expanded v0.6.3 regression: 226 PASS / 1 explicit certification skip across all Obsidian,
  continuity, plugin, and Aegis-installer suites. Registry generation/root validation,
  work-tracking audit, S:W:H:E guard, and `git diff --check` also pass.
- v0.6.4 regression: the same 226-test surface remains PASS with one explicit certification skip;
  the dashboard test now proves confirmed project state is captured before dashboard publication,
  and the rollback test proves predecessor timer reload precedes failed-state cleanup.
- Hosted CI passed on Python 3.11 through 3.14 and every required delivery/guard workflow. PR #341
  merged exact signed head `1259ccee` as `e56d4899` with byte-identical tree `7912ae77`.
- Installed v0.6.4 digests: runtime `118a75b4`, service `9e3e9df1`, timer `85a227e0`, registry
  `ab3b8a76`. Host acceptance confirmed every project/dashboard live index and one byte-identical
  no-reload cycle while preserving WSL Obsidian PID `3168034` and suspended rigs.
