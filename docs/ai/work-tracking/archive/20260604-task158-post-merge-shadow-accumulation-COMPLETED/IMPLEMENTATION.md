# Task 158 Add post-merge shadow accumulation with mismatch triage – Implementation Notes

## Implemented

- Added dynamic shadow-path `.taskmaster/state.json` prediction. Shadow records now start from candidate blast-radius paths and add `.taskmaster/state.json` to the effective prediction only when sacrificial validation observes that delta.
- Preserved legacy live apply prediction behavior by keeping required-state prediction as the default `_predicted_paths` behavior and using the optional path only from the shadow record builder.
- Added post-merge CI context binding: only `GITHUB_EVENT_NAME=push` and `GITHUB_REF=refs/heads/main` are valid for shadow accumulation; PR CI is diagnostic with `valid_for_shadow=false`.
- Added `build_shadow_accumulation_report` for artifact-only accumulation evidence, including reporting-only mismatch triage and explicit no-auto-extension fields.
- Added invalid Taskmaster authority refusal before sacrificial validation so malformed `.taskmaster/tasks/tasks.json` cannot produce `would_apply`.
- Changed precision corpus metrics from finding-kind aggregation to `(finding_kind, proof_source)` pair metrics.
- Wired CI to emit `reports/ci/reconcile-shadow-accumulation.json`, with candidate discovery only for valid post-merge context and a process-level whole-tree side-effect oracle allowing only that artifact delta.

## Verification

- Focused shadow/precision/CI workflow suite: 55 passed.
- Task 158 focused suite plus Task 157/159 standing gates: 73 passed.
- Apply write apparatus compatibility regression check: 19 passed.
- Full repository pytest: 1081 passed, 4 optional smoke tests skipped.
- Taskmaster health: OK, invalid dependency refs 0.
