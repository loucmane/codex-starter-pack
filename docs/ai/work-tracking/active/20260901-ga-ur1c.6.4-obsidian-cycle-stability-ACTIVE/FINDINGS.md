# Findings

- 2026-09-01 — The installed reconciler completed every project projection and live-index probe,
  but its strict dashboard check failed immediately afterward. `reconcile_registry` holds
  `registry-cycle.lock` across dashboard generation, so the dashboard snapshot recorded
  `cycle.status=running`; the post-run check observed the released lock as `idle`. Because the raw
  snapshot is digest-bound into the report, equality was impossible even with unchanged project
  state.
- 2026-09-01 — RED evidence: the focused continuity/reconciler suite failed in three exact places:
  `capture_snapshot` rejected the new explicit status argument, the CLI rejected
  `--obsidian-cycle-status idle`, and dashboard capture omitted the option. No runtime code had been
  changed when these failures were captured.
- 2026-09-01 — GREEN evidence: the same 46 focused tests pass after adding the idle-only projection;
  direct capture under the held lock remains `running`, projected capture is `idle`, invalid
  `running` override is refused, and the reconciler fixed argv is asserted.
- 2026-09-01 — Broad regression evidence: 2,442 tests passed with 21 expected skips when the
  editable-package invocation module was excluded. Its first test attempted to create a fresh venv
  and download build dependencies, which the sandbox could not reach and the standing no-package
  boundary correctly refused to escalate. Eleven later failures were only attempts by legacy guard
  tests to create fixtures inside the externally rooted isolated worktree; both affected modules
  passed 92/92 in the writable execution context. Hosted CI remains the package-install authority.
