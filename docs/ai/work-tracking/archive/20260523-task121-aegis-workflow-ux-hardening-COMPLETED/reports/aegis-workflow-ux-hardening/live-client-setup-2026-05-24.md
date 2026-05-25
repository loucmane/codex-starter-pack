# Live Client First-Pass Setup - 2026-05-24

## Target Project
- Path: `/tmp/aegis-live-client-task121-20260524-first-pass/shop-webapp`
- Baseline branch: `main`
- Baseline commit: `bbedfdc`
- Baseline status: clean
- Aegis installed: no (`.aegis/` and `.claude/` absent)
- MCP configured: yes (`.mcp.json` points `aegis` to local source `/home/loucmane/codex`)

## Starter App
- `index.html`
- `package.json`
- `src/main.ts`
- `README.md`

## Purpose
Retest Task 121 after adding response-level `next_action` guidance and evidence-location metadata. The pass condition is stricter than the previous live test: the first `aegis.closeout` attempt must pass without post-closeout repair logging.

## Claude Client Directory
```bash
cd /tmp/aegis-live-client-task121-20260524-first-pass/shop-webapp
```

## Acceptance Prompt
```text
We are testing the Aegis workflow in this fresh project after the Task 121 first-pass guidance fix.

Use the Aegis MCP server if it is available. If Claude asks whether to trust the project MCP server, choose the option that enables this project MCP server. If the Aegis MCP server is not available after that, stop and report that clearly.

Goal: install the Aegis workflow for Claude in this project, then complete Task 42: Add Cart Button.

Important workflow expectations:
- Use Aegis MCP for workflow control-plane actions: inspect, plan_install, install, kickoff, log, verify, and closeout.
- Use normal Claude/native tools for implementation work: read files, edit source, run shell checks/tests, and inspect git status.
- Do not use Aegis MCP to edit src/main.ts. Edit source with normal tools.
- Do not hand-edit Aegis workflow files unless the installed workflow explicitly requires it.
- Do not bypass hooks, do not use --no-verify, and do not work around Aegis gates.
- Follow the next_action field returned by Aegis tools when it is present.
- When a mutation creates pending tracking, log it with pending_event_id=current instead of guessing handler/evidence manually.
- If the pending event includes evidence_location, include that in your final report.

Work to perform:
1. Inspect/plan/install Aegis for Claude in this project.
2. Kick off task 42 with slug add-cart-button and title "Add Cart Button".
3. After kickoff, follow Aegis next_action and log scope before any source edit.
4. Add a visible "Add to cart" button to the app in src/main.ts.
5. Log the implementation using pending_event_id=current, with plan-step-implement completed.
6. Run task-specific verification using npm test or an equivalent source check, save a short verification report under the active reports folder, and log it with plan-step-verify completed.
7. Run strict Aegis verification and log its pending event with plan-step-verify completed.
8. Run Aegis closeout with handoff update.

Final report must include:
- current branch
- final readiness result
- active session, plan, and work-tracking paths
- whether .aegis/state/pending-tracking.json is absent
- whether src/main.ts is referenced in sessions/current, TRACKER.md, IMPLEMENTATION.md, CHANGELOG.md, HANDOFF.md, and plans/current
- strict verification result
- closeout result
- whether the first closeout attempt passed
- any evidence_location value observed for the src/main.ts mutation
- any gate blocks and how they were resolved
```

## Pass Criteria
- Fresh Claude installs Aegis through MCP.
- Source implementation uses native tools, not Aegis MCP.
- Scope, implementation, task-specific verification, and strict verification are logged before closeout.
- First `aegis.closeout` attempt passes.
- No manual workflow-file edits, no hook bypass, no post-closeout repair loop.
