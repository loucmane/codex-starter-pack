# Claude Live Test Result

Date: 2026-05-22

Target project:

```text
/tmp/aegis-task120-claude-live-shop-dry91w
```

## Result

PASS. A fresh Claude session accepted the project-scoped `aegis` MCP server from `.mcp.json`, installed Aegis from the local wheel into a previously uninstalled target project, completed kickoff, made a normal source edit with native tools, logged S:W:H:E tracking through Aegis, ran strict verification, and passed closeout.

## Observed Workflow

Claude used the Aegis MCP for workflow control-plane actions:

- `aegis.inspect`
- `aegis.plan_install`
- `aegis.install`
- `aegis.kickoff`
- `aegis.log`
- `aegis.verify`
- `aegis.closeout`

Claude used native project tools for implementation work:

- Bash readiness probes
- file reads
- native `Write` for `src/main.ts`
- `grep` app-level verification

This is the intended architecture: MCP installs and operates Aegis workflow state; the installed runtime and hooks enforce behavior while normal agent tools perform normal project work.

## Final State Reported By Claude

- Branch: `feat/task-42-add-cart-button`
- Readiness: `READY | task=42`
- Changed source: `src/main.ts`
- Active session: `sessions/2026/05/2026-05-22-001-task42-add-cart-button.md`
- Active plan: `plans/2026-05-22-task42-add-cart-button.md`
- Active work tracking: `docs/ai/work-tracking/active/20260522-task42-add-cart-button-ACTIVE/`
- Pending tracking: empty
- `src/main.ts` was referenced in session, `TRACKER.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `HANDOFF.md`, and `plans/current`
- Strict verify: passed, 27 checks, 0 required failures, 0 warnings, 1 unsupported policy-only MCP memory check
- Closeout: passed, 22 gates, 0 required failures, 0 warnings

## Gate Behavior

Claude encountered and resolved the expected gates:

1. Pre-kickoff readiness blocked on branch `main` because no task ID/current work existed.
2. The implementation edit created pending S:W:H:E tracking, requiring `aegis.log` before further mutation.
3. `aegis.log` rejected an incorrect plan-step name and accepted the correct `plan-step-implement`.
4. Strict verify created an MCP pending event that had to be logged using exact handler/evidence.
5. Initial closeout failed because `CHANGELOG.md` lacked references to three verification evidence entries; additional `aegis.log` calls with `surfaces=["changelog"]` repaired the evidence and closeout passed.

## Product Finding

The live test confirms the intended tool split:

```text
Aegis MCP = installer and workflow control plane
Installed Aegis runtime = enforcement system
Native agent tools = normal implementation, reading, testing, and git inspection
```

Future installed contracts should say this explicitly so agents do not infer "use MCP for absolutely everything."
