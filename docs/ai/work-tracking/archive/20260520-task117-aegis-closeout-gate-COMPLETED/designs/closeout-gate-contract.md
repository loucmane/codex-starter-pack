# Task 117 Closeout Gate Contract

## Purpose

Task 117 turns the workflow proven in this repository into a portable Aegis completion gate for installed projects.

The intended behavior is not "Claude read the instructions and remembered to finish correctly." The intended behavior is:

1. A task starts with `aegis kickoff`, which creates branch-aligned current work, `sessions/current`, `plans/current`, and an ACTIVE work-tracking folder.
2. Mutations create pending S:W:H:E tracking through the installed hooks.
3. The next mutation and stop are blocked until `aegis log` writes the evidence into the session, tracker, implementation log, changelog, handoff, and plan.
4. Task completion is blocked until `aegis closeout` verifies readiness, tracking, ordered plan steps, strict verification, evidence cross-references, and semantic handoff state.

This is the portable equivalent of the local Codex workflow: work is only complete when the workflow state proves it.

## Non-Goals

- Do not require Taskmaster in installed projects.
- Do not require Serena in installed projects.
- Do not make `gac` the default commit path.
- Do not make closeout a Claude-only adapter command.
- Do not archive active work during closeout. Archive remains a separate lifecycle action.

## Command Surface

Add `aegis closeout` to the shared Aegis core.

Supported entry points:

- `aegis closeout --target-dir .`
- `./.aegis/bin/aegis closeout --target-dir .`
- `python3 scripts/codex-task aegis closeout --target-dir .`

MCP support may be added if it fits the existing acknowledgement shape; the CLI remains the portable authority for this task.

Optional flags:

- `--update-handoff`: deterministically refresh the Aegis-owned semantic sections of `HANDOFF.md` before validating.
- `--require-clean-git`: fail when the target Git worktree has uncommitted changes.
- `--no-git-guidance`: omit suggested Git/GitHub commands from the report.

## Closeout Report

Write `.aegis/reports/closeout-report.json`.

Required top-level fields:

- `schema_version`
- `status`: `passed` or `failed`
- `checked_at`
- `closed_at` when passed
- `target_root`
- `current_work`
- `readiness`
- `strict_verify`
- `plan`
- `pending_tracking`
- `evidence_matrix`
- `handoff`
- `integrations`
- `git`
- `checks`
- `summary`

The command exits `0` only when `status == "passed"`.

## Required Checks

### Runtime State

- `closeout.current_work`: `.aegis/state/current-work.json` exists and has active task state.
- `closeout.readiness`: installed readiness returns READY for the task.
- `closeout.pending_tracking`: `.aegis/state/pending-tracking.json` is absent or has zero events.
- `closeout.strict_verify`: `verify(..., strict=True)` passes.

Closeout should keep `current_work.status == "in-progress"` because strict verification currently treats that as the active-work invariant. On success, write additive fields instead:

- `closeout_passed_at`
- `closeout_report`

### Ordered Plan Steps

Parse `plans/current` and active `TRACKER.md`.

Required order:

1. `plan-step-scope` is completed.
2. `plan-step-implement` is completed.
3. `plan-step-verify` is completed.

Failure check IDs:

- `closeout.plan.scope`
- `closeout.plan.implement`
- `closeout.plan.verify`
- `closeout.plan.order`
- `closeout.tracker.scope`
- `closeout.tracker.implement`
- `closeout.tracker.verify`

The plan table and tracker checklist must agree. Do not trust only one surface.

### Evidence Cross-References

For every required evidence token:

- source implementation evidence from `plan-step-implement`
- verification evidence from `plan-step-verify`
- strict verification report path

Verify that the token appears in:

- `sessions/current`
- active `TRACKER.md`
- active `IMPLEMENTATION.md`
- active `CHANGELOG.md`
- active `HANDOFF.md`
- `plans/current`

Failure check IDs:

- `closeout.evidence.session`
- `closeout.evidence.tracker`
- `closeout.evidence.implementation`
- `closeout.evidence.changelog`
- `closeout.evidence.handoff`
- `closeout.evidence.plan`

Scope evidence may also appear in `FINDINGS.md` and `DECISIONS.md`, but closeout should not require those surfaces for every task.

### Semantic Handoff

The handoff must not be only kickoff text plus appended Progress Log entries.

Validate content outside `## Progress Log`:

- `## Current State` has non-placeholder content that does not only say the task was kicked off.
- `## Next Steps` has non-placeholder content.
- implementation evidence appears outside Progress Log.
- verification evidence appears outside Progress Log.
- strict verification evidence appears outside Progress Log.

Failure check IDs:

- `closeout.handoff.current_state`
- `closeout.handoff.next_steps`
- `closeout.handoff.implementation_evidence`
- `closeout.handoff.verification_evidence`
- `closeout.handoff.strict_verify_evidence`

`--update-handoff` may rewrite only the Aegis-owned semantic sections:

- `## Current State`
- `## What Was Done`
- `## Current Issues/Blockers`
- `## Next Steps`
- `## Important Context`

It must preserve `## Progress Log`.

### Optional Integrations

Taskmaster and Serena are optional unless `.aegis/state/current-work.json` marks them required.

Closeout report fields should say whether each integration is:

- detected
- required
- status

Closeout must pass in a target with no `.taskmaster` and no `.serena` when current work marks both optional.

### Git Guidance

Closeout may print suggested commands when Git work is delegated and auth is available:

- `git status --short`
- `git add <paths>`
- `git commit -m "..."`
- `git push`
- `gh pr create` or `gh pr view`

`gac` is legacy/manual only. It must not appear as the default path in generated Aegis closeout instructions.

## Hook and Instruction Changes

Update generated Claude runtime instructions to make completion explicit:

1. Run task-specific verification.
2. Log `plan-step-verify`.
3. Run `aegis verify --strict`.
4. Log strict verification evidence.
5. Run `aegis closeout`.
6. Do not report the task complete until closeout passes.

Update hook logic so `aegis closeout` is treated as a mutation for readiness and pending-tracking gating, but does not create a new pending S:W:H:E event after it succeeds. Closeout writes its own report and is the terminal completion gate.

## Regression Tests

Add or extend tests under the existing Aegis suites.

Positive installed-target path:

1. Install Aegis into `tests/fixtures/aegis-target-projects/web-started`.
2. Run kickoff for an Add Cart Button task.
3. Log scope.
4. Mutate `src/main.ts`.
5. Verify pending tracking blocks further mutation.
6. Log implementation.
7. Run task-specific verification.
8. Log verification.
9. Run strict verify.
10. Log strict verification report.
11. Update handoff semantically or run closeout with `--update-handoff`.
12. Run closeout and assert it passes.

Negative paths:

- closeout fails when readiness is BLOCKED.
- closeout fails with pending tracking.
- closeout fails when plan steps are missing or out of order.
- closeout fails before strict verify passes.
- closeout fails when evidence is missing from any required surface.
- closeout fails when handoff only contains kickoff/default text.
- closeout passes without Taskmaster and Serena when they are optional.

## Implementation Boundary

Primary files:

- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_foundation/cli.py`
- `scripts/codex-task`
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `docs/aegis/invocation-contract.md`
- `tests/meta_workflow_guard/test_aegis_installer.py`
- `tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`

The implementation should reuse shared core helpers and avoid creating a parallel closeout engine for one adapter.
