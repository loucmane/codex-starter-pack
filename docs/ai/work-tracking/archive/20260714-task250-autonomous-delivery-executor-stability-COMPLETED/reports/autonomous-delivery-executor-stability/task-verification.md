# Task 250 Verification Evidence

## Initial PR #276 remediation

PR #276 had all required workflows green, no review threads, and an exact
synchronized head. The read-only evaluator correctly returned `provisional`
while GitHub reported `mergeable=true/state=unstable`. The initial Task 250
implementation added executor-phase candidate check/status accounting and a
second policy evaluation before merge.

Its local verification passed 72 focused tests, source/package policy parity,
Ruff, Taskmaster health, plan/tracker parity, source guards, and the full suite
apart from the documented `/tmp` location-sensitive assertion. Protected hosted
checks then passed and the governance PR merged normally as `0088fff`.

## Canary correction

The required live canary PR #278 did not merge. Its `workflow_run` executor was
anchored to trusted `main`, so the initial candidate-head self-check lookup was
structurally unable to find the current merge job and failed closed with
`executor-self-check-missing`.

The follow-up evidence and verification are recorded in
`pr278-executor-run-evidence.md`. The attended remediation merged as `89ea3a4`,
PR #278 autonomously merged at exact current head `2a034355` as `c3daa484`, and
repository-dispatch CI and guards passed against that exact merge SHA. The full
hosted proof is recorded in `hosted-canary-acceptance.md`.

## Terminal reconciliation

PR #276 is superseded rather than merged because its Taskmaster/session pointers
predate current Task 250 authority. Its durable Task 249 terminal files are
preserved from signed closeout commit `9553859`; this closeout restores the one
archived verification report omitted by the earlier fold-in. Task 250 can proceed
to terminal verification without deleting evidence or rewinding current state.

Source-closeout verification passed all 316 focused regressions across
`test_source_checkout_closeout.py`, `test_guard_rules.py`, and
`test_codex_task.py`. Readiness, Taskmaster health, plan sync, work-tracking audit,
and the S:W:H:E guard also pass. This source worktree is intentionally not an
installed Aegis target, so installed-target strict verification is not applicable;
no manifest or installation state was fabricated.

The same 316-test matrix passed again after Task 250 was marked done and its
tracking bundle was archived through the supported helper. Completed-source
readiness reported `READY`, Taskmaster health reported 240 done tasks and zero
invalid references, and the terminal source guard passed.
