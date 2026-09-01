# Bead ga-ur1c.6.4 Make continuity dashboard cycle snapshots post-run stable – Implementation Notes

## Planned Workstreams
- Add a RED regression that captures the same Obsidian registry state while the reconciler lock is
  held and proves live observation remains `running` while the dashboard candidate projects `idle`.
- Restrict the explicit projection to `idle` at the continuity CLI boundary and thread it through
  the read-only collector.
- Make only the reconciler-owned dashboard capture use that post-release projection; direct
  continuity snapshots retain live flock observation.
- Prove focused and regression suites, publish through the signed PR path, then install and exercise
  the merge-bound reconciler with a changed cycle followed by a byte-identical no-op.

## Append-forward transaction repair
- Serialize `check_registry` with `reconcile_registry` through the registry-cycle lock.
- Stop the timer and wait for the oneshot service to become inactive before capturing state/output
  rollback snapshots, then issue one stabilizing stop to cancel a queued late activation; restore
  scheduler intent without killing an unquiesced pre-mutation service.
- Keep the timer enabled but inactive through the manual reconciliation and strict installed check;
  start it only after validation and require a settled waiting/success state.
- Compare rollback against the post-quiescence service baseline and stable timer policy, not
  transient preflight substates. Prime the restored runtime only when that stable baseline was
  successful; preserve a pre-existing failed result without replaying the known-bad cycle.
- Atomically recover only pure missing-file drift in an Aegis-owned generated subtree when every
  survivor and regenerated overlapping file matches the ownership manifest. Unknown, symlinked,
  or hash-modified content remains a hard refusal.
