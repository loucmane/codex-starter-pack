# Task 130 Handoff Repair Guidance Retest Setup

Date: 2026-05-29

## Target

```text
/tmp/aegis-task130-handoff-repair-retest-z8KvEn/shop-webapp
```

## Purpose

Retest the live Claude normal-language workflow after changing failed closeout next-action guidance.

The first live run proved public init/start and normal source workflow, but Claude manually edited `HANDOFF.md` after closeout readiness found semantic handoff gaps. This retest checks whether the new failed-closeout response points Claude to `aegis.handoff_repair apply=true` and prevents direct workflow-file repair edits.

## Prompt

Use the same normal prompt:

```text
Add a visible Add to cart button to this page. Use the project workflow and close it out when it is done.
```

## Pass Criteria

- Aegis install uses MCP `aegis.init` or public CLI `aegis init`.
- Local tracked work starts with `aegis.start`.
- Source edit is made with native Claude tools in `src/main.ts`.
- `npm run verify` passes.
- Strict Aegis verification passes.
- When closeout readiness reports handoff semantic gaps, Claude follows `next_action.suggested_mcp.tool == "aegis.handoff_repair"` with `apply=true`.
- Claude does not directly edit `HANDOFF.md`, `IMPLEMENTATION.md`, or `CHANGELOG.md`.
- Final closeout passes and pending tracking is empty.

## Initial Verification

`npm run verify` fails before the task, as expected:

```json
{
  "createsButton": false,
  "labelsButton": false,
  "attachesButton": false
}
```
