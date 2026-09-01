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
