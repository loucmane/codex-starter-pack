# Task 216 — Closeout convergence: design scope

Date: 2026-06-13. Trigger: HP-Coach closeout report "fix-creates-failure loop".

## Decision (see DECISIONS.md D1 for full evidence)
Ship the CHURN-ENGINE fix; defer the generate-don't-assert populate rework to TM 217.

A read-only reproduce→map→design→adversarial-review workflow (9 agents) proved
empirically that, post-churn-fix, the canonical kickoff→log→verify→closeout flow already
converges one-shot, the invariant holds (un-evidenced work fails), and the original loop
was the adapter-hook churn we fixed. The populate rework drew three sound-with-changes
reviews flagging real regressions (operator-prose clobber, strict_verify synthesis, drain
normalizer mismatch); it is partially redundant and high-risk, so it is TM 217 with the
reviewer constraints as acceptance preconditions.

## Churn-engine fix boundary
.claude/scripts/gate_lib.py (+ assets mirror) + tests only:
- READ_ONLY_SIMPLE_COMMANDS expanded (jq/column/… ) with READ_ONLY_WRITE_FLAG_GUARDS
  for in-place writers (sed -i, yq -i, sort -o).
- payload_is_codex_task_logging excludes this repo's logging/workflow commands from
  pending-tracking (codex-task analog of payload_is_aegis_log).
- Core invariant preserved: every real source mutation still enqueues (tested).
