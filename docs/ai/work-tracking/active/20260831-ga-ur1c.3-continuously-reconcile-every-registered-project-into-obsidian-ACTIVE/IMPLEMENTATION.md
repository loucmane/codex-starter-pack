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

## Verification to Date
- `ruff check`: PASS for every changed Python source and test.
- Focused Obsidian/plugin/schema suite: `58 passed`.
- Core Aegis installer suite: `158 passed, 1 skipped`.
- Adjacent offline integration modules: `93 passed, 1 skipped`.
- Plugin validation and generated registry `--check --validate-roots`: PASS.
- Two temporary editable-install tests require a network build-dependency fetch and are intentionally deferred to hosted CI; no package installation or safety bypass was used locally.
