# Claude Live Test 1 - Fresh Project Workflow

Date: 2026-05-28

Project:

```text
/tmp/aegis-task129-claude-live-siGsEu/shop-webapp
```

## Result

The live Claude session successfully:

- Loaded the local Aegis MCP server from `.mcp.json`.
- Installed Aegis through MCP `aegis.init`.
- Started tracked local work through MCP `aegis.start`.
- Edited `src/main.ts` with native tools to render a visible `Add to cart` button.
- Ran `npm run verify` successfully.
- Wrote task verification evidence under the active reports folder.
- Ran strict Aegis verification.
- Repaired handoff content.
- Closed out successfully.
- Ran read-only doctor after closeout.

Final Claude-reported state:

- Branch: `feat/task-1-add-to-cart-button`
- Closeout: passed, 22/22 checks, 0 failed required, 0 warnings
- Pending tracking: empty
- Doctor: `status=healthy`, `current_state=completed_closeout`
- Doctor checks: 20/20, 0 failed required, 0 warnings

## Issue Found

The workflow exposed a real idempotency/backfill flaw in `log_work`.

When Claude tried to re-log an existing `(handler, evidence)` pair with additional requested surfaces, Aegis returned `already_logged` and did not update the missing surfaces. Claude then worked around this by:

- using distinct synthetic handler names to force extra surface entries;
- directly editing `IMPLEMENTATION.md` and `CHANGELOG.md`;
- logging additional pending events created by those direct edits.

That behavior was too awkward for the intended workflow. A replayed log command should not duplicate session/tracker entries, but it should be allowed to backfill missing requested surfaces and missing plan evidence.

## Fix Applied

Updated `log_work` so an already-recorded S:W:H:E token now:

- avoids duplicate session and tracker entries;
- checks requested workflow surfaces;
- writes only missing requested surfaces;
- updates missing plan evidence/status if needed;
- returns `already_logged` only when no mutation is needed;
- returns `logged` with `replay_completed_missing_surfaces=true` when it completed missing surface or plan work.

Regression added:

- `test_log_work_replay_can_backfill_missing_surfaces_without_duplicate_core_entries`

Verification after fix:

```text
93 passed, 1 skipped in 8.16s
```

## Follow-Up Required

Run a second live Claude test against a fresh project after the fix, so installed Aegis assets include the corrected `log_work` behavior.
