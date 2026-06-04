# Task 158 Scope And Safety Boundary

## Scope

Task 158 implements post-merge shadow accumulation as evidence only. It may produce CI upload artifacts, but it must not enable live apply, flip any kill switch, mutate Taskmaster/Aegis workflow state, update git refs, or write a repository ledger.

## Decisions

- Shadow `.taskmaster/state.json` prediction is dynamic: the shadow path starts from the candidate blast-radius paths and adds `.taskmaster/state.json` to the effective prediction only when the sacrificial clone actually changes it.
- Existing live apply runtime behavior remains deliberately unchanged for this task. The live write apparatus still uses the legacy required-state prediction until a later enablement hardening task changes that path explicitly.
- Shadow context proof is valid for accumulation only on `push` to `refs/heads/main`; pull request CI artifacts are diagnostics and are emitted with `valid_for_shadow=false`.
- Accumulation triage is reporting-only. It may flag canonicalization completeness findings, but it must not update canonicalization versions or exemptions.
- Shadow refuses malformed or structurally invalid Taskmaster authority before sacrificial validation, so invalid `.taskmaster/tasks/tasks.json` cannot enter `would_apply` evidence.
- Precision evidence is keyed by the live `(finding_kind, proof_source)` pair rather than by finding kind alone.

## Verification Targets

- Focused shadow, precision, and CI workflow tests.
- Task 157/159 standing gates for target selector discipline, degraded classifier delegation, and agent-facing apply isolation.
- Full repository pytest.
- Taskmaster health, work-tracking audit, plan sync, guard validation, and whitespace checks.
