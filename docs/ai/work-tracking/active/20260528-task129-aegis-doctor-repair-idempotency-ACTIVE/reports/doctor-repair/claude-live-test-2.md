# Claude Live Test 2 - Post-Backfill-Fix Fresh Project Workflow

Date: 2026-05-29

Project:

```text
/tmp/aegis-task129-claude-live2-uHyfax/shop-webapp
```

## Result

The second real Claude session successfully:

- Loaded the local Aegis MCP server from `.mcp.json`.
- Installed Aegis through MCP `aegis.init`.
- Started tracked local work through MCP `aegis.start`.
- Confirmed the installed readiness gate returned `READY`.
- Logged scope before source edits.
- Edited `src/main.ts` with native tools to render a visible `Add to cart` button.
- Cleared pending tracking with `aegis.log` using `pending_event_id=current`.
- Ran `npm run verify` successfully.
- Wrote task verification evidence under the active reports folder.
- Ran strict Aegis verification.
- Repaired handoff semantic sections through MCP `aegis.handoff_repair`.
- Re-ran strict verification after the handoff repair mutation.
- Closed out successfully with `aegis.closeout(update_handoff=true)`.
- Ran read-only doctor after closeout.

Final Claude-reported state:

- Branch: `feat/task-1-add-visible-add-to-cart-button`
- Closeout: passed, 22/22 gates, 0 failed required
- Pending tracking: empty
- Doctor: `status=healthy`, `current_state=completed_closeout`
- Doctor checks: 20 checks, 0 failed required

## Gate Behavior

The run encountered expected workflow gates and resolved them through Aegis:

1. `closeout.handoff.*` semantic-section gates failed because the kickoff handoff still contained placeholder prose. Claude repaired this with `aegis.handoff_repair`.
2. The handoff repair created one pending tracking event. Claude cleared it with `aegis.log` and `pending_event_id=current`.
3. Strict verification initially reflected that pending event. Claude re-ran strict verification after clearing pending tracking and logged the new strict verification evidence.
4. Final closeout required the handoff to include the latest handoff-repair evidence. Claude ran `aegis.closeout(update_handoff=true)`, and closeout passed.

Claude did not directly edit `IMPLEMENTATION.md` or `CHANGELOG.md`, and did not invent synthetic handler names.

## Backfill-Specific Note

The second live run validated the desired end-to-end behavior after the fix: Claude completed the installed workflow without the awkward workaround from the first run.

However, this run did not force the exact missing `IMPLEMENTATION.md` / `CHANGELOG.md` surface-backfill branch, because the closeout evidence matrix was already complete before handoff semantic repair. The exact replay/backfill branch remains covered by the focused regression:

```text
test_log_work_replay_can_backfill_missing_surfaces_without_duplicate_core_entries
```

This is acceptable evidence for Task 129 because the live client no longer needed synthetic handlers or direct workflow-surface edits, and the edge branch is protected by a deterministic regression test.

## Conclusion

Live Claude validation passed for the installed Aegis workflow. The system behaved as intended from a fresh project:

- MCP installation created the workflow scaffold.
- Aegis start created branch, current work, session, plan, and active work-tracking state.
- Native source edits and project verification remained normal agent work.
- Aegis handled evidence, pending tracking, handoff repair, strict verification, closeout, and doctor.
- Post-closeout doctor reported a healthy completed state.
