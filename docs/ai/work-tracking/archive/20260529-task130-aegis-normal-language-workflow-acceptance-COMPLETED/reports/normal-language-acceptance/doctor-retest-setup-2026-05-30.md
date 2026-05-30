# Task 130 Post-Closeout Doctor Guidance Retest Setup

Date: 2026-05-30

## Target

```text
/tmp/aegis-task130-doctor-retest-jIfkTE/shop-webapp
```

## Purpose

Retest the live Claude normal-language workflow after adding post-closeout doctor guidance.

Earlier Task 130 live runs proved public `aegis.init`, `aegis.start`, handoff repair guidance, and existing-project preservation. The remaining acceptance gap is whether Claude follows the new successful-closeout `next_action` and runs read-only `aegis.doctor` before reporting final completion.

## Shape

- Fresh synthetic shop webapp with baseline git commit on `main`.
- Existing `CLAUDE.md` project instructions.
- Existing `.mcp.json` registering the local Aegis MCP server from `/home/loucmane/codex`.
- No Aegis runtime installed yet.
- No Taskmaster or Serena.
- Verification command: `npm run verify`.

## Baseline

Initial commit:

```text
50756d9 chore: create doctor retest fixture
```

Initial project verification fails as expected:

```json
{
  "createsButton": false,
  "labelsButton": false,
  "attachesButton": false
}
```

## Prompt

Open a fresh Claude client in the target folder, approve the project MCP server, then use this normal prompt:

```text
Add a visible Add to cart button to this page. Use the project workflow and close it out when it is done.
```

## Pass Criteria

- Claude uses MCP `aegis.init` or public CLI `aegis init`, preserving existing project instructions under the Aegis managed block.
- Claude starts local tracked work with `aegis.start`, not explicit numeric `aegis.kickoff`.
- Claude logs scope before source edits.
- Claude uses native source-editing tools for `src/main.ts`.
- `npm run verify` passes.
- Claude logs implementation and verification pending events with `pending_event_id=current` when applicable.
- Strict Aegis verification passes.
- If closeout readiness reports handoff semantic gaps, Claude uses `aegis.handoff_repair apply=true`.
- Final closeout passes with pending tracking empty.
- After final closeout passes, Claude follows the new `run_post_closeout_doctor` guidance and calls read-only `aegis.doctor`.
- Claude reports doctor status in the final answer and only then says the task is complete.

## Evidence To Capture After Run

- Final branch name.
- Final `npm run verify` result.
- `.aegis/reports/verification-report.json` summary.
- `.aegis/reports/closeout-report.json` summary.
- Doctor result: expected `healthy` / `completed_closeout`.
- Whether `.aegis/state/pending-tracking.json` is absent or has zero events.
- Whether existing `CLAUDE.md` content was preserved.
