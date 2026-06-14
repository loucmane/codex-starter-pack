# Task 221 — Drain must not accrete read-only evidence (2026-06-14)

Third HP-Coach closeout report. Draining a PRE-#224 read-only pending backlog via
`aegis log --pending-id --plan-step plan-step-verify` accreted each event's evidence into
the plan's required-evidence cell → closeout.evidence.* required inspection noise
(.scratch/, /tmp/*.log, mcp__playwright__browser_click, =p, 127:). KEY INSIGHT: matching-layer
demotion (TM 218) is fundamentally insufficient — a read-only path token is indistinguishable
by shape from a real edit; only the originating event's tool/command knows. So fix at DRAIN layer.

## Shipped (live scripts/_aegis_installer.py + cli.py)
- `_load_target_gate_lib(target_root)`: dynamic import of the TARGET's gate_lib (sys.modules
  registered before exec_module; cached; fail-None).
- `_stored_event_is_read_only(target_root, event)`: STRICT fail-KEEP classifier by tool +
  recovered command, NEVER by evidence shape. Edit/Write/MultiEdit/NotebookEdit → keep. Bash:
  `cmd`...`` → bash_is_read_only(inner) (provably safe: bash_is_mutation is exact complement);
  redirect-target/aegis-verify evidence → keep. MCP: discard ONLY chrome-devtools/playwright
  namespaces + TASKMASTER_READ_ONLY suffixes + MCP_READ_ONLY_TOOL_RE; KEEP apply-gated aegis
  (repair/runtime_update/handoff_repair — they don't match read-only RE so kept by default),
  aegis read-only suffixes (conservatively kept due to target-dir-violation hole), and unknown.
- Drain-gate in log_work: read-only `--pending-id` event drains from queue, returns
  status="purged_read_only", writes NOTHING to surfaces/plan.
- `purge_read_only_pending(target_dir, apply=False)` + `aegis repair --purge-read-only-pending`
  (preview/--apply): batch-clean pre-#224 backlog; fail-KEEP; touches only the queue file.

## Verification
Design+adversarial workflow (wf_d5d2814c) FOUND the apply-gated escape (aegis_repair with empty
tool_input reconstructs read-only via payload_is_read_only) → closed by classifying NAME-ONLY
(never reconstruct Payload with empty tool_input). A diff-review sub-agent attacked the
implemented classifier → SAFE, no mutation escape. 20 tests (full classifier matrix incl.
apply-gated KEPT, fail-keep on missing/broken gate_lib, purge preview/apply, drain integration).

## Honest scope
Prevents FUTURE accretion + purges queue backlog; does NOT retroactively clean already-polluted
plan cells → HP-Coach task 80 stays mark-done, not recovered. Post-#224 read-only never enters
the queue, so lasting value is the one-time purge + a correctness backstop.

This CLOSES the HP-Coach closeout-report series (215 schema-skew, 216 churn, 218 orphan, 221
drain). See [[task218-recoverable-closeout-evidence]], [[task216-closeout-convergence]],
[[task222-secret-hygiene-and-backlog]]. Deferred: TM 219 (assets installer drift), TM 220
(path-lost populate).
