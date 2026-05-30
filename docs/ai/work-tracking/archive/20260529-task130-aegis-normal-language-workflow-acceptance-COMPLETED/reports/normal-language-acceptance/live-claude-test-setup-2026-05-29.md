# Task 130 Normal-Language Claude Live Test Setup

Date: 2026-05-29

## Target

```text
/tmp/aegis-task130-normal-language-yGhoHJ/shop-webapp
```

## Shape

- Fresh tiny TypeScript webapp on branch `main`.
- No Aegis runtime installed yet.
- No Taskmaster or Serena.
- Existing project `CLAUDE.md` is present so the install must preserve/merge it.
- `.mcp.json` points the `aegis` MCP server at the local checkout under `/home/loucmane/codex`.
- `npm run verify` is intentionally failing before the task because `src/main.ts` does not create an `Add to cart` button.

## Expected User Flow

The test should not use a long checklist prompt. Open a fresh Claude client in the target folder, approve the project MCP server, then give a normal request:

```text
Add a visible Add to cart button to this page. Use the project workflow and close it out when it is done.
```

Claude should infer the rest from `.mcp.json`, Aegis MCP metadata, installed `CLAUDE.md` after init, `.aegis/contract.md`, hooks, and `aegis.next`.

## Pass Criteria

- Uses MCP `aegis.init` or public CLI `aegis init`, not the advanced plan-install/install path unless it explains a conflict review.
- Starts local work with `aegis.start`, not external numeric `kickoff`, because no external task id exists.
- Uses native Claude tools for the source edit.
- Adds a semantically real visible `Add to cart` button in `src/main.ts`.
- Runs `npm run verify` and records a task verification report.
- Logs pending S:W:H:E events with `pending_event_id=current`.
- Runs strict Aegis verification.
- Uses `aegis.closeout_ready`, `aegis.handoff_repair` if needed, and final `aegis.closeout`.
- Ends with pending tracking empty, closeout passed, and doctor healthy.
- Does not invent synthetic handler names.
- Does not directly edit `IMPLEMENTATION.md` or `CHANGELOG.md`.
- Does not require Taskmaster or Serena.

## Initial Verification

```text
npm run verify
```

failed as expected with:

```json
{
  "createsButton": false,
  "labelsButton": false,
  "attachesButton": false
}
```
