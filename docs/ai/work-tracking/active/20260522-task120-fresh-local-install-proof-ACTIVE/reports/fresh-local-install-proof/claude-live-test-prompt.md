# Claude Live Test Prompt

Use this prompt from the fresh target folder:

```bash
cd /tmp/aegis-task120-claude-live-shop-dry91w
claude
```

Prompt to paste into Claude:

```text
We are testing Aegis from a project-scoped MCP registration backed by a local wheel. Follow the installed/project Aegis workflow exactly. Do not edit `.aegis/`, `.claude/`, `CLAUDE.md`, `AGENTS.md`, or `.mcp.json` directly. Do not use PyPI, TestPyPI, `twine upload`, or any registry install of `aegis-foundation`.

Goal: add a visible "Add to cart" button to this tiny web app and complete Aegis verification/closeout.

Steps:

1. Confirm the current folder with `pwd`.
2. Inspect the Aegis MCP tools. Prefer the `aegis.*` MCP tools. If MCP tools are unavailable, report that as a finding and stop; do not manually edit `.mcp.json`.
3. Run `aegis.inspect` for `target_dir="."` and report whether Aegis is already installed. It should not be installed yet.
4. Run `aegis.plan_install` for `target_dir="."`, `primary_agent="claude"`, and `agents=["claude"]`.
5. Run `aegis.install` with `apply=true` using the same target/profile/agent values.
6. Run `bash .claude/scripts/readiness.sh --quick --root .`. It should be BLOCKED on `main` because no task branch/current work exists yet.
7. Run `aegis.kickoff` with `apply=true`, `target_dir="."`, `task="42"`, `slug="add-cart-button"`, `title="Add Cart Button"`, and goals:
   - "Add a visible Add to cart button to the web app"
   - "Record scope, implementation, verification, and closeout through Aegis"
8. Run readiness again. It should return `READY | task=42`.
9. Record scope with `aegis.log`: handler `claude:scope`, evidence `<active-work-tracking-folder>/FINDINGS.md`, note "Confirmed add-cart-button scope in the fresh local wheel install target", surfaces `["findings", "decisions"]`, plan step `plan-step-scope`, status `completed`.
10. Edit only `src/main.ts` to render a visible `<button type="button">Add to cart</button>`. Do not touch Aegis-owned files.
11. After the edit, if the hook creates pending tracking, clear it with `aegis.log` using the pending handler/evidence exactly. Expected evidence is `src/main.ts`; expected handler is likely `claude:Edit`.
12. Run an app-level verification command such as `grep -n "Add to cart" src/main.ts`. Save a short verification report under the active work-tracking reports folder, then log it with `aegis.log` using plan step `plan-step-verify`, status `completed`.
13. Run `aegis.verify` with `strict=true` and report-write acknowledgement if the MCP tool requires it. Log `.aegis/reports/verification-report.json` with handler `aegis:verify`, plan step `plan-step-verify`, status `completed`.
14. Run `aegis.closeout` with report-write acknowledgement and `update_handoff=true`.
15. Final report: current branch, final readiness, changed files, active session/plan/work-tracking paths, pending tracking status, whether `src/main.ts` is referenced in session/TRACKER/IMPLEMENTATION/CHANGELOG/HANDOFF/plan, strict verify status, closeout status, and every gate that blocked you.

If any Aegis MCP call is missing, any gate behaves differently, or closeout fails, stop and report the exact blocker instead of working around it.
```
