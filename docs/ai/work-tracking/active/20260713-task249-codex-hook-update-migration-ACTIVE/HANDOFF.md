# Task 249 Fix pre-adapter Codex manifest update migration – Handoff Summary

## Current State
- The installer and packaged installer are byte-identical and use install-before-runtime
  sequencing for `project_update --apply`.
- Deterministic regressions cover Codex-only and multi-agent legacy manifests, final-schema
  validity, idempotence, direct-runtime strictness, and divergent-hook refusal before writes.
- A disposable Blog Task 40 snapshot upgraded successfully and passed all 42 strict checks.
- Live Blog remains untouched because Task 40 is active and `.codex/hooks.json` requires
  attended manual review.

## Next Steps
- Deliver Task 249 through hosted CI and the evidence-gated merge policy. Hosted CI must
  exercise the single source-checkout safety assertion whose premise excludes `/tmp`.
- After implementation merge, mark Task 249 done, archive its evidence through the
  supported source helper, and deliver the narrow terminal closeout.
- At a safe Blog checkpoint, rerun preview; preserve the operator hook until the owner
  explicitly chooses the managed candidate, then stop at `/hooks` exact-hash trust review.
