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
- 2026-09-01 — The first successful repaired install exposed one deeper semantic loop during live
  acceptance: the dashboard correctly projected `cycle.status=idle`, but still digest-bound every
  project's `last_attempt_at`, `completed_at`, and live-index `observed_at`. Each successful cycle
  advanced those audit clocks after its dashboard capture, guaranteeing the following cycle would
  rebuild. Two host-context snapshots with no intervening cycle were byte-identical, isolating the
  mutation to reconciler state advancement rather than Beads, Git, process, or vault drift.
- 2026-09-01 — Append-forward GREEN evidence adds a semantic post-cycle projection that omits only
  the three volatile audit timestamps while retaining their exact values in ordinary diagnostic
  snapshots. Host authority and confirmed live-index status remain required. The affected
  continuity/installer/reconciler/vault suite passes 73/73, including distinct-success-timestamp
  equality and missing-time refusal outside the explicit projection.
- 2026-09-01 — Broad append-forward verification passes 2,260 tests with 21 expected skips across
  the complete meta-workflow and Claude-adapter safety surfaces, excluding only the separately
  hosted package-install invocation module. Ruff, diff check, Aegis guard, drift check, plan sync,
  and work-tracking audit all pass.
- 2026-09-01 — Final append-forward acceptance used the exact already-installed runtime rather than
  repeating a byte-identical service transition. Two consecutive scheduled cycles advanced only
  audit clocks (`14:06:28Z` to `14:07:37Z`): all five output-tree manifests, dashboard snapshot and
  report digests stayed identical, and every live-index `refresh_attempted` value was false. The
  serialized strict check passed all four projects and the dashboard. The timer settled
  enabled/active/waiting, the service settled inactive/dead/success with zero restarts, WSL
  Obsidian retained PID `3168034` and start tick `35154910`, all four rigs remained suspended, and
  zero agents ran.
- 2026-09-01 — Archive preconditions were satisfied and the completed bundle was preserved.
