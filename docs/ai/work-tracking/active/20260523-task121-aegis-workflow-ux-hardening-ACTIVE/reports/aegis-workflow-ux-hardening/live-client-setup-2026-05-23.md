# Live Client Acceptance Setup - Task 121

Date: 2026-05-23

## Target Project

- Path: `/tmp/aegis-live-client-task121-e8BuyR/shop-webapp`
- Baseline branch: `main`
- Baseline commit: `99e8dc9`
- Baseline status: clean
- Starter app:
  - `index.html`
  - `package.json`
  - `src/main.ts`
  - `README.md`

## MCP Registration

Registered with Claude project scope from the target project directory:

```bash
claude mcp add --scope project aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio
```

This produced project-local `.mcp.json` and keeps Aegis absent from the project until the live Claude client uses MCP `aegis.install`.

## Acceptance Prompt

Paste this into a fresh Claude client opened in `/tmp/aegis-live-client-task121-e8BuyR/shop-webapp`:

```text
We are testing the Aegis workflow in this fresh project.

Use the Aegis MCP server if it is available. If it is not available, stop and report that clearly.

Goal: install the Aegis workflow for Claude in this project, then complete Task 42: Add Cart Button.

Expected behavior:
- Use Aegis MCP for workflow control-plane actions: inspect, plan_install, install, kickoff, log, verify, and closeout.
- Use normal Claude/native tools for implementation work: read files, edit source, run shell checks/tests, and inspect git status.
- Do not hand-edit Aegis workflow files unless the installed workflow explicitly requires it.
- Do not bypass hooks, do not use --no-verify, and do not work around Aegis gates.
- If a gate blocks you, follow the Aegis-provided repair path, preferably pending-id/current logging.

Work to perform:
1. Inspect/plan/install Aegis for Claude in this project.
2. Kick off task 42 with slug add-cart-button and title "Add Cart Button".
3. Add a visible "Add to cart" button to the app in src/main.ts.
4. Log the implementation using the pending tracking event, not by guessing handler/evidence manually.
5. Run task-specific verification using npm test or an equivalent source check, save a short verification report under the active reports folder, and log it.
6. Run strict Aegis verification and log its evidence.
7. Run Aegis closeout with handoff update.

Final report must include:
- current branch
- final readiness result
- active session, plan, and work-tracking paths
- whether .aegis/state/pending-tracking.json is absent
- whether src/main.ts is referenced in sessions/current, TRACKER.md, IMPLEMENTATION.md, CHANGELOG.md, HANDOFF.md, and plans/current
- strict verification result
- closeout result
- any gate blocks and how they were resolved
```

## Pass Criteria

The live client passes only if a fresh Claude session can install Aegis through MCP, perform a normal source edit with native tools, consume pending tracking through Aegis logging, update all canonical workflow surfaces, pass strict verification, and pass closeout without manual workflow-file editing or extra relogging.
