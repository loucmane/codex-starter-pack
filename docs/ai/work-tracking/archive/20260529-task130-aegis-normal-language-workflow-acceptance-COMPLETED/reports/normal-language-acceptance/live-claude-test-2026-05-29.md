# Task 130 Normal-Language Claude Live Test

Date: 2026-05-29

## Target

```text
/tmp/aegis-task130-normal-language-yGhoHJ/shop-webapp
```

## Prompt

```text
Add a visible Add to cart button to this page. Use the project workflow and close it out when it is done.
```

## Result

Partial pass.

Claude successfully inferred and used most of the intended public workflow from the normal prompt:

- Read the project and detected the Aegis MCP server.
- Called Aegis status/next and found Aegis was not installed.
- Installed through MCP `aegis.init`.
- Started local tracked work through MCP `aegis.start`.
- Created branch `feat/task-1-add-visible-add-to-cart-button`.
- Logged scope before source edits.
- Edited `src/main.ts` with native source tools.
- Added a real visible `Add to cart` button.
- Logged the pending implementation event.
- Ran `npm run verify`; it passed with the semantic fixture assertion.
- Wrote and logged a task verification report.
- Ran strict Aegis verification; it passed with 27 checks and 0 failures.
- Ran closeout readiness.
- Final closeout passed with 22 gates, 0 failures, and pending tracking empty.

Final target state:

```text
branch: feat/task-1-add-visible-add-to-cart-button
closeout: passed
pending_tracking: empty
```

## Failure Found

Claude did not use deterministic handoff repair after closeout readiness found placeholder handoff content.

Instead of calling `aegis.handoff_repair apply=true`, Claude manually edited:

```text
docs/ai/work-tracking/active/20260529-task1-add-visible-add-to-cart-button-ACTIVE/HANDOFF.md
```

That violates the Task 130 acceptance bar:

- no direct workflow-file edits for mechanical closeout repair;
- use Aegis repair tools for handoff semantic-section repair;
- avoid teaching Claude to patch Aegis-owned files by hand.

The manual edit still reached final closeout, so this was not a workflow blocker, but it is not the desired first-pass behavior.

## Root Cause

The failed closeout `next_action` was too generic.

When closeout failed only on `closeout.handoff.*` semantic gates, the response still used:

```text
action: repair_closeout_gates_before_retry
suggested_mcp: aegis.closeout_ready or aegis.closeout
message: apply repair_guidance and retry closeout
```

That left Claude to infer the repair path and it chose a direct `HANDOFF.md` edit.

## Fix Applied

Updated `closeout()` next-action behavior so handoff-only failures now return:

```text
action: apply_handoff_repair_before_retry
suggested_mcp: aegis.handoff_repair
arguments: { target_dir: ".", apply: true }
```

Mixed failures such as missing `IMPLEMENTATION.md` or `CHANGELOG.md` evidence references still keep the generic `repair_closeout_gates_before_retry` path because `aegis.handoff_repair` alone cannot fix those surfaces.

Regression coverage added/updated in:

```text
tests/meta_workflow_guard/test_aegis_installer.py
```

Focused verification:

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -k 'closeout_reports_missing_evidence_repair_guidance or closeout_requires_semantic_handoff_and_passes_with_update or handoff_repair_fixes_placeholder_handoff_before_closeout'
```

passed:

```text
3 passed, 35 deselected
```

## Retest Required

Run a new fresh Claude live test after this fix. The expected behavior is:

1. Closeout readiness fails on handoff semantic gates.
2. Claude follows `next_action.suggested_mcp.tool == "aegis.handoff_repair"`.
3. Claude logs the handoff repair pending event if the hook records one.
4. Claude re-runs strict verification if needed.
5. Claude closes out without direct edits to `HANDOFF.md`, `IMPLEMENTATION.md`, or `CHANGELOG.md`.
