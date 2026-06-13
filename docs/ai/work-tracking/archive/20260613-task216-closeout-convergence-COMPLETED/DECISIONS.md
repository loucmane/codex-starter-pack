# Decisions — Task 216 closeout convergence

- 2026-06-13 — D1 — Ship the churn-engine fix; defer the generate-don't-assert populate rework to TM 217 (full record below).

## D1 (2026-06-13): Ship the churn-engine fix; do NOT do the generate-don't-assert populate rework now.

**Context.** TM 216 was filed from the HP-Coach closeout report describing a
"fix-creates-failure loop": satisfying `closeout.evidence.*` required editing surface
files, but every edit re-armed the pending-tracking queue that `closeout.pending_tracking`
needs empty, so closeout never converged.

**Evidence (read-only reproduce → map → design → adversarial-review workflow, 9 agents).**
- **Reproduced empirically against the real CLI.** With the churn-engine fix applied
  (read-only Bash + `codex-task` logging no longer arm pending-tracking), the canonical
  flow `kickoff → aegis log (scope/implement/verify) → aegis verify --strict → closeout
  --update-handoff` **converges in one shot**: status=passed, 23/23 required gates,
  pending queue empty throughout, second back-to-back run idempotent.
- **Invariant holds.** A committed source change with the implement/verify steps NOT
  logged fails closeout (11 required gates), and `--update-handoff` cannot fabricate the
  missing evidence. Un-evidenced work cannot pass.
- **Root cause of the original loop = the adapter hooks, which we already fixed.** The
  loop was the PreToolUse/PostToolUse layer (`.claude/scripts/gate_lib.py`) arming
  pending-tracking on inspection and self-logging. `aegis log` *clears* pending-tracking;
  it never arms it. The `_aegis_installer.py` closeout/log machinery has no self-re-arming
  loop.
- **Residual is bounded, not a loop.** Logging with a non-default `--surface` selection
  (e.g. `--surface handoff` only) leaves some surfaces without tokens → closeout fails
  ONCE → the report emits exact `aegis log --surface …` repair commands → applying them
  (no re-arm) → next closeout passes. Fail → 1 repair → pass.

**Why not do the populate rework now.** All three adversarial reviewers returned
`sound-with-changes`, with serious concerns:
1. **Invariant soft spot:** `strict_verify_rel` is always required, so a populate step
   would synthesize fake `aegis:verify` SWHE lines even when verify was never logged;
   safe only because `closeout.strict_verify` re-runs independently — but the design must
   not rely on synthesized text. Must refuse to synthesize unless a green
   `verification-report.json` exists on disk.
2. **Idempotence regression:** making `--update-handoff` default-on promotes
   `_render_closeout_handoff`'s wholesale section regeneration to every closeout, which
   **clobbers operator-authored HANDOFF prose** (Blockers/Next Steps/Important Context).
   Needs surgical per-section repair, not full re-render. Also second-run idempotence
   actually comes from the archive short-circuit, not a populate fixpoint.
3. **Drain coupling:** the proposed pending-drain compares plan-cell-derived tokens
   (through `_split_evidence_tokens`/`_markdown_table_cell`) against pending-event
   evidence (through `payload_evidence`/`normalize_path`) — two different normalizers; a
   mismatch leaves a stale event and reintroduces the exact non-convergence it targets.
4. **Test churn:** central tests (`test_closeout_requires_semantic_handoff_and_passes_with_update`,
   `test_closeout_reports_missing_evidence_repair_guidance`) need full rewrites, and the
   design's own negative-test reasoning was wrong about which gates fail (handoff evidence
   gates pass vacuously over empty token lists; the real blockers are
   `closeout.pending_tracking` + `closeout.strict_verify`).

**Decision.** The churn-engine fix resolves the loop TM 216 actually reported, proven
empirically with the invariant intact. The generate-don't-assert populate rework is
high-risk, partially redundant (canonical work already one-shots), and would weaken or
complicate the core gate. Ship the churn fix as TM 216. Capture the populate rework as
TM 217 with the three reviewer-mandated safety constraints as acceptance preconditions.

**Follow-up (TM 217 scope).** One-shot convergence for non-canonical usage
(no `--update-handoff`, or non-default `--surface`) via a populate step that: (a) sources
tokens ONLY from logged plan rows; (b) never synthesizes `strict_verify_rel` without the
on-disk green report; (c) does surgical handoff section repair preserving operator prose;
(d) drains pending events on the pre-escape `_normalize_evidence` form with a log_work-style
no-silent-miss guard; (e) keeps `dry_run` strictly read-only. Negative test must assert
failure on `closeout.pending_tracking`/`closeout.strict_verify`, not the (vacuous) handoff
evidence gates.
