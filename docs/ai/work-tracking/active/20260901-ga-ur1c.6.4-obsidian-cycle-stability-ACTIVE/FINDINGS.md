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
- 2026-09-01 — The first merge-bound install stopped safely after proving a second race. The
  installer captured timer/service state before stopping the timer, then re-enabled the one-minute
  timer before its strict check. A queued cycle could therefore start while rollback snapshots or
  check snapshots were being read. The observed rollback snapshot retained exact manifests but
  omitted 6 Operations and 17 Blog generated `Legacy/` files; directory timestamps and unit timing
  bind the omissions to the raced restore, not source deletion or human-authored vault content.
- 2026-09-01 — The rollback bytes were restored, but the verifier compared transient timer/service
  substates (`running/start`) with the correct settled scheduler state (`waiting/dead`). The durable
  contract is timer enablement/activation plus its settled waiting state and the post-quiescence
  service result—not the state sampled before quiescence.
- 2026-09-01 — Append-forward RED evidence failed in four exact places: checks ignored the held
  registry lock, missing generated files blocked deterministic repair, the timer used `enable
  --now` before validation, and no semantic rollback comparator existed. The corresponding focused
  regressions now pass; the adjacent installer/reconciler/vault/continuity suite passes 46/46.
- 2026-09-01 — Proportional verification is 2,459 passed with 21 expected skips. An initial broad
  run deliberately surfaced 77 environment-only refusals because its fixture root was inside Git;
  a second run still disagreed with Python's Windows-inherited temp root. Pinning `TMPDIR`, `TMP`,
  and `TEMP` consistently to WSL `/tmp` made the complete affected corpus pass 682/682 with 9
  expected skips. No product failure remained.
