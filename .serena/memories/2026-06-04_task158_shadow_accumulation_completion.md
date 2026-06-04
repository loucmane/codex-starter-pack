# Task 158 Shadow Accumulation Completion

Implemented Task 158 on branch `feat/task-158-post-merge-shadow-accumulation`.

Key changes:
- `aegis_foundation/reconcile_shadow_apply.py` now treats `.taskmaster/state.json` as optional on the shadow path: shadow predictions omit it initially, sacrificial validation adds it to the effective prediction only when the clone actually changes it, while legacy live apply callers retain required-state prediction behavior.
- Added `build_shadow_accumulation_report` for artifact-only post-merge shadow evidence. It emits `valid_for_shadow`, reporting-only triage fields, and never auto-extends canonicalization exemptions.
- `build_ci_shadow_context_proof` now distinguishes `push` to `refs/heads/main` from PR/other CI and marks PR evidence `valid_for_shadow=false`.
- Shadow now refuses malformed/invalid `.taskmaster/tasks/tasks.json` before sacrificial validation so invalid Taskmaster authority cannot enter `would_apply` evidence.
- Precision corpus helper now reports metrics by `finding_kind/proof_source` pair (`precision_by_finding_proof`) instead of kind-only aggregation.
- CI workflow now captures `reports/ci/reconcile-shadow-accumulation.json`; PR runs do not run candidate discovery, push/main runs the shadow path, and the step is wrapped with `snapshot_whole_tree(..., require_tmp_root=False)` allowing only the declared artifact delta.

Verification:
- Focused shadow/precision/CI workflow tests: 55 passed.
- Focused Task 158 plus Task 157/159 standing gates: 73 passed.
- Apply write apparatus regression after prediction split: 19 passed.
- Full pytest: 1081 passed, 4 optional smoke tests skipped.
- Taskmaster health after status updates: OK, all 159 tasks done, invalid dependency refs 0.

Important nuance:
- Do not remove required `.taskmaster/state.json` prediction from the live apply runtime in this task. Task 158 only makes shadow evidence dynamic. The live write path still depends on the legacy required-state behavior until a later enablement-hardening task changes runtime prediction deliberately.