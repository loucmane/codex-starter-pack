# Decisions

- 2026-06-04 — Add an explicit `reconcile_shadow_evidence_classification` layer to shadow
  accumulation artifacts instead of relying on prose alone. Empty valid post-merge runs are
  marked `operational_entry: true`, `precision_observation: false`, and
  `empty_real_accumulation_counts_as_zero_divergence_precision: false`.
- 2026-06-04 — Store run `26959807056` as committed evidence under `docs/aegis/evidence/`
  rather than as an in-repo runtime ledger. The record is documentation/test evidence only;
  it does not create an Aegis or Taskmaster state surface.
- 2026-06-04 — Pin the Taskmaster state initialization contract with a real CLI regression
  test, skip-guarded when `task-master` is unavailable, because the Task 160 active-tag
  presence guard depends on the pinned CLI not adding active tag keys during state init.
